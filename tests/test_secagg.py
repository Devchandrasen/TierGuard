from __future__ import annotations

import pytest
import torch

from tierguard.security.additive_sharing import additive_reconstruct, additive_share
from tierguard.security.finite_field import field_modulus
from tierguard.security.shamir import reconstruct, share
from tierguard.security.threshold_secagg import ThresholdSecureAggregator


def test_additive_shares_reconstruct_vector():
    modulus = field_modulus(31)
    secret = torch.tensor([1, 2, 3], dtype=torch.long)
    shares = additive_share(secret, n=4, modulus=modulus)
    assert torch.equal(additive_reconstruct(shares, modulus), secret)


def test_shamir_reconstructs_with_threshold():
    modulus = field_modulus(31)
    shares = share(12345, n=5, threshold=3, modulus=modulus)
    assert reconstruct(shares[:3], threshold=3, modulus=modulus) == 12345


def test_shamir_fails_below_threshold():
    modulus = field_modulus(31)
    shares = share(12345, n=5, threshold=3, modulus=modulus)
    with pytest.raises(ValueError):
        reconstruct(shares[:2], threshold=3, modulus=modulus)


def test_secure_aggregation_sum_matches_plaintext():
    updates = [torch.tensor([0.1, -0.2]), torch.tensor([0.3, 0.4])]
    secagg = ThresholdSecureAggregator(committee_size=3, threshold=2, quantization_bits=16, field_bits=31)
    result = secagg.aggregate(updates)
    assert result.overhead["reconstruction_success"] is True
    assert torch.allclose(result.aggregate, sum(updates), atol=1 / 256)
