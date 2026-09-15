from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from tierguard.analysis.make_tables import final_rows


def generate_interpretation(summary: str | Path, out: str | Path) -> str:
    frame = pd.read_csv(summary) if Path(summary).exists() else pd.DataFrame()
    frame = final_rows(frame)
    lines = ["# Result Interpretation", ""]
    if frame.empty:
        lines.append("No result logs were found. Run experiments before drawing conclusions.")
    else:
        metric_cols = [
            col
            for col in [
                "clean_accuracy",
                "macro_f1",
                "attack_success_rate",
                "detection_f1",
                "runtime",
                "communication",
            ]
            if col in frame.columns
        ]
        mean_cols = [col for col in ["dataset", "attack", "method"] if col in frame.columns]
        if "method" in mean_cols and metric_cols:
            frame = frame.groupby(mean_cols, dropna=False, as_index=False)[metric_cols].mean()
        group_cols = [col for col in ["dataset", "attack"] if col in frame.columns]
        groups = frame.groupby(group_cols, dropna=False) if group_cols else [((), frame)]
        for key, group in groups:
            label = key if isinstance(key, tuple) else (key,)
            label_text = ", ".join(str(x) for x in label)
            lines.append(f"## {label_text}")
            if "clean_accuracy" in group.columns:
                best_acc = group.loc[group["clean_accuracy"].idxmax()]
                lines.append(f"- Best clean accuracy: {best_acc['method']} ({best_acc['clean_accuracy']:.4f}).")
            if "attack_success_rate" in group.columns:
                best_asr = group.loc[group["attack_success_rate"].idxmin()]
                lines.append(f"- Lowest ASR: {best_asr['method']} ({best_asr['attack_success_rate']:.4f}).")
            tierguard = group[group["method"] == "tierguard"]
            hfl = group[group["method"] == "hfl_fedavg"]
            if not tierguard.empty and not hfl.empty:
                tg = tierguard.iloc[0]
                hf = hfl.iloc[0]
                if "clean_accuracy" in group.columns:
                    lines.append(
                        f"- TierGuard clean-accuracy difference versus HFL-FedAvg: "
                        f"{tg['clean_accuracy'] - hf['clean_accuracy']:.4f}."
                    )
                if "attack_success_rate" in group.columns:
                    lines.append(
                        f"- TierGuard ASR difference versus HFL-FedAvg: "
                        f"{tg['attack_success_rate'] - hf['attack_success_rate']:.4f}."
                    )
            lines.append("")
        lines.extend(
            [
                "## Limitations",
                "- Conclusions above are limited to the result CSVs present when this file was generated.",
                "- Simulated secure robust aggregation should not be described as a full cryptographic SMPC implementation.",
                "- Reimplemented RoPPFL-like and SHIELD-like baselines are not the original authors' code.",
            ]
        )
    text = "\n".join(lines) + "\n"
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    generate_interpretation(args.summary, args.out)


if __name__ == "__main__":
    main()
