from __future__ import annotations

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from torch.utils.data import DataLoader, Dataset, Subset, random_split

from tierguard.data.backdoor import BackdoorDataset
from tierguard.data.datasets import DataBundle
from tierguard.data.partition import partition_dataset


class TabularDataset(Dataset):
    def __init__(self, features: np.ndarray, labels: np.ndarray):
        self.features = torch.tensor(features, dtype=torch.float32)
        self.targets = labels.astype(int).tolist()

    def __len__(self) -> int:
        return len(self.targets)

    def __getitem__(self, idx: int):
        return self.features[idx], int(self.targets[idx])


def load_ids_csv(path: str, label_column: str):
    if not path:
        raise FileNotFoundError(
            "IDS CSV path is not configured. Set data.csv_path to UNSW-NB15, CICIDS2017, "
            "or N-BaIoT preprocessed CSV."
        )
    frame = pd.read_csv(path)
    if label_column not in frame.columns:
        raise ValueError(f"Label column {label_column!r} not found in {path}")
    labels = LabelEncoder().fit_transform(frame[label_column])
    features = frame.drop(columns=[label_column])
    features = pd.get_dummies(features).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    x = StandardScaler().fit_transform(features.to_numpy(dtype=np.float32))
    return x, labels


def make_ids_data_bundle(config: dict) -> DataBundle:
    data_cfg = config["data"]
    fed_cfg = config["federated"]
    attack_cfg = config.get("attack", {})
    seed = int(config["experiment"].get("seed", 1))
    x, y = load_ids_csv(data_cfg.get("csv_path"), data_cfg.get("label_column", "label"))
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=seed, stratify=y if len(set(y)) > 1 else None
    )
    train = TabularDataset(x_train, y_train)
    test = TabularDataset(x_test, y_test)
    root_size = min(int(data_cfg.get("root_dataset_size", 200)), len(train))
    main_size = len(train) - root_size
    main_train, root_set = random_split(
        train, [main_size, root_size], generator=torch.Generator().manual_seed(seed + 2)
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
    return DataBundle(
        client_loaders=[
            DataLoader(
                Subset(main_train, part),
                batch_size=batch_size,
                shuffle=True,
                generator=torch.Generator().manual_seed(seed + 10_000 + client_id),
            )
            for client_id, part in enumerate(parts)
        ],
        edge_mapping=edge_mapping,
        root_loader=DataLoader(
            root_set,
            batch_size=batch_size,
            shuffle=True,
            generator=torch.Generator().manual_seed(seed + 20_000),
        ),
        audit_loader=DataLoader(
            root_set,
            batch_size=batch_size,
            shuffle=True,
            generator=torch.Generator().manual_seed(seed + 30_000),
        ),
        test_loader=DataLoader(test, batch_size=batch_size, shuffle=False),
        backdoor_test_loader=DataLoader(
            BackdoorDataset(
                test,
                target_label=int(attack_cfg.get("target_label", 0)),
                source_label=None,
            ),
            batch_size=batch_size,
            shuffle=False,
        ),
        num_classes=int(np.max(y) + 1),
        input_shape=(x.shape[1],),
        input_dim=x.shape[1],
    )
