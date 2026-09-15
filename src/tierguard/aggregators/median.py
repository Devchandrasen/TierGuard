from __future__ import annotations

from .base import AggregationResult, BaseAggregator, stack_updates


class MedianAggregator(BaseAggregator):
    def aggregate(self, updates, weights=None, **kwargs):
        return AggregationResult(update=stack_updates(updates).median(dim=0).values)
