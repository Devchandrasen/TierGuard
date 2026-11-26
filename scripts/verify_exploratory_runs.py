"""Validate recorded exploratory runs and the primary rows used as comparators."""

from __future__ import annotations

import argparse
from itertools import product
import json
from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal


ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "artifacts" / "exploratory_analysis"
PRIMARY_RECORDS = ROOT / "artifacts" / "confirmatory_v1" / "per_run_metrics.csv"
SEEDS = (101, 202, 303, 404, 505, 606)
DATASETS = ("digits", "fashionmnist", "mnist")
TARGETED = ("adaptive_tierguard_aware", "backdoor_model_replacement")
UNTARGETED = ("alie", "gaussian", "label_flip", "none", "sign_flip")
PRIMARY_METHODS = ("hfl_fedavg", "hfl_fltrust", "hfl_trimmed_mean", "hfl_rfa", "tierguard")
EXTRA_METHODS = ("hfl_median", "hfl_foolsgold", "tierguard_core")
ROOT_METHODS = ("hfl_fltrust", "tierguard", "tierguard_core")
ROOT_CASES = ("classes0to4", "inverted", "poison20", "small20", "small50")
METRICS = ("clean_accuracy", "macro_f1", "attack_success_rate")
CONDITION = ["dataset", "attack", "method", "root_case"]
RUN_KEY = [*CONDITION, "seed"]
EXPLORATORY_COMMIT = "3b91856860d0a0ebfbdc7e73fb22ae975595e5c1"


def validate_matrix(frame: pd.DataFrame) -> None:
    expected = {
        "primary": set(product(DATASETS, TARGETED, PRIMARY_METHODS, ["standard"], SEEDS)),
        "baselines": set(product(DATASETS, TARGETED, EXTRA_METHODS, ["standard"], SEEDS)),
        "attacks": set(product(["digits"], UNTARGETED, PRIMARY_METHODS + EXTRA_METHODS,
                               ["standard"], SEEDS)),
        "root": set(product(["digits"], TARGETED, ROOT_METHODS, ROOT_CASES, SEEDS)),
    }
    if frame.duplicated(RUN_KEY).any():
        raise ValueError("Duplicate recorded run")
    if set(frame["panel"]) != set(expected):
        raise ValueError("Incorrect panel names")
    for panel, expected_keys in expected.items():
        keys = set(frame.loc[frame["panel"].eq(panel), RUN_KEY].itertuples(index=False, name=None))
        if keys != expected_keys:
            raise ValueError(f"{panel}: {len(expected_keys - keys)} missing and "
                             f"{len(keys - expected_keys)} unexpected runs")


def load_runs(records: Path = RECORDS, primary_path: Path = PRIMARY_RECORDS) -> pd.DataFrame:
    frame = pd.read_csv(records / "final_run_metrics.csv")
    validate_matrix(frame)
    targeted = frame["attack"].isin(TARGETED)
    for metric in METRICS[:2]:
        if not frame[metric].between(0, 1).all():
            raise ValueError(f"Invalid {metric}")
    if (not frame.loc[targeted, "attack_success_rate"].between(0, 1).all()
            or not frame.loc[~targeted, "attack_success_rate"].isna().all()):
        raise ValueError("ASR must be valid for targeted runs and empty for other runs")

    expected_rounds = frame["dataset"].map({"digits": 20, "fashionmnist": 30, "mnist": 20})
    if not frame["final_round"].eq(expected_rounds).all():
        raise ValueError("Unexpected final round")
    settings = {"num_clients": 20, "num_edges": 5, "local_epochs": 2,
                "alpha": 0.5, "selected_clients_per_round": 10}
    for field, value in settings.items():
        if not frame[field].eq(value).all():
            raise ValueError(f"Unexpected {field}")
    expected_fraction = frame["attack"].ne("none").astype(float) * 0.2
    if not frame["malicious_fraction"].eq(expected_fraction).all():
        raise ValueError("Unexpected recorded attack intensity")

    primary = frame["panel"].eq("primary")
    provenance = json.loads((records / "provenance.json").read_text(encoding="utf-8"))
    counts = {"primary_runs": int(primary.sum()), "extension_runs": int((~primary).sum()),
              "total_runs": len(frame)}
    if any(provenance[field] != count for field, count in counts.items()):
        raise ValueError("Run counts do not match the provenance record")
    if not frame.loc[~primary, "git_commit"].eq(EXPLORATORY_COMMIT).all():
        raise ValueError("Unexpected recorded exploratory commit")
    for field in ("extension_source_sha256", "partition_sha256", "config_sha256"):
        if not frame.loc[~primary, field].str.fullmatch(r"[0-9a-f]{64}", na=False).all():
            raise ValueError(f"Missing or invalid recorded hash: {field}")
    if not frame.loc[~primary, "extension_source_sha256"].eq(
        provenance["extension_driver_sha256"]
    ).all():
        raise ValueError("Recorded exploratory source hashes disagree")

    primary_data = pd.read_csv(primary_path)
    key = ["dataset", "attack", "method", "seed"]
    columns = [*METRICS, "git_commit", "config_sha256"]
    assert_frame_equal(
        frame.loc[primary].set_index(key)[columns].sort_index(),
        primary_data.set_index(key)[columns].sort_index(),
        check_exact=False, rtol=1e-10, atol=1e-12,
    )
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=RECORDS)
    parser.add_argument("--primary", type=Path, default=PRIMARY_RECORDS)
    args = parser.parse_args()
    frame = load_runs(args.records, args.primary)
    print(f"Verified {len(frame)} recorded runs and their primary comparator rows.")


if __name__ == "__main__":
    main()
