from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_latex_table(frame: pd.DataFrame, path: str | Path, caption: str = "", label: str = "") -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = frame.to_latex(index=False, escape=True, caption=caption or None, label=label or None)
    text = text.replace("\\begin{table}", "\\begin{table*}[t]")
    text = text.replace("\\end{table}", "\\end{table*}")
    text = text.replace("\\begin{tabular}", "\\centering\n\\scriptsize\n\\resizebox{\\textwidth}{!}{%\n\\begin{tabular}")
    text = text.replace("\\end{tabular}", "\\end{tabular}%\n}")
    path.write_text(text, encoding="utf-8")
