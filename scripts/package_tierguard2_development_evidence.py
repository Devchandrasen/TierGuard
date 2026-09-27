"""Validate a downloaded development snapshot and package it without claim inflation.

This does not train models, submit jobs, select a method or create a manuscript.
Remote absolute run paths in indices are mapped to the snapshot's raw directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import zipfile

import yaml


REMOTE_ROOT = "/home/chandrasen.pandey/tierguard2_env_2026_09_23/"
EXPECTED_CLONES = {
    "project_dev_attested": 9,
    "project_attack_dev": 27,
    "project_clean_dev_more": 18,
    "project_t2_attack_dev": 2,
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_path(root: Path, remote: str) -> Path:
    if not remote.startswith(REMOTE_ROOT):
        raise ValueError(f"Unexpected remote path: {remote}")
    relative = Path(remote[len(REMOTE_ROOT):])
    if ".." in relative.parts or relative.parts[0] not in EXPECTED_CLONES:
        raise ValueError(f"Path outside evidence scope: {remote}")
    return root / "raw" / relative


def validate(root: Path) -> dict:
    errors = []
    verified = 0
    for index_path in sorted((root / "indices").glob("*index*.json")):
        payload = json.loads(index_path.read_text(encoding="utf-8"))
        for row in payload.get("runs", []):
            run = local_path(root, row["run_dir"])
            for field, name in (
                ("partition_sha256", "partition_indices.json"),
                ("provenance_sha256", "provenance.json"),
                ("final_metrics_sha256", "final_metrics.json"),
            ):
                if row.get(field):
                    path = run / name
                    if not path.is_file() or digest(path) != row[field]:
                        errors.append(f"Index hash mismatch or missing: {path}")
                    else:
                        verified += 1
            config_path = run / "resolved_config.yaml"
            if not config_path.is_file():
                errors.append(f"Missing configuration: {run}")
                continue
            config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            canonical = json.dumps(config, sort_keys=True, separators=(",", ":"), default=str)
            config_hash = hashlib.sha256(canonical.encode()).hexdigest()
            provenance = json.loads((run / "provenance.json").read_text(encoding="utf-8"))
            if config_hash != provenance["config_sha256"]:
                errors.append(f"Canonical configuration hash mismatch: {run}")
            expected_hash = (config_hash if "clean_development_index" in index_path.name
                             else digest(config_path))
            if row.get("config_sha256") != expected_hash:
                errors.append(f"Index configuration hash mismatch: {run}")
    for calibration_path in sorted((root / "indices").glob("calibration*.json")):
        payload = json.loads(calibration_path.read_text(encoding="utf-8"))
        for remote, expected_hash in payload["source_sha256"].items():
            path = local_path(root, remote)
            if not path.is_file() or digest(path) != expected_hash:
                errors.append(f"Calibration source hash mismatch or missing: {path}")
            else:
                verified += 1
    rows = []
    for clone, expected_count in EXPECTED_CLONES.items():
        paths = sorted((root / "raw" / clone).rglob("final_metrics.json"))
        if len(paths) != expected_count:
            errors.append(f"{clone}: expected {expected_count} runs, found {len(paths)}")
        for path in paths:
            final = json.loads(path.read_text(encoding="utf-8"))
            config = yaml.safe_load((path.parent / "resolved_config.yaml").read_text(encoding="utf-8"))
            provenance = json.loads((path.parent / "provenance.json").read_text(encoding="utf-8"))
            with (path.parent / "metrics_per_round.csv").open(newline="", encoding="utf-8") as stream:
                rounds = list(csv.DictReader(stream))
            if (int(final["final_round"]) != 40 or len(rounds) != 40 or
                    [int(row["round"]) for row in rounds] != list(range(1, 41))):
                errors.append(f"Round sequence incomplete: {path.parent}")
            if provenance.get("git_worktree_dirty") is not False:
                errors.append(f"Dirty source attestation: {path.parent}")
            for metric in ("clean_accuracy", "macro_f1"):
                value = float(final[metric])
                if not math.isfinite(value) or not 0 <= value <= 1:
                    errors.append(f"Invalid {metric}: {path.parent}")
            dataset = config["data"]["dataset"]
            attack = config["attack"]["name"]
            if attack == "none":
                label = "complete_clean_development_only"
            elif clone == "project_t2_attack_dev":
                label = "partial_two_of_nine_development_panel"
            elif dataset == "cifar10":
                label = "rejected_attack_validity_panel_do_not_use_for_claims"
            else:
                label = "complete_fedavg_attack_development_only"
            rows.append({
                "clone": clone, "dataset": dataset,
                "method": config["aggregation"]["method"], "attack": attack,
                "seed": int(config["experiment"]["seed"]),
                "clip_multiplier": config["tierguard2"]["clip_reference_multiplier"],
                "clean_accuracy": final["clean_accuracy"],
                "macro_f1": final["macro_f1"],
                "attack_success_rate": final.get("attack_success_rate"),
                "stability_failures": int(final["stability_failures"]),
                "evidence_status": label, "confirmatory": False,
                "source_commit": provenance["git_commit"],
                "run_directory": path.parent.relative_to(root).as_posix(),
            })
    return {"snapshot_integrity_passed": not errors, "errors": errors,
            "run_count": len(rows), "verified_index_or_calibration_hashes": verified,
            "confirmatory_runs": 0, "submission_ready": False, "runs": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--zip", type=Path, required=True)
    args = parser.parse_args()
    root = args.evidence_root.resolve()
    if args.zip.exists():
        raise FileExistsError(args.zip)
    result = validate(root)
    if result["errors"]:
        print(json.dumps({key: value for key, value in result.items() if key != "runs"}, indent=2))
        raise SystemExit(1)
    analysis = root / "analysis"
    analysis.mkdir(exist_ok=True)
    with (analysis / "seed_level_development_results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(result["runs"][0]))
        writer.writeheader()
        writer.writerows(result["runs"])
    (analysis / "snapshot_validation.json").write_text(
        json.dumps({key: value for key, value in result.items() if key != "runs"}, indent=2) + "\n",
        encoding="utf-8")
    manifest_path = root / "SHA256SUMS.json"
    files = sorted(path for path in root.rglob("*") if path.is_file() and path != manifest_path)
    manifest_path.write_text(json.dumps({path.relative_to(root).as_posix(): digest(path)
                                         for path in files}, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")
    with zipfile.ZipFile(args.zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files + [manifest_path]:
            archive.write(path, path.relative_to(root).as_posix())
    with zipfile.ZipFile(args.zip) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP integrity check failed")
    print(json.dumps({"zip": str(args.zip), "zip_sha256": digest(args.zip),
                      "run_count": result["run_count"], "snapshot_integrity_passed": True,
                      "submission_ready": False}, indent=2))


if __name__ == "__main__":
    main()
