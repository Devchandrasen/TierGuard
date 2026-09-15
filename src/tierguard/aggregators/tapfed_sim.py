from __future__ import annotations

from .fedavg import FedAvgAggregator


class TAPFedSimAggregator(FedAvgAggregator):
    """TAPFed-style threshold secure aggregation simulator with HFL-FedAvg quality."""

    def aggregate(self, updates, weights=None, **kwargs):
        result = super().aggregate(updates, weights, **kwargs)
        security = self.config.get("security", {})
        result.metadata.update(
            {
                "secure_sim": True,
                "edge_threshold": security.get("edge_threshold", 2),
                "edge_committee_size": security.get("edge_committee_size", 3),
                "cloud_threshold": security.get("cloud_threshold", 3),
                "cloud_committee_size": security.get("cloud_committee_size", 5),
            }
        )
        return result
