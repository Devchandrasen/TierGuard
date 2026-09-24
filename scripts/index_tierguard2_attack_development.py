"""Index one nine-run TierGuard 2 attack-development candidate against FedAvg.

This is descriptive development evidence only. It neither selects parameters
nor performs the prespecified confirmatory test.
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


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finite_unit(value: object) -> bool:
    number = float(value)
    return math.isfinite(number) and 0 <= number <= 1


def index_runs(results_root: Path, dataset: str, fedavg_index_path: Path,
               calibration_path: Path, clip: float = 8.0) -> dict:
    if dataset not in DATASETS:
        raise ValueError("Unsupported dataset")
    fedavg = json.loads(fedavg_index_path.read_text(encoding="utf-8"))
    if not fedavg.get("complete"):
        raise ValueError("FedAvg attack-validity index is not complete")
    baseline = {(row["attack"], int(row["seed"])): row
                for row in fedavg["runs"] if row["dataset"] == dataset}
    expected = {(attack, seed) for attack in ATTACKS for seed in SEEDS}
    if set(baseline) != expected:
        raise ValueError("FedAvg index does not contain the exact paired matrix")
    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
    if (calibration["dataset"] != dataset or
            calibration["development_seeds"] != list(SEEDS)):
        raise ValueError("Clean calibration is not matched to this dataset and seeds")
    client_threshold = float(calibration["calibrated_client_gain_threshold"])
    edge_threshold = float(calibration["calibrated_edge_gain_threshold"])
    if not (_finite_unit(client_threshold) and _finite_unit(edge_threshold)):
        raise ValueError("Invalid clean calibration thresholds")

    found = {}
    errors = []
    commits = set()
    for final_path in sorted(results_root.rglob("final_metrics.json")):
        run_dir = final_path.parent
        final = json.loads(final_path.read_text(encoding="utf-8"))
        config_path = run_dir / "resolved_config.yaml"
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if (config["data"]["dataset"] != dataset or
                config["aggregation"]["method"] != "tierguard2" or
                final.get("experiment_name") not in {
                    "tierguard2_fashion_attack_development_clip8",
                    "tierguard2_mnist_attack_development_clip8",
                }):
            continue
        attack = str(config["attack"]["name"])
        seed = int(config["experiment"]["seed"])
        key = (attack, seed)
        if key not in expected:
            errors.append(f"unexpected attack-development task: {key}")
            continue
        if key in found:
            errors.append(f"duplicate completed attack-development task: {key}")
            continue
        provenance_path = run_dir / "provenance.json"
        partition_path = run_dir / "partition_indices.json"
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        if (int(config["experiment"]["rounds"]) != 40 or
                int(final["final_round"]) != 40 or
                int(config["data"]["test_size"]) != 10000 or
                int(config["federated"]["num_clients"]) != 60 or
                int(config["federated"]["num_edges"]) != 6 or
                int(config["federated"]["clients_per_edge_per_round"]) != 5 or
                int(config["federated"]["local_epochs"]) != 2 or
                float(config["attack"]["malicious_fraction"]) != 0.2 or
                float(config["attack"]["backdoor_fraction"]) != 0.3 or
                float(config["tierguard2"]["clip_reference_multiplier"]) != clip or
                float(config["tierguard2"]["calibrated_client_gain_threshold"]) != client_threshold or
                float(config["tierguard2"]["calibrated_edge_gain_threshold"]) != edge_threshold or
                config["attack"]["instance_mode"] != "deterministic" or
                config.get("provenance", {}).get("require_clean_git") is not True):
            errors.append(f"protocol or calibration mismatch in {run_dir}")
        baseline_row = baseline[key]
        baseline_config = yaml.safe_load((Path(baseline_row["run_dir"]) /
                                          "resolved_config.yaml").read_text(encoding="utf-8"))
        if config["attack"]["instance_sha256"] != baseline_config["attack"]["instance_sha256"]:
            errors.append(f"non-identical attack instance in {run_dir}")
        if provenance.get("git_worktree_dirty") is not False:
            errors.append(f"dirty or unknown source in {run_dir}")
        commits.add(str(provenance.get("git_commit")))
        with (run_dir / "metrics_per_round.csv").open(newline="", encoding="utf-8") as stream:
            if len(list(csv.DictReader(stream))) != 40:
                errors.append(f"incomplete round metrics in {run_dir}")
        if not partition_path.is_file() or _digest(partition_path) != baseline_row["partition_sha256"]:
            errors.append(f"non-identical paired partitions in {run_dir}")
        clean = float(final["clean_accuracy"])
        asr = float(final["attack_success_rate"])
        if not (_finite_unit(clean) and _finite_unit(asr)):
            errors.append(f"non-finite or invalid final metric in {run_dir}")
        if int(final["stability_failures"]) != 0:
            errors.append(f"non-finite model update in {run_dir}")
        audit_paths = sorted(run_dir.glob("audit_round_*.json"))
        if len(audit_paths) != 40:
            errors.append(f"incomplete audit records in {run_dir}")
        separation_positive = 0
        separation_count = 0
        for audit_path in audit_paths:
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            if (len(audit["client_audits"]) != 30 or
                    len(audit["edge_audits"]) != 6 or
                    len(audit["edge_minus_client_risk"]) != 6 or
                    audit["expected_edge_reports"] != 6 or
                    audit["received_edge_reports"] != 6 or
                    len(audit["challenged_edges"]) != 3 or
                    audit["rejected_edges"] or audit["missing_edge_reports"]):
                errors.append(f"incomplete or rejected audit round in {audit_path}")
                continue
            if not all(_finite_unit(item["risk"]) for item in audit["client_audits"] +
                       audit["edge_audits"]):
                errors.append(f"invalid audit risk in {audit_path}")
            if not all(
                math.isfinite(float(item["heldout_target_gain"])) and
                -1 <= float(item["heldout_target_gain"]) <= 1 and
                math.isfinite(float(item["clean_loss_change"]))
                for item in audit["client_audits"] + audit["edge_audits"]
            ):
                errors.append(f"invalid audit counterfactual score in {audit_path}")
            separations = [float(value) for value in audit["edge_minus_client_risk"]]
            if not all(math.isfinite(value) and -1 <= value <= 1 for value in separations):
                errors.append(f"invalid edge-client separation in {audit_path}")
            separation_positive += sum(value > 0 for value in separations)
            separation_count += len(separations)
        found[key] = {
            "dataset": dataset,
            "attack": attack,
            "seed": seed,
            "clean_accuracy": clean,
            "attack_success_rate": asr,
            "fedavg_clean_accuracy": baseline_row["clean_accuracy"],
            "fedavg_attack_success_rate": baseline_row["attack_success_rate"],
            "asr_difference_tierguard2_minus_fedavg": asr - baseline_row["attack_success_rate"],
            "clean_difference_tierguard2_minus_fedavg": clean - baseline_row["clean_accuracy"],
            "edge_risk_exceeds_client_suggestion_count": separation_positive,
            "edge_risk_comparisons": separation_count,
            "git_commit": provenance.get("git_commit"),
            "config_sha256": _digest(config_path),
            "provenance_sha256": _digest(provenance_path),
            "partition_sha256": _digest(partition_path) if partition_path.is_file() else None,
            "final_metrics_sha256": _digest(final_path),
            "run_dir": str(run_dir),
        }
    missing = sorted(expected - found.keys())
    if missing:
        errors.append(f"missing completed tasks: {missing}")
    if len(commits) != 1:
        errors.append(f"mixed source commits: {sorted(commits)}")
    summary = []
    for attack in ATTACKS:
        rows = [found[(attack, seed)] for seed in SEEDS if (attack, seed) in found]
        if rows:
            summary.append({
                "attack": attack,
                "completed_seeds": [row["seed"] for row in rows],
                "asr_mean": sum(row["attack_success_rate"] for row in rows) / len(rows),
                "asr_difference_mean": sum(row["asr_difference_tierguard2_minus_fedavg"]
                                           for row in rows) / len(rows),
                "clean_difference_mean": sum(row["clean_difference_tierguard2_minus_fedavg"]
                                             for row in rows) / len(rows),
            })
    return {
        "complete": not errors,
        "dataset": dataset,
        "expected_run_count": len(expected),
        "observed_run_count": len(found),
        "errors": errors,
        "cell_summary": summary,
        "calibration_sha256": _digest(calibration_path),
        "fedavg_index_sha256": _digest(fedavg_index_path),
        "runs": sorted(found.values(), key=lambda row: (row["attack"], row["seed"])),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", required=True, type=Path)
    parser.add_argument("--dataset", required=True, choices=DATASETS)
    parser.add_argument("--fedavg-index", required=True, type=Path)
    parser.add_argument("--calibration", required=True, type=Path)
    parser.add_argument("--clip", type=float, default=8.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = index_runs(args.results_root, args.dataset, args.fedavg_index,
                        args.calibration, args.clip)
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
