from __future__ import annotations

import torch


def add_gaussian_noise(update: torch.Tensor, clipping_norm: float, noise_multiplier: float) -> torch.Tensor:
    if noise_multiplier <= 0:
        return update
    return update + torch.randn_like(update) * float(noise_multiplier) * float(clipping_norm)
