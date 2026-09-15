from __future__ import annotations

import random
from collections.abc import Sequence

from .finite_field import field_modulus, mod_inv


def _eval_poly(coeffs: list[int], x: int, modulus: int) -> int:
    total = 0
    power = 1
    for coeff in coeffs:
        total = (total + coeff * power) % modulus
        power = (power * x) % modulus
    return total


def share_scalar(secret: int, n: int, threshold: int, modulus: int) -> list[tuple[int, int]]:
    if threshold > n:
        raise ValueError("threshold cannot exceed n")
    coeffs = [secret % modulus] + [random.randrange(0, modulus) for _ in range(threshold - 1)]
    return [(x, _eval_poly(coeffs, x, modulus)) for x in range(1, n + 1)]


def reconstruct_scalar(shares: Sequence[tuple[int, int]], threshold: int, modulus: int) -> int:
    if len(shares) < threshold:
        raise ValueError("Not enough shares to reconstruct")
    selected = list(shares[:threshold])
    secret = 0
    for j, (xj, yj) in enumerate(selected):
        num = 1
        den = 1
        for m, (xm, _) in enumerate(selected):
            if m == j:
                continue
            num = (num * (-xm)) % modulus
            den = (den * (xj - xm)) % modulus
        secret = (secret + yj * num * mod_inv(den, modulus)) % modulus
    return secret


def share(secret, n: int, threshold: int, modulus: int | None = None):
    modulus = modulus or field_modulus(61)
    if isinstance(secret, int):
        return share_scalar(secret, n, threshold, modulus)
    values = list(secret)
    scalar_shares = [share_scalar(int(value), n, threshold, modulus) for value in values]
    out = []
    for idx in range(n):
        x = scalar_shares[0][idx][0]
        out.append((x, [shares[idx][1] for shares in scalar_shares]))
    return out


def reconstruct(shares, threshold: int, modulus: int | None = None):
    modulus = modulus or field_modulus(61)
    if not shares:
        raise ValueError("No shares supplied")
    if isinstance(shares[0][1], int):
        return reconstruct_scalar(shares, threshold, modulus)
    width = len(shares[0][1])
    result = []
    for col in range(width):
        col_shares = [(x, values[col]) for x, values in shares]
        result.append(reconstruct_scalar(col_shares, threshold, modulus))
    return result
