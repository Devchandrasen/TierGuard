from __future__ import annotations

import torch

from .base import AggregationResult, BaseAggregator, geometric_median, stack_updates


class ShieldLikeAggregator(BaseAggregator):
    """Hierarchical robust baseline inspired by SHIELD, not the authors' original code."""

    def aggregate(self, updates, weights=None, **kwargs):
        stacked = stack_updates(updates)
        center = geometric_median(updates, weights=weights, max_iter=5)
        distances = torch.linalg.vector_norm(stacked - center.view(1, -1), dim=1)
        reliability = 1.0 / distances.clamp_min(1e-6)
        reliability = reliability / reliability.sum()
        update = (stacked * reliability.view(-1, 1)).sum(dim=0)
        anomaly = (distances / distances.median().clamp_min(1e-6)).clamp(max=10.0)
        return AggregationResult(
            update=update,
            weights=reliability,
            suspicion=anomaly / anomaly.max().clamp_min(1e-6),
            anomaly_mass=float(anomaly.mean().item() / 10.0),
        )
