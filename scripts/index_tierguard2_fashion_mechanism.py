"""Fail-closed, partial-panel validation of the bounded mechanism screen."""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fashion_mechanism_common import (VARIANTS, canonical_hash, cell_config,
                                      cell_results, cells, check_manifest, digest)

def require(condition, message):
    if not condition:
        raise ValueError(message)

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def finite(value, low=None, high=None):
    x = float(value)
    return math.isfinite(x) and (low is None or x >= low) and (high is None or x <= high)

def validate_run(folder, cell, manifest):
    expected = cell_config(cell)
    config = yaml.safe_load((folder / "resolved_config.yaml").read_text())
    require(config == expected, "resolved configuration differs from frozen cell")
    config_hash = canonical_hash(config)
    provenance, final = read(folder / "provenance.json"), read(folder / "final_metrics.json")
    require(provenance["git_commit"] == final["git_commit"] == manifest["source_commit"],
            "source commit mismatch")
    require(provenance["git_worktree_dirty"] is False, "dirty or unattested source")
    require(provenance["config_sha256"] == final["config_sha256"] == config_hash,
            "configuration attestation mismatch")
    require(provenance["environment_lock_sha256"] == manifest["environment_lock_sha256"],
            "environment lock mismatch")
    require(provenance["device"].startswith("cuda"), "GPU was not used")
    require(provenance["python"].split()[0] == manifest["python_version"], "Python version mismatch")
    require(provenance["torch_num_threads"] == 2, "worker thread count mismatch")
    require(all(provenance["packages"].get(name) == version
                for name, version in manifest["provenance_packages"].items()), "package version mismatch")
    require(digest(folder / "partition_indices.json") == manifest["partition_hashes"][str(cell["seed"])],
            "paired client/root/test partitions changed")
    for key, value in {"final_round": 40, "stability_failures": 0, "seed": cell["seed"],
                       "method": expected["aggregation"]["method"], "attack": cell["attack"],
                       "dataset": "fashionmnist", "experiment_name": "tierguard2_fashion_mechanism_v1"}.items():
        require(final[key] == value, f"final {key} mismatch")
    for key in ("clean_accuracy", "macro_f1"):
        require(finite(final[key], 0, 1), f"invalid final {key}")
    if cell["attack"] == "none":
        require(final["attack_success_rate"] is None, "ASR must be undefined without attack")
    else:
        require(finite(final["attack_success_rate"], 0, 1), "invalid final ASR")
    with (folder / "metrics_per_round.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    require([int(row["round"]) for row in rows] == list(range(1, 41)), "incomplete/duplicate rounds")
    for row in rows:
        require(int(row["stability_failures"]) == 0, "numerical-stability failure")
        for key, value in row.items():
            if key in {"experiment_name", "method", "dataset", "attack"}:
                require(value == str(final[key]), f"round identity mismatch: {key}")
            elif value == "":
                clean_asr = cell["attack"] == "none" and key in {"asr", "attack_success_rate"}
                pre_eval = int(row["round"]) < 5 and key in {
                    "clean_accuracy", "clean_loss", "macro_f1", "asr", "attack_success_rate"}
                require(clean_asr or pre_eval, f"unexpected empty metric: {key}")
            else:
                require(finite(value), f"non-finite metric: {key}")
    for csv_key, final_key in (("clean_accuracy", "clean_accuracy"), ("macro_f1", "macro_f1"),
                               ("asr", "attack_success_rate")):
        if final[final_key] is not None:
            require(math.isclose(float(rows[-1][csv_key]), final[final_key], abs_tol=1e-14),
                    f"CSV/final disagreement: {final_key}")
    expected_audits = [folder / f"audit_round_{n:03d}.json" for n in range(1, 41)]
    require(set(folder.glob("audit_round_*.json")) == set(expected_audits), "audit round mismatch")
    tg2 = expected["aggregation"]["method"] == "tierguard2"
    for path in expected_audits:
        audit = read(path)
        require(audit["expected_edge_reports"] == audit["received_edge_reports"] == 6,
                "edge report mismatch")
        require(len(set(audit["challenged_edges"])) == 3 and
                set(audit["challenged_edges"]) <= set(range(6)), "invalid challenges")
        require(not audit["rejected_edges"] and not audit["missing_edge_reports"],
                "unexpected receipt rejection or missing report")
        for field in ("client_edge_update_bytes", "client_cloud_receipt_bytes",
                      "edge_cloud_report_bytes", "challenge_raw_upload_bytes"):
            require(finite(audit[field], 1), f"invalid payload accounting: {field}")
        if tg2:
            require(len(audit["client_audits"]) == 30 and len(audit["edge_audits"]) == 6,
                    "counterfactual audit incomplete")
            require(len(audit["edge_minus_client_risk"]) == 6 and
                    all(finite(v, -1, 1) for v in audit["edge_minus_client_risk"]), "invalid separation")
            require(finite(audit["clip_radius"], 0.1), "invalid clipping radius")
            for level in ("client", "edge"):
                enabled = expected["tierguard2"][f"{level}_risk_weighting"]
                require(audit[f"{level}_risk_weighting"] is enabled, "ablation switch mismatch")
                observations = audit[f"{level}_audits"]
                risks = [entry["risk"] for entry in observations]
                require(audit[f"{level}_applied_risks"] == (risks if enabled else [0.0] * len(risks)),
                        "applied risks do not match the specified ablation")
                for observation in observations:
                    require(finite(observation["risk"], 0, 1) and
                            finite(observation["heldout_target_gain"], -1, 1) and
                            finite(observation["clean_loss_change"]), "invalid counterfactual score")
    assignment = read(folder / "attack_assignment.json")
    import random
    malicious = sorted(random.Random(cell["seed"] + 17).sample(range(60),
                       0 if cell["attack"] == "none" else 12))
    require(assignment["malicious_client_ids"] == malicious, "malicious-client pairing mismatch")
    if cell["attack"] == "distributed_backdoor":
        require(assignment["distributed_components"] == {
            str(client): index % 4 for index, client in enumerate(malicious)}, "component mismatch")
    trigger_files = sorted(folder.glob("attack_triggers_round_*.json"))
    if cell["attack"] == "defence_aware_optimized_trigger":
        # This fixed topology/seed grid has at least one attacker every round;
        # check that premise independently, before requiring 40 trigger files.
        import numpy as np
        selected_per_round = {}
        for round_idx in range(1, 41):
            selected = []
            for edge_id in range(6):
                rng = np.random.default_rng(cell["seed"] + round_idx * 9973 + edge_id * 104729)
                selected.extend(rng.choice(list(range(edge_id, 60, 6)), 5,
                                           replace=False).tolist())
            selected_per_round[round_idx] = set(selected) & set(malicious)
        require(all(selected_per_round.values()), "attack-free round in expected optimized panel")
        require(set(trigger_files) == {
            folder / f"attack_triggers_round_{n:03d}.json" for n in range(1, 41)},
            "optimized-trigger evidence incomplete")
        for path in trigger_files:
            triggers = read(path)
            require(bool(triggers), "empty optimized-trigger evidence")
            round_idx = int(path.stem.rsplit("_", 1)[1])
            require(set(map(int, triggers)) == selected_per_round[round_idx], "trigger owner mismatch")
            for patch in triggers.values():
                array = np.asarray(patch, dtype=float)
                require(array.shape == (1, 3, 3) and np.isfinite(array).all(), "invalid trigger pixels")
    hashes = {path.name: digest(path) for path in folder.iterdir() if path.is_file()}
    return {**cell, "run_dir": str(folder), "job_id": provenance["pbs_job_id"],
            "clean_accuracy": final["clean_accuracy"], "macro_f1": final["macro_f1"],
            "attack_success_rate": final["attack_success_rate"], "file_sha256": hashes}

def index_runs(results_root, manifest):
    check_manifest(manifest)
    runs, missing, errors, attempts = [], [], [], []
    expected_dirs = set()
    for cell in cells():
        path = cell_results(results_root, cell)
        folders = list(path.iterdir()) if path.exists() else []
        if not folders:
            missing.append(cell["id"])
            continue
        attempts.append(cell["id"])
        expected_dirs.update(folders)
        if len(folders) != 1 or not folders[0].is_dir():
            errors.append(f"duplicate or invalid attempt: {cell['id']}")
            continue
        try:
            runs.append(validate_run(folders[0], cell, manifest))
        except (ValueError, KeyError, OSError, TypeError) as exc:
            errors.append(f"{cell['id']}: {exc}")
    if results_root.exists():
        for path in results_root.rglob("*"):
            if path.is_file() and path.parent not in expected_dirs:
                errors.append(f"unexpected run: {path.parent}")
    return {"phase": "fashion_mechanism_v1", "complete": not errors and not missing,
            "valid_partial": not errors, "expected_run_count": len(cells()),
            "observed_run_count": len(runs), "attempted_cells": attempts,
            "missing_unattempted_cells": missing, "errors": errors, "runs": runs}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = index_runs(args.results_root, read(args.manifest))
    result["manifest_sha256"] = digest(args.manifest)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({key: result[key] for key in
                     ("complete", "valid_partial", "observed_run_count", "errors")}, indent=2))
    if not result["valid_partial"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
