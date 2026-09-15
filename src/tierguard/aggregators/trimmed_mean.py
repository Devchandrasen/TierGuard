from __future__ import annotations

from .base import AggregationResult, BaseAggregator, coordinate_trimmed_mean


class TrimmedMeanAggregator(BaseAggregator):
    def aggregate(self, updates, weights=None, **kwargs):
        beta = float(self.config.get("aggregation", {}).get("trim_beta", 0.2))
        return AggregationResult(update=coordinate_trimmed_mean(updates, beta=beta))
