from __future__ import annotations

from .base import AggregationResult, BaseAggregator, normalize_weights, weighted_mean


class FedAvgAggregator(BaseAggregator):
    def aggregate(self, updates, weights=None, **kwargs):
        normed = normalize_weights(weights, len(updates))
        return AggregationResult(update=weighted_mean(updates, normed), weights=normed)
