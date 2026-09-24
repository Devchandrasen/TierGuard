"""Fail-closed index of the nine exploratory CIFAR-10 clean-rate runs.

The index does not select a rate or substitute for attack/defence validation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import yaml


RATES = (0.005, 0.01, 0.02)
SEEDS = (2001, 2002, 2003)
EXPECTED = {(rate, seed) for rate in RATES for seed in SEEDS}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def index_runs(results_root: Path) -> dict:
    found = {}
    errors = []
    commits = set()
    partitions_by_seed = {}
    for final_path in sorted(results_root.rglob("final_metrics.json")):
        run_dir = final_path.parent
        final = json.loads(final_path.read_text(encoding="utf-8"))
        if final.get("experiment_name") != "tierguard2_cifar_clean_lr_exploratory":
            continue
        config_path = run_dir / "resolved_config.yaml"
        provenance_path = run_dir / "provenance.json"
        partition_path = run_dir / "partition_indices.json"
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        rate = float(config["federated"]["client_lr"])
        seed = int(config["experiment"]["seed"])
        key = (rate, seed)
        if key not in EXPECTED:
            errors.append(f"unexpected learning-rate task: {key}")
            continue
        if key in found:
            errors.append(f"duplicate completed learning-rate task: {key}")
            continue
        if (config["data"]["dataset"] != "cifar10" or
                config["model"]["name"] != "cifar_cnn" or
                config["aggregation"]["method"] != "hfl_fedavg" or
                config["attack"]["name"] != "none" or
                float(config["attack"]["malicious_fraction"]) != 0.0 or
                int(config["experiment"]["rounds"]) != 40 or
                int(final["final_round"]) != 40 or
                int(config["data"]["test_size"]) != 10000 or
                int(config["federated"]["num_clients"]) != 60 or
                int(config["federated"]["num_edges"]) != 6 or
                int(config["federated"]["clients_per_edge_per_round"]) != 5 or
                int(config["federated"]["local_epochs"]) != 2 or
                config.get("provenance", {}).get("require_clean_git") is not True):
            errors.append(f"protocol mismatch in {run_dir}")
        if provenance.get("git_worktree_dirty") is not False:
            errors.append(f"dirty or unknown source in {run_dir}")
        commits.add(str(provenance.get("git_commit")))
        with (run_dir / "metrics_per_round.csv").open(newline="", encoding="utf-8") as stream:
            if len(list(csv.DictReader(stream))) != 40:
                errors.append(f"incomplete round metrics in {run_dir}")
        if not partition_path.is_file():
            errors.append(f"missing explicit partition indices in {run_dir}")
        else:
            partitions = json.loads(partition_path.read_text(encoding="utf-8"))
            if len(partitions["test"]) != 10000:
                errors.append(f"test index count is not 10000 in {run_dir}")
            previous = partitions_by_seed.setdefault(seed, partitions)
            if partitions != previous:
                errors.append(f"non-identical paired partitions for seed {seed}")
        accuracy = float(final["clean_accuracy"])
        macro_f1 = float(final["macro_f1"])
        if not (math.isfinite(accuracy) and math.isfinite(macro_f1) and
                0 <= accuracy <= 1 and 0 <= macro_f1 <= 1):
            errors.append(f"non-finite or invalid clean metric in {run_dir}")
        if final.get("attack_success_rate") is not None:
            errors.append(f"ASR should be undefined in clean run {run_dir}")
        if int(final["stability_failures"]) != 0:
            errors.append(f"non-finite model update in {run_dir}")
        found[key] = {
            "rate": rate,
            "seed": seed,
            "clean_accuracy": accuracy,
            "macro_f1": macro_f1,
            "git_commit": provenance.get("git_commit"),
            "config_sha256": _digest(config_path),
            "provenance_sha256": _digest(provenance_path),
            "partition_sha256": _digest(partition_path) if partition_path.is_file() else None,
            "final_metrics_sha256": _digest(final_path),
            "run_dir": str(run_dir),
        }
    missing = sorted(EXPECTED - found.keys())
    if missing:
        errors.append(f"missing completed tasks: {missing}")
    if len(commits) != 1:
        errors.append(f"mixed source commits: {sorted(commits)}")
    summary = []
    for rate in RATES:
        rows = [found[(rate, seed)] for seed in SEEDS if (rate, seed) in found]
        if rows:
            summary.append({
                "rate": rate,
                "completed_seeds": [row["seed"] for row in rows],
                "clean_accuracy_mean": sum(row["clean_accuracy"] for row in rows) / len(rows),
                "clean_accuracy_min": min(row["clean_accuracy"] for row in rows),
                "macro_f1_mean": sum(row["macro_f1"] for row in rows) / len(rows),
            })
    return {
        "complete": not errors,
        "expected_run_count": len(EXPECTED),
        "observed_run_count": len(found),
        "errors": errors,
        "cell_summary": summary,
        "runs": sorted(found.values(), key=lambda row: (row["rate"], row["seed"])),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = index_runs(args.results_root)
    if args.output:
        if args.output.exists():
            raise FileExistsError(args.output)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "complete", "expected_run_count", "observed_run_count", "errors")}, indent=2))
    if not result["complete"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
