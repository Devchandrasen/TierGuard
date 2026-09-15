from __future__ import annotations

from .fedavg import FedAvgAggregator


class HFLFedAvgAggregator(FedAvgAggregator):
    """Model-quality equivalent to FedAvg; hierarchy is handled by the runner."""
