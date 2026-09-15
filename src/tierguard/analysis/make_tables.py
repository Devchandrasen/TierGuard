from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from tierguard.analysis.latex_export import write_latex_table


RELATED_WORK_ROWS = [
    ["FedAvg", "No", "No", "No", "No", "No", "No", "No", "No", "No", "Limited"],
    ["Bonawitz Secure Aggregation", "No", "Yes", "No", "No", "No", "No", "No", "Limited", "No", "Yes"],
    ["Krum", "No", "No", "No", "Yes", "Limited", "No", "No", "No", "No", "Limited"],
    ["Median / Trimmed Mean", "No", "No", "No", "Yes", "Limited", "No", "No", "No", "No", "Limited"],
    ["RFA", "No", "No", "No", "Yes", "Limited", "No", "No", "No", "No", "Limited"],
    ["FoolsGold", "No", "No", "No", "Sybil", "Limited", "Yes", "No", "No", "No", "Limited"],
    ["FLTrust", "No", "No", "No", "Yes", "Limited", "Reference", "No", "No", "No", "Limited"],
    ["RoPPFL", "Yes", "Partial", "No", "Yes", "Limited", "Similarity", "Yes", "No", "Yes", "Yes"],
    ["SHIELD", "Yes", "Yes", "Limited", "Yes", "Yes", "Yes", "No", "Limited", "Yes", "Yes"],
    ["TAPFed", "Yes", "Yes", "Yes", "No", "No", "No", "No", "Yes", "Yes", "Yes"],
    ["TierGuard", "Yes", "Simulated", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes"],
]


def final_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    if "round" in frame.columns and "run_dir" in frame.columns:
        return frame.sort_values("round").groupby("run_dir", as_index=False).tail(1)
    return frame


def metric_table(frame: pd.DataFrame, dataset: str | None = None) -> pd.DataFrame:
    frame = final_rows(frame)
    if dataset and "dataset" in frame.columns:
        frame = frame[frame["dataset"].astype(str).str.lower() == dataset.lower()]
    cols = [
        "method",
        "clean_accuracy",
        "macro_f1",
        "attack_success_rate",
        "detection_f1",
        "runtime",
        "communication",
    ]
    if frame.empty:
        return pd.DataFrame(columns=["Method", "Clean Acc", "Macro-F1", "ASR", "Detection-F1", "Runtime", "Comm"])
    available = [col for col in cols if col in frame.columns]
    table = frame.groupby("method", dropna=False)[available[1:]].agg(["mean", "std"])
    rows = []
    for method, values in table.iterrows():
        row = {"Method": method}
        for metric in available[1:]:
            mean = values[(metric, "mean")]
            std = values[(metric, "std")]
            row[metric] = f"{mean:.4f} +/- {0.0 if pd.isna(std) else std:.4f}"
        rows.append(row)
    return pd.DataFrame(rows)


def overhead_table(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "num_clients",
                "num_edges",
                "model_dimension",
                "quantization_bits",
                "total_comm_mb",
                "tolerated_collusion",
                "tolerated_dropout",
                "reconstruction_success",
            ]
        )
    cols = [
        col
        for col in [
            "num_clients",
            "num_edges",
            "model_dimension",
            "quantization_bits",
            "total_comm_mb",
            "tolerated_collusion",
            "tolerated_dropout",
            "reconstruction_success",
        ]
        if col in frame.columns
    ]
    return frame[cols].copy()


def make_tables(summary: str | Path, stats: str | Path | None, out: str | Path) -> None:
    out_dir = Path(out)
    summary_path = Path(summary)
    frame = pd.read_csv(summary_path) if summary_path.exists() else pd.DataFrame()
    overhead_path = summary_path.parent / "overhead_summary.csv"
    overhead_frame = pd.read_csv(overhead_path) if overhead_path.exists() else pd.DataFrame()
    related = pd.DataFrame(
        RELATED_WORK_ROWS,
        columns=[
            "Method",
            "Hierarchical FL",
            "Secure aggregation",
            "Threshold security",
            "Poisoning robustness",
            "Backdoor robustness",
            "Adaptive defense",
            "Privacy accounting",
            "Collusion analysis",
            "Edge-cloud composition",
            "Overhead evaluation",
        ],
    )
    write_latex_table(related, out_dir / "table_related_work.tex", "Related work comparison.", "tab:related-work")
    write_latex_table(metric_table(frame, "mnist"), out_dir / "table_main_mnist.tex", "MNIST main results.", "tab:main-mnist")
    write_latex_table(metric_table(frame, "fashionmnist"), out_dir / "table_main_fashionmnist.tex", "FashionMNIST main results.", "tab:main-fashionmnist")
    write_latex_table(metric_table(frame, "digits"), out_dir / "table_main_digits.tex", "Digits main results.", "tab:main-digits")
    write_latex_table(metric_table(frame, "kmnist"), out_dir / "table_main_kmnist.tex", "KMNIST main results.", "tab:main-kmnist")
    write_latex_table(metric_table(frame, "cifar10"), out_dir / "table_main_cifar10.tex", "CIFAR-10 main results.", "tab:main-cifar10")
    write_latex_table(metric_table(frame, "ids"), out_dir / "table_main_ids.tex", "IDS main results.", "tab:main-ids")
    write_latex_table(metric_table(frame), out_dir / "table_attacker_fraction.tex", "Attacker-fraction results.", "tab:attacker-fraction")
    write_latex_table(metric_table(frame), out_dir / "table_privacy.tex", "Privacy-utility results.", "tab:privacy")
    write_latex_table(overhead_table(overhead_frame), out_dir / "table_overhead.tex", "Overhead results.", "tab:overhead")
    write_latex_table(overhead_table(overhead_frame), out_dir / "table_collusion.tex", "Collusion and dropout tolerance.", "tab:collusion")
    write_latex_table(metric_table(frame), out_dir / "table_ablation.tex", "TierGuard ablation results.", "tab:ablation")
    if stats and Path(stats).exists():
        stats_frame = pd.read_csv(stats)
    else:
        stats_frame = pd.DataFrame()
    write_latex_table(stats_frame, out_dir / "table_statistical_tests.tex", "Statistical tests.", "tab:stats")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True)
    parser.add_argument("--stats", default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    make_tables(args.summary, args.stats, args.out)


if __name__ == "__main__":
    main()
