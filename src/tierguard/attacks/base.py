from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AttackContext:
    name: str
    malicious_fraction: float
    target_label: int = 0
    source_label: int | None = None
    scale: float = 1.0
