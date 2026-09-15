from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def aggregate_results(
    results_dir: str | Path,
    out: str | Path,
    experiment_name: str | None = None,
) -> pd.DataFrame:
    root = Path(results_dir)
    rows = []
    for metrics_path in root.rglob("metrics_per_round.csv"):
        frame = pd.read_csv(metrics_path)
        frame["run_dir"] = str(metrics_path.parent)
        final_path = metrics_path.parent / "final_metrics.json"
        if final_path.exists():
            final = json.loads(final_path.read_text(encoding="utf-8"))
            for key, value in final.items():
                if key not in frame.columns:
                    frame[key] = value
        rows.append(frame)
    if rows:
        summary = pd.concat(rows, ignore_index=True)
    else:
        final_rows = []
        for final_path in root.rglob("final_metrics.json"):
            final = json.loads(final_path.read_text(encoding="utf-8"))
            final_rows.append(final)
        summary = pd.DataFrame(final_rows)
    if experiment_name and "experiment_name" in summary.columns:
        summary = summary[summary["experiment_name"] == experiment_name].copy()
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out, index=False)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results_dir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--experiment_name")
    args = parser.parse_args()
    aggregate_results(args.results_dir, args.out, experiment_name=args.experiment_name)


if __name__ == "__main__":
    main()
