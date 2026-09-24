"""Constrained compromised-edge report transformations for simulations.

This function receives neither the cloud challenge key nor its path. It does
not model arbitrary code execution in the cloud's process.
"""

from __future__ import annotations

from dataclasses import replace

from tierguard.security.edge_receipts import EdgeReport, commit_edge


def alter_edge_reports(
    reports: list[EdgeReport], edge_attack: dict, *, round_idx: int
) -> list[EdgeReport]:
    name = edge_attack.get("name", "none")
    if name in (None, "none"):
        return reports
    compromised = int(edge_attack["edge_id"])
    altered = list(reports)
    for index, report in enumerate(altered):
        if report.edge_id != compromised:
            continue
        if name == "aggregate_replacement":
            forged = -float(edge_attack.get("scale", 2.0)) * report.aggregate
            altered[index] = commit_edge(round_idx, compromised, forged, list(report.receipts))
        elif name == "report_forgery":
            receipt = replace(report.receipts[0],
                              sample_mass=report.receipts[0].sample_mass + 1)
            altered[index] = commit_edge(
                round_idx, compromised, report.aggregate,
                [receipt, *report.receipts[1:]],
            )
        elif name == "missing_report":
            altered.pop(index)
        elif name == "replay_report":
            altered[index] = commit_edge(
                round_idx - 1, compromised, report.aggregate, list(report.receipts)
            )
        else:
            raise ValueError("Unknown edge attack")
        return altered
    return altered
