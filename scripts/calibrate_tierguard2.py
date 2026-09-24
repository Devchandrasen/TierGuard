"""Freeze a clean-run gain threshold before confirmatory experiments.

Usage: python -m scripts.calibrate_tierguard2 RUN_DIR RUN_DIR RUN_DIR --output FILE
The three inputs must be clean development runs from distinct seeds of one
dataset, with calibrated_gain_threshold=1 so the provisional risk is zero.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import yaml


def calibrate(run_dirs: list[Path], quantile: float = 0.95) -> dict:
    if len(run_dirs) != 3 or not 0 < quantile < 1:
        raise ValueError("Exactly three clean development runs and a valid quantile are required")
    seeds = set()
    datasets = set()
    configurations = set()
    commits = set()
    source_hashes = {}
    gains = []
    gains_by_level: dict[str, list[float]] = {"client": [], "edge": []}
    for run_dir in run_dirs:
        config_path = run_dir / "resolved_config.yaml"
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if config["aggregation"]["method"] != "tierguard2" or config["attack"]["name"] != "none":
            raise ValueError(f"Not a clean TierGuard 2 run: {run_dir}")
        if config["experiment"]["name"] != "tierguard2_clean_development_source_attested":
            raise ValueError(f"Not an attested development run: {run_dir}")
        if float(config["tierguard2"]["calibrated_gain_threshold"]) != 1.0:
            raise ValueError("Development runs must use provisional threshold 1.0")
        if int(config["experiment"]["rounds"]) != 40:
            raise ValueError("Clean calibration requires all 40 development rounds")
        provenance = json.loads((run_dir / "provenance.json").read_text(encoding="utf-8"))
        if provenance.get("git_worktree_dirty") is not False:
            raise ValueError(f"Calibration run has dirty or unknown source: {run_dir}")
        commits.add(str(provenance["git_commit"]))
        comparable = copy.deepcopy(config)
        comparable["experiment"].pop("seed", None)
        configurations.add(json.dumps(comparable, sort_keys=True, default=str))
        seeds.add(int(config["experiment"]["seed"]))
        datasets.add(config["data"]["dataset"])
        final = json.loads((run_dir / "final_metrics.json").read_text(encoding="utf-8"))
        if int(final["final_round"]) != 40:
            raise ValueError(f"Incomplete final result: {run_dir}")
        records = sorted(run_dir.glob("audit_round_*.json"))
        if len(records) != int(config["experiment"]["rounds"]):
            raise ValueError(f"Incomplete audit record sequence: {run_dir}")
        for path in records:
            payload = path.read_bytes()
            source_hashes[str(path)] = hashlib.sha256(payload).hexdigest()
            record = json.loads(payload)
            for level, field in (("client", "client_audits"), ("edge", "edge_audits")):
                values = [float(item["heldout_target_gain"]) for item in record[field]]
                if any(not math.isfinite(value) or not -1 <= value <= 1 for value in values):
                    raise ValueError(f"Invalid {level} held-out gain in {path}")
                gains_by_level[level].extend(values)
                gains.extend(values)
    if (seeds != {2001, 2002, 2003} or len(datasets) != 1 or
            len(configurations) != 1 or len(commits) != 1 or
            any(not values for values in gains_by_level.values())):
        raise ValueError("Calibration requires seeds 2001-2003, one dataset, "
                         "one source commit, one configuration and nonempty audit data")
    return {
        "dataset": next(iter(datasets)),
        "development_seeds": sorted(seeds),
        "quantile": quantile,
        "calibrated_gain_threshold": max(0.0, float(np.quantile(gains, quantile))),
        "calibrated_client_gain_threshold": max(
            0.0, float(np.quantile(gains_by_level["client"], quantile))
        ),
        "calibrated_edge_gain_threshold": max(
            0.0, float(np.quantile(gains_by_level["edge"], quantile))
        ),
        "number_of_scores": len(gains),
        "number_of_client_scores": len(gains_by_level["client"]),
        "number_of_edge_scores": len(gains_by_level["edge"]),
        "git_commit": next(iter(commits)),
        "calibration_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "configuration_sha256": hashlib.sha256(
            next(iter(configurations)).encode("utf-8")
        ).hexdigest(),
        "source_sha256": source_hashes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dirs", nargs=3, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = calibrate(args.run_dirs)
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
