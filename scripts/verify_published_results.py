"""Recalculate paired and descriptive results from the published final-run CSV."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from analyze_confirmatory import (
    _descriptive,
    _expected_keys,
    _load_matrix,
    _paired_comparisons,
    _sha256,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORDS = ROOT / "artifacts" / "confirmatory_v1"
PROTOCOL = ROOT / "configs" / "confirmatory_v1"
RUN_KEY = ["dataset", "method", "attack", "seed"]
EXPERIMENT_COMMIT = "88a02253ff67d0d336dc4dc041c8620b5b851533"


def verify(records: Path):
    matrix = _load_matrix(PROTOCOL / "matrix.yaml")
    metrics = [metric["name"] for metric in matrix["analysis"]["metrics"]]
    frame = pd.read_csv(records / "per_run_metrics.csv")
    expected = _expected_keys(matrix)
    actual = set(frame[RUN_KEY].itertuples(index=False, name=None))
    if actual != expected or len(frame) != len(expected):
        raise ValueError("Missing, extra, or duplicate experimental cells")
    if set(frame["git_commit"]) != {EXPERIMENT_COMMIT}:
        raise ValueError("Unexpected experiment commit")
    if set(frame["protocol_id"]) != {matrix["protocol_id"]}:
        raise ValueError("Unexpected protocol identifier")
    if set(frame["protocol_manifest_sha256"]) != {_sha256(PROTOCOL / "FROZEN_SHA256SUMS")}:
        raise ValueError("Unexpected protocol manifest hash")
    config = {"alpha": 0.5, "num_clients": 20, "num_edges": 5, "local_epochs": 2,
              "selected_clients_per_round": 10, "malicious_fraction": 0.2,
              "stability_failures": 0,
              "device": "cpu", "hierarchical_aggregation": True}
    for field, value in config.items():
        if not frame[field].eq(value).all():
            raise ValueError(f"Unexpected recorded setting: {field}")
    rounds_by_dataset = {
        item["name"]: _load_matrix(ROOT / item["config"])["experiment"]["rounds"]
        for item in matrix["datasets"]
    }
    expected_rounds = frame["dataset"].map(rounds_by_dataset)
    if not (frame["configured_rounds"].eq(expected_rounds) &
            frame["final_round"].eq(expected_rounds)).all():
        raise ValueError("Unexpected configured or final round count")
    outcomes = frame[metrics].to_numpy(dtype=float)
    if not np.isfinite(outcomes).all() or ((outcomes < 0) | (outcomes > 1)).any():
        raise ValueError("Invalid outcome values")

    descriptive = _descriptive(frame, metrics)
    paired = _paired_comparisons(frame, matrix)
    for name, computed in (("descriptive_summary", descriptive), ("paired_comparisons", paired)):
        published = pd.read_csv(records / f"{name}.csv")
        assert_frame_equal(computed, published, check_exact=False, rtol=1e-9, atol=1e-12)
    return frame, descriptive, paired


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=DEFAULT_RECORDS)
    args = parser.parse_args()
    frame, descriptive, paired = verify(args.records)
    print(f"Verified {len(frame)} runs, {len(descriptive)} descriptives, and {len(paired)} comparisons.")


if __name__ == "__main__":
    main()
