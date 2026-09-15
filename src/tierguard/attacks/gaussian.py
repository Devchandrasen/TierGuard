from __future__ import annotations

import torch


def gaussian_attack(reference_update: torch.Tensor, sigma: float = 1.0) -> torch.Tensor:
    return torch.randn_like(reference_update) * float(sigma)
