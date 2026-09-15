from __future__ import annotations

from dataclasses import dataclass

import torch

from .additive_sharing import additive_reconstruct, additive_share
from .comm_cost import threshold_comm_cost
from .finite_field import field_modulus
from .quantization import dequantize, quantize


@dataclass
class SecureAggregationResult:
    aggregate: torch.Tensor
    overhead: dict[str, float | int | bool]


class ThresholdSecureAggregator:
    def __init__(
        self,
        committee_size: int = 3,
        threshold: int = 2,
        quantization_bits: int = 16,
        field_bits: int = 64,
    ):
        self.committee_size = committee_size
        self.threshold = threshold
        self.quantization_bits = quantization_bits
        self.field_bits = field_bits
        self.modulus = field_modulus(field_bits)

    def aggregate(self, updates: list[torch.Tensor], dropout_fraction: float = 0.0) -> SecureAggregationResult:
        if self.committee_size - int(round(self.committee_size * dropout_fraction)) < self.threshold:
            return SecureAggregationResult(
                aggregate=torch.zeros_like(updates[0]),
                overhead={
                    "reconstruction_success": False,
                    "threshold": self.threshold,
                    "committee_size": self.committee_size,
                    "tolerated_collusion": self.threshold - 1,
                    "tolerated_dropout": self.committee_size - self.threshold,
                },
            )
        q_updates = [quantize(update, self.quantization_bits, self.field_bits) for update in updates]
        party_sums = [torch.zeros_like(q_updates[0]).long() for _ in range(self.committee_size)]
        for q_update in q_updates:
            shares = additive_share(q_update, self.committee_size, self.modulus)
            for idx, share in enumerate(shares):
                party_sums[idx] = torch.remainder(party_sums[idx] + share, self.modulus)
        reconstructed = additive_reconstruct(party_sums, self.modulus)
        aggregate = dequantize(reconstructed, self.quantization_bits, self.field_bits)
        comm = threshold_comm_cost(
            len(updates), updates[0].numel(), self.quantization_bits, self.committee_size
        )
        comm.update(
            {
                "field_operations": int(len(updates) * updates[0].numel() * self.committee_size),
                "threshold": self.threshold,
                "committee_size": self.committee_size,
                "tolerated_collusion": self.threshold - 1,
                "tolerated_dropout": self.committee_size - self.threshold,
                "reconstruction_success": True,
            }
        )
        return SecureAggregationResult(aggregate=aggregate, overhead=comm)
