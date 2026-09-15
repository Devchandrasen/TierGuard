from __future__ import annotations

import torch


def model_replacement(update: torch.Tensor, scale_factor: float) -> torch.Tensor:
    return update * float(scale_factor)
