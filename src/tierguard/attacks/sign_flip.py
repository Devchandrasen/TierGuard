from __future__ import annotations

import torch


def sign_flip(update: torch.Tensor, scale: float = 1.0) -> torch.Tensor:
    return -float(scale) * update
