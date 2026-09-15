from __future__ import annotations

from tierguard.data.datasets import SyntheticImageDataset
from tierguard.data.partition import partition_dataset


def test_partition_returns_clients_and_edges():
    dataset = SyntheticImageDataset(size=100, seed=1)
    parts, edges = partition_dataset(
        dataset,
        num_clients=10,
        mode="dirichlet",
        alpha=0.5,
        iid=False,
        seed=1,
        num_edges=2,
    )
    assert len(parts) == 10
    assert sum(len(part) for part in parts) == 100
    assert len(edges) == 2
    assert sorted(client for clients in edges.values() for client in clients) == list(range(10))
