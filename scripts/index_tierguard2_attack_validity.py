"""Fail-closed index for the 27 prespecified FedAvg attack-development runs.

This checks provenance and comparability, then reports attack strength. It
does not choose an attack, defence setting or confirmatory comparator.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import yaml


DATASETS = ("mnist", "fashionmnist", "cifar10")
ATTACKS = (
    "unknown_patch_model_replacement",
    "distributed_backdoor",
    "defence_aware_optimized_trigger",
)
SEEDS = (2001, 2002, 2003)
EXPECTED = {(dataset, attack, seed) for dataset in DATASETS
            for attack in ATTACKS for seed in SEEDS}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def index_runs(results_root: Path) -> dict:
    found = {}
    errors = []
    commits = set()
    partitions_by_dataset_seed: dict[tuple[str, int], dict] = {}
    for final_path in sorted(results_root.rglob("final_metrics.json")):
        run_dir = final_path.parent
        final = json.loads(final_path.read_text(encoding="utf-8"))
        if final.get("experiment_name") != "tierguard2_attack_validity_development":
            continue
        config_path = run_dir / "resolved_config.yaml"
        provenance_path = run_dir / "provenance.json"
        partition_path = run_dir / "partition_indices.json"
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        dataset = str(config["data"]["dataset"])
        attack = str(config["attack"]["name"])
        seed = int(config["experiment"]["seed"])
        key = (dataset, attack, seed)
        if key not in EXPECTED:
            errors.append(f"unexpected attack-validity task: {key}")
            continue
        if key in found:
            errors.append(f"duplicate completed attack-validity task: {key}")
            continue
        if (config["aggregation"]["method"] != "hfl_fedavg" or
                int(config["experiment"]["rounds"]) != 40 or
                int(final["final_round"]) != 40 or
                int(config["data"]["test_size"]) != 10000 or
                float(config["attack"]["malicious_fraction"]) != 0.2 or
                float(config["attack"]["backdoor_fraction"]) != 0.3 or
                config["attack"]["instance_mode"] != "deterministic" or
                config.get("provenance", {}).get("require_clean_git") is not True):
            errors.append(f"protocol mismatch in {run_dir}")
        namespace = str(config["attack"].get("instance_namespace"))
        expected_instance = hashlib.sha256(
            f"{namespace}|{dataset}|{attack}|{seed}".encode("utf-8")
        ).hexdigest()
        if config["attack"].get("instance_sha256") != expected_instance:
            errors.append(f"attack instance mismatch in {run_dir}")
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
            previous = partitions_by_dataset_seed.setdefault((dataset, seed), partitions)
            if previous != partitions:
                errors.append(f"non-identical paired partitions for {dataset}, seed {seed}")
        clean = float(final["clean_accuracy"])
        asr = float(final["attack_success_rate"])
        if not (math.isfinite(clean) and math.isfinite(asr) and
                0 <= clean <= 1 and 0 <= asr <= 1):
            errors.append(f"non-finite or invalid final metric in {run_dir}")
        if int(final["stability_failures"]) != 0:
            errors.append(f"non-finite model update in {run_dir}")
        found[key] = {
            "dataset": dataset,
            "attack": attack,
            "seed": seed,
            "clean_accuracy": clean,
            "attack_success_rate": asr,
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
    for dataset in DATASETS:
        for attack in ATTACKS:
            rows = [found[(dataset, attack, seed)] for seed in SEEDS
                    if (dataset, attack, seed) in found]
            if rows:
                summary.append({
                    "dataset": dataset,
                    "attack": attack,
                    "completed_seeds": [row["seed"] for row in rows],
                    "asr_mean": sum(row["attack_success_rate"] for row in rows) / len(rows),
                    "asr_min": min(row["attack_success_rate"] for row in rows),
                    "clean_accuracy_mean": sum(row["clean_accuracy"] for row in rows) / len(rows),
                })
    return {
        "complete": not errors,
        "expected_run_count": len(EXPECTED),
        "observed_run_count": len(found),
        "errors": errors,
        "cell_summary": summary,
        "runs": sorted(found.values(), key=lambda row: (
            row["dataset"], row["attack"], row["seed"])),
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
