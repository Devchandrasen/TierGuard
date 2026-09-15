from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset, Subset, random_split
from torch.nn import functional as F

from tierguard.data.backdoor import BackdoorDataset
from tierguard.data.partition import partition_dataset


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


def _load_torchvision_dataset(name: str, root: str, train: bool, download: bool = False):
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
        if train:
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


def make_data_bundle(config: dict[str, Any]) -> DataBundle:
    data_cfg = config["data"]
    fed_cfg = config["federated"]
    seed = int(config["experiment"].get("seed", 1))
    if data_cfg.get("dataset", "").lower() == "ids":
        from tierguard.data.ids_loader import make_ids_data_bundle

        return make_ids_data_bundle(config)

    train, test, num_classes, input_shape = load_vision_datasets(data_cfg, seed)
    train = maybe_subset(train, data_cfg.get("train_size"), seed)
    test = maybe_subset(test, data_cfg.get("test_size") or data_cfg.get("validation_size"), seed + 1)
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
    )
