from __future__ import annotations

import torch


def make_sybil_updates(update: torch.Tensor, count: int, jitter: float = 1e-4) -> list[torch.Tensor]:
    return [update + jitter * torch.randn_like(update) for _ in range(count)]
