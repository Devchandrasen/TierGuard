from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def _save(fig, out_dir: Path, name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_dir / f"{name}.pdf")
    fig.savefig(out_dir / f"{name}.png", dpi=200)
    plt.close(fig)


def _placeholder(out_dir: Path, name: str, title: str) -> None:
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.text(0.5, 0.5, "No logged data", ha="center", va="center")
    ax.set_title(title)
    ax.set_axis_off()
    _save(fig, out_dir, name)


def _line_plot(frame: pd.DataFrame, out_dir: Path, name: str, y: str, x: str = "round") -> None:
    if frame.empty or x not in frame.columns or y not in frame.columns:
        _placeholder(out_dir, name, name)
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    for method, group in frame.groupby("method"):
        grouped = group.groupby(x)[y].agg(["mean", "std"]).reset_index()
        ax.plot(grouped[x], grouped["mean"], label=str(method))
        if grouped["std"].notna().any():
            ax.fill_between(
                grouped[x],
                grouped["mean"] - grouped["std"].fillna(0),
                grouped["mean"] + grouped["std"].fillna(0),
                alpha=0.15,
            )
    ax.set_xlabel(x.replace("_", " ").title())
    ax.set_ylabel(y.replace("_", " ").title())
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    _save(fig, out_dir, name)


def _point_plot(frame: pd.DataFrame, out_dir: Path, name: str, x: str, y: str) -> None:
    if frame.empty or x not in frame.columns or y not in frame.columns:
        _placeholder(out_dir, name, name)
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    final = frame.sort_values("round").groupby("run_dir", as_index=False).tail(1) if "run_dir" in frame.columns and "round" in frame.columns else frame
    for method, group in final.groupby("method"):
        grouped = group.groupby(x)[y].agg(["mean", "std"]).reset_index()
        ax.errorbar(grouped[x], grouped["mean"], yerr=grouped["std"].fillna(0), marker="o", label=str(method))
    ax.set_xlabel(x.replace("_", " ").title())
    ax.set_ylabel(y.replace("_", " ").title())
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    _save(fig, out_dir, name)


def make_plots(summary: str | Path, out: str | Path) -> None:
    summary_path = Path(summary)
    frame = pd.read_csv(summary_path) if summary_path.exists() else pd.DataFrame()
    overhead_path = summary_path.parent / "overhead_summary.csv"
    overhead_frame = pd.read_csv(overhead_path) if overhead_path.exists() else frame
    out_dir = Path(out)
    _line_plot(frame, out_dir, "clean_accuracy_vs_rounds", "clean_accuracy")
    _line_plot(frame, out_dir, "asr_vs_rounds", "asr")
    _point_plot(frame, out_dir, "accuracy_vs_malicious_fraction", "malicious_fraction", "clean_accuracy")
    _point_plot(frame, out_dir, "asr_vs_malicious_fraction", "malicious_fraction", "attack_success_rate")
    _point_plot(frame, out_dir, "macro_f1_vs_alpha", "dirichlet_alpha", "macro_f1")
    _point_plot(frame, out_dir, "privacy_accuracy_vs_epsilon", "epsilon", "clean_accuracy")
    _point_plot(frame, out_dir, "privacy_asr_vs_epsilon", "epsilon", "attack_success_rate")
    _point_plot(overhead_frame, out_dir, "overhead_vs_clients", "num_clients", "communication")
    _point_plot(overhead_frame, out_dir, "overhead_vs_model_dimension", "model_dimension", "total_comm_mb")
    _point_plot(frame, out_dir, "ablation_accuracy", "method", "clean_accuracy")
    _point_plot(frame, out_dir, "ablation_asr", "method", "attack_success_rate")
    _point_plot(overhead_frame, out_dir, "collusion_threshold_success", "threshold", "reconstruction_success")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    make_plots(args.summary, args.out)


if __name__ == "__main__":
    main()
