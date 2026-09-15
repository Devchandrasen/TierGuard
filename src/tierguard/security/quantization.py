from __future__ import annotations

import torch

from .finite_field import field_modulus


def quantization_scale(bits: int) -> float:
    return float(2 ** max(1, bits // 2))


def quantize(vector: torch.Tensor, bits: int = 16, field_bits: int = 64) -> torch.Tensor:
    scale = quantization_scale(bits)
    modulus = field_modulus(field_bits)
    q = torch.round(vector.detach().cpu().float() * scale).to(torch.long)
    return torch.remainder(q, modulus)


def dequantize(values: torch.Tensor, bits: int = 16, field_bits: int = 64) -> torch.Tensor:
    scale = quantization_scale(bits)
    modulus = field_modulus(field_bits)
    signed = values.detach().cpu().clone().to(torch.long)
    signed = torch.where(signed > modulus // 2, signed - modulus, signed)
    return signed.float() / scale
