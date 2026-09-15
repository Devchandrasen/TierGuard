from __future__ import annotations

import torch
from torch.nn import functional as F


def project_to_norm_ball(update: torch.Tensor, norm_bound: float) -> torch.Tensor:
    norm = torch.linalg.vector_norm(update)
    if norm <= norm_bound:
        return update
    return update * (float(norm_bound) / max(1e-12, float(norm)))


def adaptive_tierguard_update(
    backdoor_update: torch.Tensor,
    root_direction: torch.Tensor,
    norm_bound: float,
    beta_grid: tuple[float, ...] = (0.1, 0.25, 0.5, 0.75),
    min_cosine: float = 0.0,
) -> torch.Tensor:
    root = root_direction.detach().cpu()
    root_norm = torch.linalg.vector_norm(root)
    if root_norm <= 1e-12:
        return project_to_norm_ball(backdoor_update.detach().cpu(), norm_bound)
    root_unit = root / root_norm
    bd = project_to_norm_ball(backdoor_update.detach().cpu(), norm_bound)
    bd_norm = torch.linalg.vector_norm(bd)
    best = bd
    for beta in beta_grid:
        candidate = beta * bd + (1.0 - beta) * bd_norm * root_unit
        candidate = project_to_norm_ball(candidate, norm_bound)
        cosine = F.cosine_similarity(candidate.view(1, -1), root.view(1, -1)).item()
        if cosine >= min_cosine:
            best = candidate
    return best
