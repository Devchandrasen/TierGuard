from __future__ import annotations

import torch


def clip_update(update: torch.Tensor, clipping_norm: float) -> torch.Tensor:
    norm = torch.linalg.vector_norm(update)
    if norm <= clipping_norm:
        return update
    return update * (float(clipping_norm) / max(1e-12, float(norm)))
