from __future__ import annotations

import torch
from torch.nn import functional as F

from tierguard.aggregators.base import coordinate_trimmed_mean, weighted_mean


class SecureStatsOracle:
    """Low-leakage secure aggregation simulator.

    Nonlinear operations are plaintext simulations for model-quality experiments and
    should be reported as simulated secure robust aggregation with separate overhead.
    """

    def secure_sum(self, updates: list[torch.Tensor]) -> torch.Tensor:
        return torch.stack([u.detach().cpu().float() for u in updates]).sum(dim=0)

    def secure_weighted_sum(self, updates: list[torch.Tensor], weights) -> torch.Tensor:
        return weighted_mean(updates, weights)

    def secure_norms(self, updates: list[torch.Tensor]) -> torch.Tensor:
        return torch.tensor([torch.linalg.vector_norm(u.detach().cpu().float()).item() for u in updates])

    def secure_cosine_scores(self, updates: list[torch.Tensor], reference: torch.Tensor) -> torch.Tensor:
        stacked = torch.stack([u.detach().cpu().float() for u in updates])
        return F.cosine_similarity(stacked, reference.detach().cpu().float().view(1, -1), dim=1)

    def secure_sign_agreement(
        self, updates: list[torch.Tensor], reference: torch.Tensor, sampled_indices: torch.Tensor
    ) -> torch.Tensor:
        ref = torch.sign(reference.detach().cpu().float()[sampled_indices])
        values = []
        for update in updates:
            values.append((torch.sign(update.detach().cpu().float()[sampled_indices]) == ref).float().mean())
        return torch.stack(values)

    def secure_trimmed_mean_sim(self, updates: list[torch.Tensor], beta: float) -> torch.Tensor:
        return coordinate_trimmed_mean(updates, beta=beta)
