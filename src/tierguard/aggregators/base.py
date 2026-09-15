from __future__ import annotations

from dataclasses import dataclass, field

import torch


@dataclass
class AggregationResult:
    update: torch.Tensor
    weights: torch.Tensor | None = None
    suspicion: torch.Tensor | None = None
    reliability: float = 1.0
    anomaly_mass: float = 0.0
    metadata: dict = field(default_factory=dict)


class BaseAggregator:
    def __init__(self, config: dict | None = None, dimension: int | None = None):
        self.config = config or {}
        self.dimension = dimension

    def aggregate(
        self,
        updates: list[torch.Tensor],
        weights: list[float] | torch.Tensor | None = None,
        client_ids: list[int] | None = None,
        reference_update: torch.Tensor | None = None,
        **kwargs,
    ) -> AggregationResult:
        raise NotImplementedError


def stack_updates(updates: list[torch.Tensor]) -> torch.Tensor:
    if not updates:
        raise ValueError("Cannot aggregate an empty update list")
    return torch.stack([u.detach().cpu().float() for u in updates])


def normalize_weights(weights: list[float] | torch.Tensor | None, n: int) -> torch.Tensor:
    if weights is None:
        out = torch.ones(n, dtype=torch.float32)
    else:
        out = torch.as_tensor(weights, dtype=torch.float32).clone()
    total = out.sum()
    if total <= 1e-12:
        out = torch.ones(n, dtype=torch.float32)
        total = out.sum()
    return out / total


def weighted_mean(updates: list[torch.Tensor], weights: list[float] | torch.Tensor | None = None) -> torch.Tensor:
    stacked = stack_updates(updates)
    w = normalize_weights(weights, len(updates)).view(-1, 1)
    return (stacked * w).sum(dim=0)


def geometric_median(
    updates: list[torch.Tensor],
    weights: list[float] | torch.Tensor | None = None,
    max_iter: int = 10,
    eps: float = 1e-6,
) -> torch.Tensor:
    stacked = stack_updates(updates)
    sample_weights = normalize_weights(weights, len(updates))
    current = (stacked * sample_weights.view(-1, 1)).sum(dim=0)
    for _ in range(max_iter):
        distances = torch.linalg.vector_norm(stacked - current.view(1, -1), dim=1).clamp_min(eps)
        w = sample_weights / distances
        current = (stacked * (w / w.sum()).view(-1, 1)).sum(dim=0)
    return current


def coordinate_trimmed_mean(
    updates: list[torch.Tensor],
    beta: float = 0.2,
    weights: list[float] | torch.Tensor | None = None,
) -> torch.Tensor:
    stacked = stack_updates(updates)
    n = stacked.size(0)
    trim = int(beta * n)
    if trim <= 0 or 2 * trim >= n:
        return weighted_mean(updates, weights)
    sorted_values, _ = torch.sort(stacked, dim=0)
    return sorted_values[trim : n - trim].mean(dim=0)


def clip_by_norm(update: torch.Tensor, max_norm: float) -> torch.Tensor:
    norm = torch.linalg.vector_norm(update)
    if norm <= max_norm:
        return update
    return update * (float(max_norm) / max(1e-12, float(norm)))
