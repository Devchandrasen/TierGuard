from __future__ import annotations

import math


def compute_epsilon(
    noise_multiplier: float,
    sample_rate: float,
    steps: int,
    delta: float,
    orders: tuple[int, ...] = (2, 3, 4, 8, 16, 32, 64),
) -> float:
    if steps <= 0:
        return 0.0
    if noise_multiplier <= 0:
        return float("inf")
    epsilons = []
    for order in orders:
        rdp = steps * (sample_rate**2) * order / (2.0 * noise_multiplier**2)
        eps = rdp + math.log(1.0 / delta) / (order - 1)
        epsilons.append(eps)
    return float(min(epsilons))
