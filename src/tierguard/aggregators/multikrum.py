from __future__ import annotations

import torch

from .base import AggregationResult, BaseAggregator, weighted_mean
from .krum import krum_scores


class MultiKrumAggregator(BaseAggregator):
    def aggregate(self, updates, weights=None, **kwargs):
        f = self.config.get("aggregation", {}).get("krum_f")
        if f is None:
            f = max(0, int(len(updates) * self.config.get("attack", {}).get("malicious_fraction", 0.0)))
        scores = krum_scores(updates, int(f))
        m = max(1, len(updates) - int(f) - 2)
        selected_idx = torch.argsort(scores)[:m].tolist()
        selected_updates = [updates[i] for i in selected_idx]
        selected_weights = torch.zeros(len(updates), dtype=torch.float32)
        selected_weights[selected_idx] = 1.0 / len(selected_idx)
        return AggregationResult(
            update=weighted_mean(selected_updates),
            weights=selected_weights,
            metadata={"selected": selected_idx},
        )
