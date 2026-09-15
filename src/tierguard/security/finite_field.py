from __future__ import annotations


def field_modulus(field_bits: int = 64) -> int:
    if field_bits >= 61:
        return 2**61 - 1
    return 2**field_bits - 1


def mod_inv(value: int, modulus: int) -> int:
    return pow(value % modulus, -1, modulus)
