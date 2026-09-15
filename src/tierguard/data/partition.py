from __future__ import annotations

import numpy as np


def labels_to_numpy(dataset) -> np.ndarray:
    if hasattr(dataset, "targets"):
        targets = dataset.targets
        return np.asarray(targets, dtype=np.int64)
    labels = []
    for idx in range(len(dataset)):
        labels.append(int(dataset[idx][1]))
    return np.asarray(labels, dtype=np.int64)


def build_edge_mapping(num_clients: int, num_edges: int) -> dict[int, list[int]]:
    mapping: dict[int, list[int]] = {edge: [] for edge in range(num_edges)}
    for client_id in range(num_clients):
        mapping[client_id % num_edges].append(client_id)
    return mapping


def client_to_edge(edge_mapping: dict[int, list[int]]) -> dict[int, int]:
    return {client: edge for edge, clients in edge_mapping.items() for client in clients}


def partition_iid(num_items: int, num_clients: int, rng: np.random.Generator) -> list[list[int]]:
    indices = rng.permutation(num_items)
    return [chunk.tolist() for chunk in np.array_split(indices, num_clients)]


def partition_dirichlet(
    labels: np.ndarray,
    num_clients: int,
    alpha: float,
    rng: np.random.Generator,
    min_size: int = 1,
) -> list[list[int]]:
    num_classes = int(labels.max()) + 1
    for _ in range(100):
        client_indices = [[] for _ in range(num_clients)]
        for cls in range(num_classes):
            cls_indices = np.where(labels == cls)[0]
            rng.shuffle(cls_indices)
            proportions = rng.dirichlet(np.repeat(alpha, num_clients))
            cuts = (np.cumsum(proportions) * len(cls_indices)).astype(int)[:-1]
            for client_id, split in enumerate(np.split(cls_indices, cuts)):
                client_indices[client_id].extend(split.tolist())
        if min(len(items) for items in client_indices) >= min_size:
            for items in client_indices:
                rng.shuffle(items)
            return client_indices
    return partition_iid(len(labels), num_clients, rng)


def partition_label_shard(
    labels: np.ndarray, num_clients: int, shards_per_client: int, rng: np.random.Generator
) -> list[list[int]]:
    sorted_indices = np.argsort(labels)
    num_shards = num_clients * shards_per_client
    shards = np.array_split(sorted_indices, num_shards)
    shard_order = rng.permutation(num_shards)
    client_indices = [[] for _ in range(num_clients)]
    for client_id in range(num_clients):
        for shard_idx in shard_order[client_id * shards_per_client : (client_id + 1) * shards_per_client]:
            client_indices[client_id].extend(shards[shard_idx].tolist())
        rng.shuffle(client_indices[client_id])
    return client_indices


def partition_edge_skewed(
    labels: np.ndarray,
    num_clients: int,
    num_edges: int,
    alpha: float,
    rng: np.random.Generator,
) -> list[list[int]]:
    edge_mapping = build_edge_mapping(num_clients, num_edges)
    edge_indices = partition_dirichlet(labels, num_edges, alpha, rng)
    client_indices = [[] for _ in range(num_clients)]
    for edge_id, clients in edge_mapping.items():
        chunks = np.array_split(rng.permutation(edge_indices[edge_id]), len(clients))
        for client_id, chunk in zip(clients, chunks):
            client_indices[client_id] = chunk.tolist()
    return client_indices


def partition_dataset(
    dataset,
    num_clients: int,
    mode: str,
    alpha: float,
    iid: bool,
    seed: int,
    num_edges: int,
) -> tuple[list[list[int]], dict[int, list[int]]]:
    rng = np.random.default_rng(seed)
    labels = labels_to_numpy(dataset)
    if iid or mode == "iid":
        parts = partition_iid(len(dataset), num_clients, rng)
    elif mode == "label_shard":
        parts = partition_label_shard(labels, num_clients, shards_per_client=2, rng=rng)
    elif mode == "edge_skewed":
        parts = partition_edge_skewed(labels, num_clients, num_edges, alpha, rng)
    else:
        parts = partition_dirichlet(labels, num_clients, alpha, rng)
    return parts, build_edge_mapping(num_clients, num_edges)
