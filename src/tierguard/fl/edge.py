from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass
class EdgeAggregate:
    edge_id: int
    update: torch.Tensor
    num_samples: int
    reliability: float = 1.0
    anomaly_mass: float = 0.0
