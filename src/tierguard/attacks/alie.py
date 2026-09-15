from __future__ import annotations

import torch


def alie_attack(honest_updates: list[torch.Tensor], z: float = 1.0) -> torch.Tensor:
    if not honest_updates:
        raise ValueError("ALIE requires honest update statistics")
    stacked = torch.stack([u.detach().cpu() for u in honest_updates])
    return stacked.mean(dim=0) + float(z) * stacked.std(dim=0, unbiased=False)
