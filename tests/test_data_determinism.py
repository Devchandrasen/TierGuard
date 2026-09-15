from __future__ import annotations

import torch

from tierguard.data.datasets import make_data_bundle


def _synthetic_config() -> dict:
    return {
        "experiment": {"seed": 101},
        "federated": {"num_clients": 4, "num_edges": 2, "batch_size": 8},
        "data": {
            "dataset": "mnist",
            "synthetic": True,
            "train_size": 120,
            "test_size": 40,
            "root_dataset_size": 20,
            "partition": "dirichlet",
            "dirichlet_alpha": 0.5,
            "iid": False,
        },
        "attack": {"target_label": 0},
    }


def test_audit_loader_does_not_advance_reference_or_client_shuffle():
    audited = make_data_bundle(_synthetic_config())
    control = make_data_bundle(_synthetic_config())

    next(iter(audited.audit_loader))
    audited_root = next(iter(audited.root_loader))
    control_root = next(iter(control.root_loader))
    audited_client = next(iter(audited.client_loaders[0]))
    control_client = next(iter(control.client_loaders[0]))

    assert torch.equal(audited_root[0], control_root[0])
    assert torch.equal(audited_root[1], control_root[1])
    assert torch.equal(audited_client[0], control_client[0])
    assert torch.equal(audited_client[1], control_client[1])
