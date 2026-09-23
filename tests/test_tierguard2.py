from __future__ import annotations

from dataclasses import replace

import pytest
import torch
from torch.utils.data import DataLoader, TensorDataset

from tierguard.aggregators.tierguard2 import CounterfactualAuditor, aggregate_level
from tierguard.aggregators.flame_hierarchical import HierarchicalFlameAggregator
from tierguard.aggregators.fedgame_hierarchical import HierarchicalFedGameAggregator
from tierguard.data.datasets import SyntheticImageDataset
from tierguard.data.datasets import make_data_bundle
from tierguard.data.root_splits import stratified_root_split
from tierguard.fl.hierarchical_runner import _selected_clients_per_edge
from tierguard.fl.hierarchical_runner import _aggregate_tierguard2
from tierguard.fl.client import ClientUpdate
from tierguard.security.edge_receipts import (
    ReceiptAuthority, choose_challenges, commit_edge, single_report_escape_probability,
    verify_challenged_report,
)
from tierguard.data.backdoor import add_configured_trigger
from tierguard.attacks.optimized_trigger import optimize_trigger


def test_root_partitions_are_balanced_disjoint_and_repeatable():
    dataset = SyntheticImageDataset(100, num_classes=10, seed=7)
    first = stratified_root_split(dataset, (20, 20, 20), 42)
    assert first == stratified_root_split(dataset, (20, 20, 20), 42)
    assert set().union(*(set(items) for items in first.values())) == set(range(100))
    names = list(first)
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            assert not set(first[left]) & set(first[right])
    for name in ("reference", "search", "evaluation"):
        assert sorted(dataset.targets[index] for index in first[name]) == sorted(list(range(10)) * 2)


def test_new_study_baseline_uses_identical_partitions():
    config = {
        "experiment": {"seed": 11},
        "federated": {"num_clients": 10, "num_edges": 2, "batch_size": 10},
        "data": {"dataset": "mnist", "synthetic": True, "train_size": 100,
                 "test_size": 30, "root_dataset_size": 20, "audit_search_size": 10,
                 "audit_eval_size": 10, "three_way_root_split": True, "iid": True},
        "attack": {"name": "none"},
        "aggregation": {"method": "tierguard2"},
    }
    candidate = make_data_bundle(config)
    config["aggregation"]["method"] = "hfl_fedavg"
    baseline = make_data_bundle(config)
    assert candidate.partition_indices == baseline.partition_indices


def test_root_contamination_keeps_client_and_test_indices_fixed():
    config = {
        "experiment": {"seed": 11},
        "federated": {"num_clients": 10, "num_edges": 2, "batch_size": 10},
        "data": {"dataset": "mnist", "synthetic": True, "train_size": 100,
                 "test_size": 30, "root_dataset_size": 20, "audit_search_size": 10,
                 "audit_eval_size": 10, "three_way_root_split": True, "iid": True},
        "attack": {"name": "unknown_patch_model_replacement", "target_label": 5,
                   "trigger_top": 0, "trigger_left": 0},
        "aggregation": {"method": "tierguard2"},
    }
    clean = make_data_bundle(config).partition_indices
    config["data"]["root_contamination_fraction"] = 0.2
    poisoned = make_data_bundle(config).partition_indices
    assert clean["clients"] == poisoned["clients"]
    assert clean["test"] == poisoned["test"]
    assert sum(len(items) for items in poisoned["root_contamination"].values()) == 8


def test_counterfactual_auditor_and_continuous_aggregation():
    torch.manual_seed(3)
    images = torch.rand(8, 1, 8, 8)
    labels = torch.tensor([0, 1, 0, 1, 0, 1, 0, 1])
    search = DataLoader(TensorDataset(images[:4], labels[:4]), batch_size=4)
    evaluation = DataLoader(TensorDataset(images[4:], labels[4:]), batch_size=4)
    settings = {"probes_per_class": 2, "patch_sizes": [2],
                "calibrated_gain_threshold": 0.0, "risk_gamma": 5.0}
    auditor = CounterfactualAuditor(search, evaluation, 2, settings, torch.device("cpu"))
    model = torch.nn.Sequential(torch.nn.Flatten(), torch.nn.Linear(64, 2))
    update = torch.zeros(sum(p.numel() for p in model.parameters()))
    result = auditor.audit(model, update)
    assert result.risk == pytest.approx(0.0, abs=1e-7)
    assert result.heldout_target_gain == pytest.approx(0.0, abs=1e-7)
    assert result.target_class in (0, 1)
    averaged, weights = aggregate_level(
        [torch.tensor([1.0]), torch.tensor([100.0])], [1, 1], [0.0, 1.0], 2.0, settings
    )
    assert 1.0 <= float(averaged) < 1.5
    assert weights[0] > weights[1]


def test_counterfactual_audit_detects_heldout_functional_change():
    images = torch.zeros(8, 1, 8, 8)
    images[:, :, 0, 0] = 1.0
    labels = torch.tensor([0, 1] * 4)
    settings = {"probes_per_class": 2, "patch_sizes": [2],
                "calibrated_gain_threshold": 0.0}
    auditor = CounterfactualAuditor(
        DataLoader(TensorDataset(images[:4], labels[:4]), batch_size=4),
        DataLoader(TensorDataset(images[4:], labels[4:]), batch_size=4),
        2, settings, torch.device("cpu"),
    )
    model = torch.nn.Sequential(torch.nn.Flatten(), torch.nn.Linear(64, 2, bias=False))
    torch.nn.init.zeros_(model[1].weight)
    update = torch.zeros(128)
    update[64 + 63] = 4.0
    detected = auditor.audit(model, update)
    assert detected.target_class == 1
    assert detected.heldout_target_gain > 0.45
    assert detected.risk > 0.45


def test_per_edge_selection_is_balanced_and_deterministic():
    mapping = {0: list(range(10)), 1: list(range(10, 20))}
    chosen = _selected_clients_per_edge(mapping, 5, 4, 1)
    assert chosen == _selected_clients_per_edge(mapping, 5, 4, 1)
    assert len(set(chosen) & set(mapping[0])) == 5
    assert len(set(chosen) & set(mapping[1])) == 5


def test_configured_patch_and_distributed_attack_patterns():
    image = torch.zeros(1, 8, 8)
    top_left = add_configured_trigger(
        image, {"name": "unknown_patch_model_replacement", "trigger_size": 2,
                "trigger_top": 0, "trigger_left": 0, "trigger_value": 1.0}
    )
    assert torch.all(top_left[:, :2, :2] == 1)
    assert torch.all(top_left[:, -2:, -2:] == 0)
    distributed = add_configured_trigger(
        image, {"name": "distributed_backdoor", "trigger_size": 2}
    )
    assert sum(float(distributed[:, row, col]) for row, col in
               ((0, 0), (0, 7), (7, 0), (7, 7))) == 4.0


def test_defence_aware_attack_uses_only_local_images_and_global_model():
    images = torch.rand(4, 1, 8, 8)
    labels = torch.tensor([0, 0, 1, 1])
    loader = DataLoader(TensorDataset(images, labels), batch_size=4)
    model = torch.nn.Sequential(torch.nn.Flatten(), torch.nn.Linear(64, 2))
    settings = {"target_label": 1, "trigger_size": 2, "trigger_top": 0,
                "trigger_left": 0, "optimize_items": 2, "optimize_steps": 2}
    trigger = optimize_trigger(model, loader, settings, torch.device("cpu"), seed=7)
    assert trigger.shape == (1, 2, 2)
    assert torch.isfinite(trigger).all()
    attacked = add_configured_trigger(
        images[0], {"name": "defence_aware_optimized_trigger", **settings,
                    "trigger_tensor": trigger}
    )
    assert torch.equal(attacked[:, :2, :2], trigger)


def test_hierarchical_flame_adaptation_is_replayable_for_challenges():
    config = {"experiment": {"seed": 9}, "flame": {"noise_multiplier": 0.01}}
    aggregator = HierarchicalFlameAggregator(config)
    updates = [torch.tensor([1.0, 0.0]) + 0.01 * i for i in range(4)]
    updates.append(torch.tensor([-10.0, 10.0]))
    first = aggregator.aggregate(updates, round_idx=2, edge_id=1,
                                 global_vector=torch.tensor([0.2, 0.3]))
    again = HierarchicalFlameAggregator(config).aggregate(
        updates, round_idx=2, edge_id=1, global_vector=torch.tensor([0.2, 0.3])
    )
    assert torch.equal(first.update, again.update)
    assert len(first.suspicion) == 5


def test_hierarchical_fedgame_defender_adapter_replays():
    config = {
        "experiment": {"seed": 9},
        "fedgame": {"reconstruction_steps": 1, "reconstruction_lr": 0.005,
                    "mask_penalty": 0.01, "root_items": 4},
    }
    images = torch.rand(4, 1, 8, 8)
    labels = torch.tensor([0, 1, 0, 1])
    root = DataLoader(TensorDataset(images, labels), batch_size=4)
    model = torch.nn.Sequential(torch.nn.Flatten(), torch.nn.Linear(64, 2))
    updates = [torch.zeros(130), torch.ones(130) * 0.001]
    first = HierarchicalFedGameAggregator(config).aggregate(
        updates, model=model, root_loader=root, device=torch.device("cpu"),
        round_idx=1, edge_id=0,
    )
    again = HierarchicalFedGameAggregator(config).aggregate(
        updates, model=model, root_loader=root, device=torch.device("cpu"),
        round_idx=1, edge_id=0,
    )
    assert torch.equal(first.update, again.update)
    assert len(first.metadata["mask_norms"]) == 2


def test_signed_receipts_detect_forgery_replay_and_wrong_aggregate():
    authority = ReceiptAuthority([1, 2])
    raw = {1: torch.tensor([1.0, 2.0]), 2: torch.tensor([3.0, 4.0])}
    receipts = [authority.sign(round_idx=1, model_hash="abc", client_id=client,
                               edge_id=0, sample_mass=1, update=raw[client])
                for client in (1, 2)]
    report = commit_edge(1, 0, torch.tensor([2.0, 3.0]), receipts)
    def recompute(updates, masses):
        return torch.stack(updates).mean(dim=0)
    assert verify_challenged_report(report, raw, authority, round_idx=1,
                                    model_hash="abc", recompute=recompute) == 16
    with pytest.raises(ValueError, match="Replayed"):
        verify_challenged_report(report, raw, authority, round_idx=1,
                                 model_hash="abc", recompute=recompute)
    fresh = ReceiptAuthority([1, 2])
    signed = [fresh.sign(round_idx=1, model_hash="abc", client_id=client,
                         edge_id=0, sample_mass=1, update=raw[client])
              for client in (1, 2)]
    tampered = commit_edge(1, 0, torch.tensor([2.0, 3.0]),
                           [replace(signed[0], sample_mass=2), signed[1]])
    with pytest.raises(ValueError, match="Invalid client signature"):
        verify_challenged_report(tampered, raw, fresh, round_idx=1,
                                 model_hash="abc", recompute=recompute)
    wrong = commit_edge(1, 0, torch.tensor([9.0, 9.0]), signed)
    with pytest.raises(ValueError, match="aggregate does not match"):
        verify_challenged_report(wrong, raw, ReceiptAuthorityProxy(fresh), round_idx=1,
                                 model_hash="abc", recompute=recompute)
    assert len(choose_challenges([report, commit_edge(1, 1, raw[1], [])])) == 1
    assert single_report_escape_probability(6) == 0.5


def test_challenged_compromised_edge_is_rejected(monkeypatch):
    images = torch.rand(4, 1, 8, 8)
    labels = torch.tensor([0, 1, 0, 1])
    loader = DataLoader(TensorDataset(images, labels), batch_size=4)
    settings = {"probes_per_class": 2, "patch_sizes": [2],
                "calibrated_gain_threshold": 1.0, "clip_floor": 0.1,
                "clip_reference_multiplier": 2.0}
    auditor = CounterfactualAuditor(loader, loader, 2, settings, torch.device("cpu"))
    model = torch.nn.Sequential(torch.nn.Flatten(), torch.nn.Linear(64, 2))
    updates = [torch.ones(130) * 0.001, torch.ones(130) * 0.002]
    clients = [
        ClientUpdate(update=update, client_id=index, edge_id=index, num_samples=10,
                     malicious=False, local_loss=0.0, local_accuracy=0.0)
        for index, update in enumerate(updates)
    ]
    config = {"tierguard2": settings, "federated": {"server_lr": 1.0},
              "edge_attack": {"name": "aggregate_replacement", "edge_id": 0,
                              "scale": 2.0}}
    monkeypatch.setattr("tierguard.fl.hierarchical_runner.choose_challenges",
                        lambda reports: {0})
    auditor.begin_round(model)
    _, metadata, _ = _aggregate_tierguard2(
        clients, model, auditor, torch.ones(130) * 0.01,
        config, ReceiptAuthority([0, 1]), 1,
    )
    assert metadata["aggregation_metadata"]["rejected_edges"] == [0]


class ReceiptAuthorityProxy:
    """Fresh replay ledger with the same public keys, for the independent check."""

    def __init__(self, authority):
        self.public_keys = authority.public_keys
        self._seen = set()

    verify = ReceiptAuthority.verify
    verify_signature = ReceiptAuthority.verify_signature
