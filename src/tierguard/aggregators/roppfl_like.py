from __future__ import annotations

import torch
from torch.nn import functional as F

from .base import AggregationResult, BaseAggregator, stack_updates


class RoPPFLLikeAggregator(BaseAggregator):
    """Fair reimplementation inspired by RoPPFL, not the authors' original code."""

    def aggregate(self, updates, weights=None, **kwargs):
        stacked = stack_updates(updates)
        noise_multiplier = float(self.config.get("privacy", {}).get("dp_noise_multiplier", 0.0))
        if noise_multiplier > 0:
            stacked = stacked + torch.randn_like(stacked) * noise_multiplier * 0.01
        majority = stacked.mean(dim=0)
        sim = F.cosine_similarity(stacked, majority.view(1, -1), dim=1).clamp_min(0.0)
        if sim.sum() <= 1e-12:
            sim = torch.ones_like(sim)
        agg_weights = sim / sim.sum()
        return AggregationResult(update=(stacked * agg_weights.view(-1, 1)).sum(dim=0), weights=agg_weights)
