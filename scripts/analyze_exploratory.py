"""Rebuild and verify the exploratory result tables from archived final-run metrics."""

from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from analyze_confirmatory import _holm_adjust, _t_ci
from verify_exploratory_runs import (
    CONDITION,
    METRICS,
    PRIMARY_RECORDS,
    RECORDS,
    SEEDS,
    TARGETED,
    load_runs,
)


SIGN_ASSIGNMENTS = np.array(list(product((-1.0, 1.0), repeat=len(SEEDS))))


def outcomes(attack: str) -> tuple[str, ...]:
    return METRICS if attack in TARGETED else METRICS[:2]


def paired(left: pd.DataFrame, right: pd.DataFrame, metric: str) -> dict:
    # Explicit seed alignment also preserves the published columns of individual deltas.
    left_values = left.set_index("seed").loc[list(SEEDS), metric].to_numpy()
    right_values = right.set_index("seed").loc[list(SEEDS), metric].to_numpy()
    diff = left_values - right_values
    mean = float(diff.mean())
    sd = float(diff.std(ddof=1))
    low, high = _t_ci(diff)
    sign_flip_means = (SIGN_ASSIGNMENTS * diff).mean(axis=1)
    return {
        "n": len(diff),
        "mean_difference": mean,
        "ci_low": low,
        "ci_high": high,
        "p_exact": float((np.abs(sign_flip_means) >= abs(mean) - 1e-14).mean()),
        "dz": mean / sd if sd > 1e-14 else np.nan,
        **{f"difference_pp_seed_{seed}": 100 * value for seed, value in zip(SEEDS, diff, strict=True)},
    }


def add_adjusted_columns(rows: list[dict], family: list[str]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    frame["p_holm"] = frame.groupby(family)["p_exact"].transform(_holm_adjust)
    for column in ("mean_difference", "ci_low", "ci_high"):
        frame[f"{column}_pp"] = 100 * frame[column]
    return frame


def rebuild(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    descriptions = []
    for keys, group in frame.groupby(CONDITION):
        for metric in outcomes(keys[1]):
            sample = group[metric]
            descriptions.append({
                **dict(zip(CONDITION, keys, strict=True)),
                "metric": metric, "n": len(sample), "mean": sample.mean(),
                "sd": sample.std(ddof=1), "minimum": sample.min(), "maximum": sample.max(),
            })

    standard = frame[frame["root_case"].eq("standard")]
    method_rows = []
    for (dataset, attack), group in standard.groupby(["dataset", "attack"]):
        pta = group[group["method"].eq("tierguard")]
        for method, baseline in group[~group["method"].eq("tierguard")].groupby("method"):
            for metric in outcomes(attack):
                method_rows.append({
                    "dataset": dataset, "attack": attack, "method": method, "metric": metric,
                    **paired(pta, baseline, metric),
                })

    root_rows = []
    perturbations = frame[frame["panel"].eq("root")]
    for (attack, method, case), group in perturbations.groupby(["attack", "method", "root_case"]):
        baseline = standard[standard["dataset"].eq("digits") & standard["method"].eq(method)
                            & standard["attack"].eq(attack)]
        for metric in METRICS:
            root_rows.append({
                "attack": attack, "method": method, "root_case": case, "metric": metric,
                **paired(group, baseline, metric),
            })

    return {
        "descriptive_metrics.csv": pd.DataFrame(descriptions),
        "method_and_untargeted_pairs.csv": add_adjusted_columns(
            method_rows, ["dataset", "attack", "metric"]
        ),
        "digits_root_pairs.csv": add_adjusted_columns(root_rows, ["attack", "method", "metric"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=RECORDS)
    parser.add_argument("--primary", type=Path, default=PRIMARY_RECORDS)
    parser.add_argument("--output", type=Path, help="Optional directory for regenerated CSVs")
    args = parser.parse_args()
    if args.output is not None and args.output.resolve() == args.records.resolve():
        parser.error("Choose an output directory separate from the published records")
    frame = load_runs(args.records, args.primary)
    tables = rebuild(frame)
    for name, calculated in tables.items():
        published = pd.read_csv(args.records / name)
        keys = [key for key in [*CONDITION, "metric"] if key in calculated]
        assert_frame_equal(
            calculated.sort_values(keys, ignore_index=True),
            published.sort_values(keys, ignore_index=True),
            check_exact=False, rtol=1e-9, atol=1e-11,
        )
        print(f"Verified {len(calculated)} rows in {name}.")
    if args.output is not None:
        args.output.mkdir(parents=True, exist_ok=True)
        for name, calculated in tables.items():
            calculated.to_csv(args.output / name, index=False)


if __name__ == "__main__":
    main()
