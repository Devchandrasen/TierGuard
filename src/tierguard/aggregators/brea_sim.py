from __future__ import annotations

from .trimmed_mean import TrimmedMeanAggregator


class BreaSimAggregator(TrimmedMeanAggregator):
    """Privacy-preserving Byzantine-resilient secure aggregation simulation."""

    def aggregate(self, updates, weights=None, **kwargs):
        result = super().aggregate(updates, weights, **kwargs)
        result.metadata["secure_robust_sim"] = True
        return result
