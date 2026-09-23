"""Freeze a clean-run gain threshold before confirmatory experiments.

Usage: python -m scripts.calibrate_tierguard2 RUN_DIR RUN_DIR RUN_DIR --output FILE
The three inputs must be clean development runs from distinct seeds of one
dataset, with calibrated_gain_threshold=1 so the provisional risk is zero.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml


def calibrate(run_dirs: list[Path], quantile: float = 0.95) -> dict:
    if len(run_dirs) != 3 or not 0 < quantile < 1:
        raise ValueError("Exactly three clean development runs and a valid quantile are required")
    seeds = set()
    datasets = set()
    source_hashes = {}
    gains = []
    for run_dir in run_dirs:
        config_path = run_dir / "resolved_config.yaml"
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if config["aggregation"]["method"] != "tierguard2" or config["attack"]["name"] != "none":
            raise ValueError(f"Not a clean TierGuard 2 run: {run_dir}")
        if float(config["tierguard2"]["calibrated_gain_threshold"]) != 1.0:
            raise ValueError("Development runs must use provisional threshold 1.0")
        seeds.add(int(config["experiment"]["seed"]))
        datasets.add(config["data"]["dataset"])
        records = sorted(run_dir.glob("audit_round_*.json"))
        if len(records) != int(config["experiment"]["rounds"]):
            raise ValueError(f"Incomplete audit record sequence: {run_dir}")
        for path in records:
            payload = path.read_bytes()
            source_hashes[str(path)] = hashlib.sha256(payload).hexdigest()
            record = json.loads(payload)
            for level in ("client_audits", "edge_audits"):
                gains.extend(float(item["heldout_target_gain"]) for item in record[level])
    if len(seeds) != 3 or len(datasets) != 1 or not gains:
        raise ValueError("Runs must have three distinct seeds, one dataset and nonempty audit data")
    return {
        "dataset": next(iter(datasets)),
        "development_seeds": sorted(seeds),
        "quantile": quantile,
        "calibrated_gain_threshold": max(0.0, float(np.quantile(gains, quantile))),
        "number_of_scores": len(gains),
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
