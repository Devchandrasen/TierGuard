from __future__ import annotations

from .base import AggregationResult, BaseAggregator, geometric_median


class RFAAggregator(BaseAggregator):
    def aggregate(self, updates, weights=None, **kwargs):
        return AggregationResult(update=geometric_median(updates, weights=weights, max_iter=10))
