from __future__ import annotations

import torch

from .base import AggregationResult, BaseAggregator, stack_updates


def krum_scores(updates: list[torch.Tensor], f: int) -> torch.Tensor:
    stacked = stack_updates(updates)
    n = stacked.size(0)
    distances = torch.cdist(stacked, stacked, p=2).pow(2)
    sorted_distances, _ = torch.sort(distances, dim=1)
    closest = max(1, n - int(f) - 2)
    return sorted_distances[:, 1 : closest + 1].sum(dim=1)


class KrumAggregator(BaseAggregator):
    def aggregate(self, updates, weights=None, **kwargs):
        f = self.config.get("aggregation", {}).get("krum_f")
        if f is None:
            f = max(0, int(len(updates) * self.config.get("attack", {}).get("malicious_fraction", 0.0)))
        scores = krum_scores(updates, int(f))
        idx = int(torch.argmin(scores))
        selected = torch.zeros(len(updates), dtype=torch.float32)
        selected[idx] = 1.0
        return AggregationResult(update=updates[idx].detach().cpu().float(), weights=selected, metadata={"krum_index": idx})


class HierarchicalKrumAggregator(KrumAggregator):
    """Apply Krum independently at edge and cloud with an explicit f.

    The study's five-client edge groups and six-edge cloud support f=1;
    smaller groups must fail instead of silently changing the tolerance.
    """

    def aggregate(self, updates, weights=None, **kwargs):
        f = self.config.get("aggregation", {}).get("krum_f")
        if f is None:
            raise ValueError("Hierarchical Krum requires an explicit krum_f")
        f = int(f)
        if f < 0 or len(updates) <= 2 * f + 2:
            raise ValueError("Hierarchical Krum requires n > 2f + 2")
        result = super().aggregate(updates, weights=weights, **kwargs)
        result.metadata.update({"krum_f": f, "group_size": len(updates)})
        return result
