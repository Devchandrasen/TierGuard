from __future__ import annotations

import csv
import json

import yaml

from scripts.index_tierguard2_cifar_lr_development import EXPECTED, index_runs


def _write_run(root, rate, seed):
    path = root / str(rate) / str(seed)
    path.mkdir(parents=True)
    config = {
        "experiment": {"seed": seed, "rounds": 40},
        "federated": {"client_lr": rate, "num_clients": 60, "num_edges": 6,
                      "clients_per_edge_per_round": 5, "local_epochs": 2},
        "data": {"dataset": "cifar10", "test_size": 10000},
        "model": {"name": "cifar_cnn"},
        "aggregation": {"method": "hfl_fedavg"},
        "attack": {"name": "none", "malicious_fraction": 0.0},
        "provenance": {"require_clean_git": True},
    }
    (path / "resolved_config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    (path / "provenance.json").write_text(json.dumps({
        "git_commit": "a" * 40, "git_worktree_dirty": False,
    }), encoding="utf-8")
    (path / "partition_indices.json").write_text(json.dumps({
        "seed": seed, "test": list(range(10000)),
    }), encoding="utf-8")
    (path / "final_metrics.json").write_text(json.dumps({
        "experiment_name": "tierguard2_cifar_clean_lr_exploratory",
        "final_round": 40, "clean_accuracy": 0.6, "macro_f1": 0.58,
        "attack_success_rate": None, "stability_failures": 0,
    }), encoding="utf-8")
    with (path / "metrics_per_round.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["round"])
        writer.writeheader()
        writer.writerows({"round": number} for number in range(1, 41))
    return path


def test_cifar_rate_index_requires_complete_attested_matrix(tmp_path):
    for rate, seed in EXPECTED:
        _write_run(tmp_path, rate, seed)
    result = index_runs(tmp_path)
    assert result["complete"]
    assert result["observed_run_count"] == 9
    assert len(result["cell_summary"]) == 3


def test_cifar_rate_index_rejects_nonfinite_run(tmp_path):
    for rate, seed in EXPECTED:
        path = _write_run(tmp_path, rate, seed)
        if (rate, seed) == (0.01, 2002):
            metrics_path = path / "final_metrics.json"
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            metrics["stability_failures"] = 1
            metrics_path.write_text(json.dumps(metrics), encoding="utf-8")
    result = index_runs(tmp_path)
    assert not result["complete"]
    assert any("non-finite model update" in item for item in result["errors"])
