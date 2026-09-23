from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from torch.utils.data import ConcatDataset, DataLoader, Dataset, Subset, random_split
from torch.nn import functional as F

from tierguard.data.backdoor import BackdoorDataset, add_configured_trigger
from tierguard.data.partition import labels_to_numpy, partition_dataset
from tierguard.data.root_splits import stratified_root_split
from tierguard.data.semantic_green_car import (
    GREEN_CAR_ATTACK_TRAIN, GREEN_CAR_HELDOUT_TEST, GREEN_CAR_INDICES,
    SemanticTargetDataset,
)


class SyntheticImageDataset(Dataset):
    def __init__(
        self,
        size: int,
        channels: int = 1,
        height: int = 28,
        width: int = 28,
        num_classes: int = 10,
        seed: int = 1,
    ):
        generator = torch.Generator().manual_seed(seed)
        labels = torch.arange(size) % num_classes
        labels = labels[torch.randperm(size, generator=generator)]
        images = 0.05 * torch.randn(size, channels, height, width, generator=generator)
        for idx, label in enumerate(labels):
            label_int = int(label)
            row = 2 + (label_int * max(1, (height - 5) // max(1, num_classes - 1))) % (height - 3)
            col = 2 + (label_int * max(1, (width - 5) // max(1, num_classes - 1))) % (width - 3)
            images[idx, :, row : row + 2, :] += 0.8
            images[idx, :, :, col : col + 2] += 0.3
        self.data = torch.clamp(images, 0.0, 1.0)
        self.targets = labels.tolist()

    def __len__(self) -> int:
        return len(self.targets)

    def __getitem__(self, idx: int):
        return self.data[idx], int(self.targets[idx])


class TensorImageDataset(Dataset):
    def __init__(self, images: torch.Tensor, labels: torch.Tensor):
        self.data = images.float()
        self.targets = [int(x) for x in labels.tolist()]

    def __len__(self) -> int:
        return len(self.targets)

    def __getitem__(self, idx: int):
        return self.data[idx], self.targets[idx]


class RootContaminationDataset(Dataset):
    def __init__(self, base: Dataset, selected: set[int], attack_config: dict):
        self.base = base
        self.selected = selected
        self.attack_config = attack_config

    def __len__(self) -> int:
        return len(self.base)

    def __getitem__(self, index: int):
        image, label = self.base[index]
        if index in self.selected:
            return add_configured_trigger(image, self.attack_config), int(
                self.attack_config["target_label"]
            )
        return image, label


class RootAppearanceDataset(Dataset):
    def __init__(self, base: Dataset, invert_intensity: bool):
        self.base = base
        self.invert_intensity = invert_intensity
        self.targets = labels_to_numpy(base).tolist()

    def __len__(self) -> int:
        return len(self.base)

    def __getitem__(self, index: int):
        image, label = self.base[index]
        if self.invert_intensity:
            image = image.amin(dim=(-2, -1), keepdim=True) + image.amax(
                dim=(-2, -1), keepdim=True
            ) - image
        return image, label


def contaminate_root(base: Dataset, fraction: float, attack_config: dict,
                     seed: int) -> tuple[Dataset, list[int]]:
    if not 0 <= fraction <= 1:
        raise ValueError("Root contamination fraction must be in [0, 1]")
    if fraction == 0:
        return base, []
    labels = labels_to_numpy(base)
    eligible = np.where(labels != int(attack_config["target_label"]))[0]
    count = int(round(fraction * len(base)))
    if count > len(eligible):
        raise ValueError("Insufficient non-target root examples for contamination")
    selected = np.random.default_rng(seed).choice(eligible, count, replace=False).tolist()
    return RootContaminationDataset(base, set(selected), attack_config), selected


@dataclass
class DataBundle:
    client_loaders: list[DataLoader]
    edge_mapping: dict[int, list[int]]
    root_loader: DataLoader
    audit_loader: DataLoader
    test_loader: DataLoader
    backdoor_test_loader: DataLoader
    num_classes: int
    input_shape: tuple[int, ...]
    input_dim: int
    audit_search_loader: DataLoader | None = None
    audit_eval_loader: DataLoader | None = None
    partition_indices: dict[str, Any] | None = None
    full_root_loader: DataLoader | None = None
    semantic_train_dataset: Dataset | None = None
    semantic_test_loader: DataLoader | None = None


def _load_torchvision_dataset(name: str, root: str, train: bool, download: bool = False,
                              augment: bool = True):
    try:
        from torchvision import datasets, transforms
    except Exception as exc:  # pragma: no cover - depends on local torchvision install
        raise RuntimeError(f"torchvision is required for {name}: {exc}") from exc

    key = name.lower()
    if key in {"mnist", "fashionmnist", "kmnist"}:
        transform = transforms.ToTensor()
        if key == "mnist":
            cls = datasets.MNIST
        elif key == "fashionmnist":
            cls = datasets.FashionMNIST
        else:
            cls = datasets.KMNIST
        return cls(root=root, train=train, download=download, transform=transform)
    if key == "cifar10":
        steps = []
        if train and augment:
            steps.extend(
                [
                    transforms.RandomCrop(32, padding=4),
                    transforms.RandomHorizontalFlip(),
                ]
            )
        steps.extend(
            [
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=(0.4914, 0.4822, 0.4465),
                    std=(0.2470, 0.2435, 0.2616),
                ),
            ]
        )
        transform = transforms.Compose(steps)
        return datasets.CIFAR10(root=root, train=train, download=download, transform=transform)
    raise ValueError(f"Unsupported torchvision dataset: {name}")


def _make_synthetic(config: dict[str, Any], seed: int):
    name = config.get("dataset", "mnist").lower()
    channels, height, width = (3, 32, 32) if name == "cifar10" else (1, 28, 28)
    train_size = int(config.get("train_size") or 1000)
    test_size = int(config.get("test_size") or 300)
    train = SyntheticImageDataset(train_size, channels, height, width, seed=seed)
    test = SyntheticImageDataset(test_size, channels, height, width, seed=seed + 1000)
    return train, test, 10, (channels, height, width)


def _load_sklearn_digits(seed: int):
    try:
        from sklearn.datasets import load_digits
    except Exception as exc:  # pragma: no cover - depends on optional sklearn install
        raise RuntimeError(f"scikit-learn is required for digits: {exc}") from exc

    digits = load_digits()
    images = torch.tensor(digits.images, dtype=torch.float32).unsqueeze(1) / 16.0
    images = F.interpolate(images, size=(28, 28), mode="bilinear", align_corners=False)
    labels = torch.tensor(digits.target, dtype=torch.long)
    generator = torch.Generator().manual_seed(seed)
    perm = torch.randperm(len(labels), generator=generator)
    split = int(0.8 * len(labels))
    train_idx = perm[:split]
    test_idx = perm[split:]
    train = TensorImageDataset(images[train_idx], labels[train_idx])
    test = TensorImageDataset(images[test_idx], labels[test_idx])
    return train, test, 10, (1, 28, 28)


def load_vision_datasets(config: dict[str, Any], seed: int):
    if bool(config.get("synthetic", False)):
        return _make_synthetic(config, seed)
    if str(config.get("dataset", "")).lower() == "digits":
        return _load_sklearn_digits(seed)
    try:
        download = bool(config.get("download", False))
        train = _load_torchvision_dataset(
            config.get("dataset", "mnist"), config.get("root", "./data"), True, download=download
        )
        test = _load_torchvision_dataset(
            config.get("dataset", "mnist"), config.get("root", "./data"), False, download=download
        )
    except Exception as exc:
        if config.get("allow_synthetic_fallback", False):
            return _make_synthetic(config, seed)
        raise RuntimeError(
            "Dataset not available locally. Set data.synthetic=true for smoke tests or "
            "download the dataset under data.root for paper experiments."
        ) from exc
    sample, _ = train[0]
    return train, test, 10, tuple(sample.shape)


def maybe_subset(dataset: Dataset, size: int | None, seed: int) -> Dataset:
    if size is None or size >= len(dataset):
        return dataset
    generator = torch.Generator().manual_seed(seed)
    indices = torch.randperm(len(dataset), generator=generator)[: int(size)].tolist()
    return Subset(dataset, indices)


def original_indices(dataset: Dataset) -> list[int]:
    if isinstance(dataset, Subset):
        parent = original_indices(dataset.dataset)
        return [int(parent[int(index)]) for index in dataset.indices]
    return list(range(len(dataset)))


def make_data_bundle(config: dict[str, Any]) -> DataBundle:
    data_cfg = config["data"]
    fed_cfg = config["federated"]
    seed = int(config["experiment"].get("seed", 1))
    if data_cfg.get("dataset", "").lower() == "ids":
        from tierguard.data.ids_loader import make_ids_data_bundle

        return make_ids_data_bundle(config)

    train, test, num_classes, input_shape = load_vision_datasets(data_cfg, seed)
    semantic_train_dataset = None
    semantic_test_dataset = None
    semantic_attack = str(config.get("attack", {}).get("name", "")) == "semantic_green_car"
    if semantic_attack:
        if data_cfg.get("dataset", "").lower() != "cifar10" or data_cfg.get("synthetic", False):
            raise ValueError("Semantic green-car stress test requires real CIFAR-10")
        if any(int(train.targets[index]) != 1 for index in GREEN_CAR_INDICES):
            raise ValueError("Green-car source indices do not match CIFAR-10 car labels")
        semantic_plain = _load_torchvision_dataset(
            "cifar10", data_cfg.get("root", "./data"), True,
            download=bool(data_cfg.get("download", False)), augment=False,
        )
        semantic_train_dataset = Subset(semantic_plain, GREEN_CAR_ATTACK_TRAIN)
        semantic_test_dataset = SemanticTargetDataset(
            Subset(semantic_plain, GREEN_CAR_HELDOUT_TEST),
            target_label=int(config["attack"].get("target_label", 2)),
        )
        reserved = set(GREEN_CAR_INDICES)
        train = Subset(train, [index for index in range(len(train)) if index not in reserved])
    train = maybe_subset(train, data_cfg.get("train_size"), seed)
    test = maybe_subset(test, data_cfg.get("test_size") or data_cfg.get("validation_size"), seed + 1)
    train_index_map = original_indices(train)
    test_index_map = original_indices(test)
    three_way_root = (
        str(config.get("aggregation", {}).get("method", "")).lower() == "tierguard2"
        or bool(data_cfg.get("three_way_root_split", False))
    )
    root_indices = None
    if three_way_root:
        sizes = (
            int(data_cfg.get("root_dataset_size", 200)),
            int(data_cfg.get("audit_search_size", 100)),
            int(data_cfg.get("audit_eval_size", 100)),
        )
        root_indices = stratified_root_split(train, sizes, seed + 2)
        main_train = Subset(train, root_indices["clients"])
        root_active = {name: list(root_indices[name])
                       for name in ("reference", "search", "evaluation")}
        allowed_labels = data_cfg.get("root_label_allowlist")
        if allowed_labels is not None:
            allowed = {int(value) for value in allowed_labels}
            if not allowed:
                raise ValueError("root_label_allowlist cannot be empty")
            train_labels = labels_to_numpy(train)
            root_active = {
                name: [index for index in indices if int(train_labels[index]) in allowed]
                for name, indices in root_active.items()
            }
            if any(not indices for indices in root_active.values()):
                raise ValueError("Root label restriction emptied a root split")
        invert = bool(data_cfg.get("root_invert_intensity", False))
        root_set = RootAppearanceDataset(Subset(train, root_active["reference"]), invert)
        search_set = RootAppearanceDataset(Subset(train, root_active["search"]), invert)
        eval_set = RootAppearanceDataset(Subset(train, root_active["evaluation"]), invert)
        contamination_fraction = float(data_cfg.get("root_contamination_fraction", 0.0))
        root_sets = [root_set, search_set, eval_set]
        contamination_local = []
        for offset, root_subset in enumerate(root_sets):
            contaminated, local_indices = contaminate_root(
                root_subset, contamination_fraction, config.get("attack", {}),
                seed + 80_000 + offset,
            )
            root_sets[offset] = contaminated
            contamination_local.append(local_indices)
        root_set, search_set, eval_set = root_sets
    else:
        root_size = min(int(data_cfg.get("root_dataset_size", 200)), len(train))
        main_size = max(0, len(train) - root_size)
        main_train, root_set = random_split(
            train,
            [main_size, root_size],
            generator=torch.Generator().manual_seed(seed + 2),
        )
    parts, edge_mapping = partition_dataset(
        main_train,
        int(fed_cfg["num_clients"]),
        data_cfg.get("partition", "dirichlet"),
        float(data_cfg.get("dirichlet_alpha", 0.3)),
        bool(data_cfg.get("iid", False)),
        seed,
        int(fed_cfg["num_edges"]),
    )
    batch_size = int(fed_cfg.get("batch_size", 64))
    client_loaders = [
        DataLoader(
            Subset(main_train, part),
            batch_size=batch_size,
            shuffle=True,
            generator=torch.Generator().manual_seed(seed + 10_000 + client_id),
        )
        for client_id, part in enumerate(parts)
    ]
    root_loader = DataLoader(
        root_set,
        batch_size=batch_size,
        shuffle=True,
        generator=torch.Generator().manual_seed(seed + 20_000),
    )
    audit_loader = DataLoader(
        root_set,
        batch_size=batch_size,
        shuffle=True,
        generator=torch.Generator().manual_seed(seed + 30_000),
    )
    test_loader = DataLoader(test, batch_size=batch_size, shuffle=False)
    attack_cfg = config.get("attack", {})
    backdoor_test = BackdoorDataset(
        test,
        target_label=int(attack_cfg.get("target_label", 0)),
        source_label=None,
        attack_config=attack_cfg if three_way_root else None,
    )
    backdoor_test_loader = DataLoader(backdoor_test, batch_size=batch_size, shuffle=False)
    input_dim = int(np.prod(input_shape))
    return DataBundle(
        client_loaders=client_loaders,
        edge_mapping=edge_mapping,
        root_loader=root_loader,
        audit_loader=audit_loader,
        test_loader=test_loader,
        backdoor_test_loader=backdoor_test_loader,
        num_classes=num_classes,
        input_shape=input_shape,
        input_dim=input_dim,
        audit_search_loader=(
            DataLoader(search_set, batch_size=batch_size, shuffle=False) if three_way_root else None
        ),
        audit_eval_loader=(
            DataLoader(eval_set, batch_size=batch_size, shuffle=False) if three_way_root else None
        ),
        partition_indices=(
            {
                "root": {
                    name: [int(train_index_map[index]) for index in root_active[name]]
                    for name in ("reference", "search", "evaluation")
                },
                "root_reserved": {
                    name: [int(train_index_map[index]) for index in root_indices[name]]
                    for name in ("reference", "search", "evaluation")
                },
                "clients": {
                    str(client_id): [int(train_index_map[root_indices["clients"][index]])
                                     for index in part]
                    for client_id, part in enumerate(parts)
                },
                "test": [int(index) for index in test_index_map],
                "root_contamination": {
                    name: [int(train_index_map[root_active[name][index]])
                           for index in contamination_local[offset]]
                    for offset, name in enumerate(("reference", "search", "evaluation"))
                },
                "root_invert_intensity": invert,
                "root_label_allowlist": sorted(allowed) if allowed_labels is not None else None,
                "semantic_green_car": (
                    {
                        "reserved_original_train_indices": list(GREEN_CAR_INDICES),
                        "attacker_train_original_indices": list(GREEN_CAR_ATTACK_TRAIN),
                        "heldout_semantic_original_indices": list(GREEN_CAR_HELDOUT_TEST),
                        "source_commit": "9f48fbbb496aaed4ba696494950a5d71ee82a80c",
                    } if semantic_attack else None
                ),
                "note": "Train and test indices refer to their respective original loaded datasets",
            }
            if three_way_root else None
        ),
        full_root_loader=(
            DataLoader(
                ConcatDataset([root_set, search_set, eval_set]),
                batch_size=batch_size, shuffle=False,
            ) if three_way_root else None
        ),
        semantic_train_dataset=semantic_train_dataset,
        semantic_test_loader=(
            DataLoader(semantic_test_dataset, batch_size=batch_size, shuffle=False)
            if semantic_test_dataset is not None else None
        ),
    )
