from __future__ import annotations

import csv
import hashlib
import json

import pytest
import yaml

from scripts.index_tierguard2_attack_development import index_runs
from scripts.index_tierguard2_attack_validity import ATTACKS, SEEDS


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _matrix(tmp_path):
    baseline_root = tmp_path / "baseline"
    candidate_root = tmp_path / "candidate"
    baseline_rows = []
    for attack in ATTACKS:
        for seed in SEEDS:
            instance = hashlib.sha256(
                f"tierguard2-draft-v1|mnist|{attack}|{seed}".encode()
            ).hexdigest()
            baseline_dir = baseline_root / attack / str(seed)
            baseline_dir.mkdir(parents=True)
            (baseline_dir / "resolved_config.yaml").write_text(yaml.safe_dump({
                "attack": {"instance_sha256": instance},
            }), encoding="utf-8")
            candidate_dir = candidate_root / attack / str(seed)
            candidate_dir.mkdir(parents=True)
            config = {
                "experiment": {"name": "tierguard2_mnist_attack_development_clip8",
                               "seed": seed, "rounds": 40},
                "data": {"dataset": "mnist", "test_size": 10000},
                "federated": {"num_clients": 60, "num_edges": 6,
                              "clients_per_edge_per_round": 5, "local_epochs": 2},
                "aggregation": {"method": "tierguard2"},
                "attack": {"name": attack, "malicious_fraction": 0.2,
                           "backdoor_fraction": 0.3, "instance_mode": "deterministic",
                           "instance_sha256": instance},
                "tierguard2": {"clip_reference_multiplier": 8.0,
                               "calibrated_client_gain_threshold": 0.2,
                               "calibrated_edge_gain_threshold": 0.1},
                "provenance": {"require_clean_git": True},
            }
            (candidate_dir / "resolved_config.yaml").write_text(
                yaml.safe_dump(config), encoding="utf-8")
            (candidate_dir / "provenance.json").write_text(json.dumps({
                "git_commit": "a" * 40, "git_worktree_dirty": False,
            }), encoding="utf-8")
            partition = {"test": list(range(10000)), "seed": seed}
            partition_path = candidate_dir / "partition_indices.json"
            partition_path.write_text(json.dumps(partition), encoding="utf-8")
            baseline_rows.append({
                "dataset": "mnist", "attack": attack, "seed": seed,
                "run_dir": str(baseline_dir), "partition_sha256": _digest(partition_path),
                "clean_accuracy": 0.8, "attack_success_rate": 0.9,
            })
            (candidate_dir / "final_metrics.json").write_text(json.dumps({
                "experiment_name": "tierguard2_mnist_attack_development_clip8",
                "final_round": 40, "clean_accuracy": 0.79,
                "attack_success_rate": 0.5, "stability_failures": 0,
            }), encoding="utf-8")
            with (candidate_dir / "metrics_per_round.csv").open(
                    "w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=["round"])
                writer.writeheader()
                writer.writerows({"round": number} for number in range(1, 41))
            audit = {
                "client_audits": [{"risk": 0.1, "heldout_target_gain": 0.1,
                                   "clean_loss_change": 0.0}] * 30,
                "edge_audits": [{"risk": 0.2, "heldout_target_gain": 0.2,
                                 "clean_loss_change": 0.0}] * 6,
                "edge_minus_client_risk": [0.1] * 6,
                "expected_edge_reports": 6, "received_edge_reports": 6,
                "challenged_edges": [0, 2, 4], "rejected_edges": [],
                "missing_edge_reports": [],
            }
            for round_idx in range(1, 41):
                (candidate_dir / f"audit_round_{round_idx:03d}.json").write_text(
                    json.dumps(audit), encoding="utf-8")
    baseline_index = tmp_path / "baseline_index.json"
    baseline_index.write_text(json.dumps({"complete": True, "runs": baseline_rows}),
                              encoding="utf-8")
    calibration = tmp_path / "calibration.json"
    calibration.write_text(json.dumps({
        "dataset": "mnist", "development_seeds": list(SEEDS),
        "calibrated_client_gain_threshold": 0.2,
        "calibrated_edge_gain_threshold": 0.1,
    }), encoding="utf-8")
    return candidate_root, baseline_index, calibration


def test_attack_development_index_pairs_all_nine_cells(tmp_path):
    candidate_root, baseline_index, calibration = _matrix(tmp_path)
    result = index_runs(candidate_root, "mnist", baseline_index, calibration)
    assert result["complete"]
    assert result["observed_run_count"] == 9
    assert all(row["asr_difference_mean"] == pytest.approx(-0.4)
               for row in result["cell_summary"])
    assert all(row["edge_risk_exceeds_client_suggestion_count"] == 240
               for row in result["runs"])


def test_attack_development_index_rejects_pairing_mismatch(tmp_path):
    candidate_root, baseline_index, calibration = _matrix(tmp_path)
    config_path = (candidate_root / ATTACKS[0] / str(SEEDS[0]) /
                   "resolved_config.yaml")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["attack"]["instance_sha256"] = "wrong"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    result = index_runs(candidate_root, "mnist", baseline_index, calibration)
    assert not result["complete"]
    assert any("non-identical attack instance" in error for error in result["errors"])
