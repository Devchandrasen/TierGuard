from __future__ import annotations

import torch
from torch.nn import functional as F

from .base import AggregationResult, BaseAggregator, stack_updates


class FoolsGoldAggregator(BaseAggregator):
    def __init__(self, config=None, dimension=None):
        super().__init__(config, dimension)
        self.memory: dict[int, torch.Tensor] = {}

    def aggregate(self, updates, weights=None, client_ids=None, **kwargs):
        if client_ids is None:
            client_ids = list(range(len(updates)))
        for client_id, update in zip(client_ids, updates):
            current = update.detach().cpu().float()
            self.memory[client_id] = self.memory.get(client_id, torch.zeros_like(current)) + current
        histories = torch.stack([self.memory[client_id] for client_id in client_ids])
        if len(updates) == 1:
            fg_weights = torch.ones(1)
        else:
            normed = F.normalize(histories, dim=1)
            sim = normed @ normed.T
            sim.fill_diagonal_(0.0)
            max_sim = sim.max(dim=1).values.clamp(0.0, 1.0)
            fg_weights = (1.0 - max_sim).clamp_min(0.0)
            if fg_weights.sum() <= 1e-12:
                fg_weights = torch.ones_like(fg_weights)
        fg_weights = fg_weights / fg_weights.sum()
        stacked = stack_updates(updates)
        return AggregationResult(update=(stacked * fg_weights.view(-1, 1)).sum(dim=0), weights=fg_weights)
