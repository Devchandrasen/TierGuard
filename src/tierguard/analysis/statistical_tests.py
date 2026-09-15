from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


def final_rounds(summary: pd.DataFrame) -> pd.DataFrame:
    if "round" not in summary.columns:
        return summary.copy()
    keys = [col for col in ["run_dir"] if col in summary.columns]
    if keys:
        return summary.sort_values("round").groupby(keys, as_index=False).tail(1)
    group_cols = [
        col
        for col in ["dataset", "method", "attack", "dirichlet_alpha", "malicious_fraction", "seed"]
        if col in summary.columns
    ]
    return summary.sort_values("round").groupby(group_cols, as_index=False).tail(1)


def bootstrap_ci(values: np.ndarray, confidence: float = 0.95, reps: int = 1000) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return (np.nan, np.nan)
    rng = np.random.default_rng(123)
    means = [rng.choice(values, size=len(values), replace=True).mean() for _ in range(reps)]
    low = np.quantile(means, (1 - confidence) / 2)
    high = np.quantile(means, 1 - (1 - confidence) / 2)
    return float(low), float(high)


def paired_test(tierguard: np.ndarray, baseline: np.ndarray) -> tuple[float, float, str]:
    if len(tierguard) < 2 or len(tierguard) != len(baseline):
        return np.nan, np.nan, "insufficient"
    diff = tierguard - baseline
    normal_p = stats.shapiro(diff).pvalue if len(diff) >= 3 else 1.0
    if normal_p > 0.05:
        p_value = stats.ttest_rel(tierguard, baseline).pvalue
        test_name = "paired_t"
    else:
        try:
            p_value = stats.wilcoxon(tierguard, baseline).pvalue
        except ValueError:
            p_value = 1.0
        test_name = "wilcoxon"
    effect = diff.mean() / (diff.std(ddof=1) + 1e-12)
    return float(p_value), float(effect), test_name


def run_statistical_tests(summary_path: str | Path, out: str | Path) -> pd.DataFrame:
    frame = final_rounds(pd.read_csv(summary_path))
    rows = []
    group_cols = [
        col
        for col in ["dataset", "attack", "malicious_fraction", "dirichlet_alpha"]
        if col in frame.columns
    ]
    metrics = ["clean_accuracy", "macro_f1", "attack_success_rate", "detection_f1", "runtime", "communication"]
    for group_key, group in frame.groupby(group_cols, dropna=False) if group_cols else [((), frame)]:
        group_dict = dict(zip(group_cols, group_key if isinstance(group_key, tuple) else (group_key,)))
        tierguard = group[group["method"] == "tierguard"]
        baselines = group[group["method"] != "tierguard"]
        for metric in metrics:
            if metric not in group.columns or tierguard.empty or baselines.empty:
                continue
            baseline_means = baselines.groupby("method")[metric].mean()
            if baseline_means.empty:
                continue
            higher_better = metric not in {"attack_success_rate", "runtime", "communication"}
            best_baseline = baseline_means.idxmax() if higher_better else baseline_means.idxmin()
            baseline = baselines[baselines["method"] == best_baseline]
            merged = tierguard[["seed", metric]].merge(
                baseline[["seed", metric]], on="seed", suffixes=("_tierguard", "_baseline")
            )
            p_value, effect, test_name = paired_test(
                merged[f"{metric}_tierguard"].to_numpy(),
                merged[f"{metric}_baseline"].to_numpy(),
            )
            low, high = bootstrap_ci(tierguard[metric].dropna().to_numpy())
            rows.append(
                {
                    **group_dict,
                    "metric": metric,
                    "tierguard_mean": tierguard[metric].mean(),
                    "tierguard_std": tierguard[metric].std(ddof=0),
                    "tierguard_ci_low": low,
                    "tierguard_ci_high": high,
                    "best_baseline": best_baseline,
                    "p_value": p_value,
                    "effect_size": effect,
                    "test": test_name,
                    "significant_p_lt_0_05": bool(p_value < 0.05) if np.isfinite(p_value) else False,
                }
            )
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    result = pd.DataFrame(rows)
    result.to_csv(out, index=False)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    run_statistical_tests(args.summary, args.out)


if __name__ == "__main__":
    main()
