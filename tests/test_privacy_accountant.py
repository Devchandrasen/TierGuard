from __future__ import annotations

import torch

from tierguard.privacy.clipping import clip_update
from tierguard.privacy.rdp_accountant import compute_epsilon


def test_epsilon_increases_with_rounds():
    eps1 = compute_epsilon(noise_multiplier=1.0, sample_rate=0.1, steps=10, delta=1e-5)
    eps2 = compute_epsilon(noise_multiplier=1.0, sample_rate=0.1, steps=20, delta=1e-5)
    assert eps2 > eps1


def test_epsilon_decreases_with_noise():
    eps_low_noise = compute_epsilon(noise_multiplier=0.5, sample_rate=0.1, steps=10, delta=1e-5)
    eps_high_noise = compute_epsilon(noise_multiplier=1.0, sample_rate=0.1, steps=10, delta=1e-5)
    assert eps_high_noise < eps_low_noise


def test_clipping_enforces_norm_bound():
    update = torch.ones(10) * 10
    clipped = clip_update(update, 1.0)
    assert torch.linalg.vector_norm(clipped) <= 1.0001
