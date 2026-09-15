from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass
class CloudAggregate:
    update: torch.Tensor
    anomaly_mean: float = 0.0
    anomaly_max: float = 0.0
