from __future__ import annotations


def collusion_summary(committee_size: int, threshold: int) -> dict[str, int]:
    return {
        "committee_size": int(committee_size),
        "threshold": int(threshold),
        "tolerated_collusion": int(threshold) - 1,
        "tolerated_dropout": int(committee_size) - int(threshold),
    }
