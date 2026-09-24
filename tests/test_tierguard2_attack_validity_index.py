from __future__ import annotations

import hashlib
import json

import pytest
import yaml

from scripts.index_tierguard2_attack_validity import ATTACKS, DATASETS, SEEDS, index_runs


def _run(root, dataset: str, attack: str, seed: int):
    run_dir = root / dataset / attack / f"seed_{seed}"
    run_dir.mkdir(parents=True)
    namespace = "tierguard2-draft-v1"
    instance = hashlib.sha256(
        f"{namespace}|{dataset}|{attack}|{seed}".encode("utf-8")
    ).hexdigest()
    config = {
        "experiment": {"name": "tierguard2_attack_validity_development",
                       "seed": seed, "rounds": 40},
        "data": {"dataset": dataset, "test_size": 10000},
        "aggregation": {"method": "hfl_fedavg"},
        "attack": {"name": attack, "malicious_fraction": 0.2,
                   "backdoor_fraction": 0.3, "instance_mode": "deterministic",
                   "instance_namespace": namespace, "instance_sha256": instance},
        "provenance": {"require_clean_git": True},
    }
    (run_dir / "resolved_config.yaml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )
    (run_dir / "provenance.json").write_text(json.dumps({
        "git_worktree_dirty": False, "git_commit": "a" * 40,
    }), encoding="utf-8")
    (run_dir / "partition_indices.json").write_text(json.dumps({
        "clients": {"0": [1, 2]}, "root": {"reference": [3]},
        "test": list(range(10000)),
    }), encoding="utf-8")
    (run_dir / "metrics_per_round.csv").write_text(
        "round\n" + "".join(f"{round_idx}\n" for round_idx in range(1, 41)),
        encoding="utf-8",
    )
    (run_dir / "final_metrics.json").write_text(json.dumps({
        "experiment_name": "tierguard2_attack_validity_development",
        "final_round": 40, "clean_accuracy": 0.8,
        "attack_success_rate": 0.7, "stability_failures": 0,
    }), encoding="utf-8")
    return run_dir


def test_attack_validity_index_requires_all_clean_attested_cells(tmp_path):
    for dataset in DATASETS:
        for attack in ATTACKS:
            for seed in SEEDS:
                _run(tmp_path, dataset, attack, seed)
    result = index_runs(tmp_path)
    assert result["complete"]
    assert result["observed_run_count"] == 27
    assert len(result["cell_summary"]) == 9
    assert all(cell["asr_mean"] == pytest.approx(0.7) for cell in result["cell_summary"])

    corrupt = tmp_path / "mnist" / ATTACKS[0] / "seed_2001" / "provenance.json"
    corrupt.write_text(json.dumps({
        "git_worktree_dirty": True, "git_commit": "a" * 40,
    }), encoding="utf-8")
    result = index_runs(tmp_path)
    assert not result["complete"]
    assert any("dirty or unknown source" in error for error in result["errors"])
