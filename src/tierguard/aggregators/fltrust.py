from __future__ import annotations

import torch
from torch.nn import functional as F

from .base import AggregationResult, BaseAggregator, stack_updates


class FLTrustAggregator(BaseAggregator):
    def aggregate(self, updates, weights=None, reference_update=None, **kwargs):
        if reference_update is None or torch.linalg.vector_norm(reference_update) <= 1e-12:
            from .fedavg import FedAvgAggregator

            return FedAvgAggregator(self.config).aggregate(updates, weights)
        stacked = stack_updates(updates)
        ref = reference_update.detach().cpu().float()
        ref_norm = torch.linalg.vector_norm(ref).clamp_min(1e-12)
        norms = torch.linalg.vector_norm(stacked, dim=1).clamp_min(1e-12)
        trust = F.cosine_similarity(stacked, ref.view(1, -1), dim=1).clamp_min(0.0)
        normalized = stacked * (ref_norm / norms).view(-1, 1)
        denom = trust.sum().clamp_min(1e-12)
        update = (normalized * (trust / denom).view(-1, 1)).sum(dim=0)
        return AggregationResult(update=update, weights=trust / denom, metadata={"trust": trust.tolist()})
