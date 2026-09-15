from __future__ import annotations

import torch


def additive_share(secret: torch.Tensor, n: int, modulus: int) -> list[torch.Tensor]:
    secret = torch.remainder(secret.detach().cpu().long(), modulus)
    shares = [torch.randint(0, min(modulus, 2**31 - 1), secret.shape, dtype=torch.long) for _ in range(n - 1)]
    partial = sum(shares, torch.zeros_like(secret))
    shares.append(torch.remainder(secret - partial, modulus))
    return shares


def additive_reconstruct(shares: list[torch.Tensor], modulus: int) -> torch.Tensor:
    if not shares:
        raise ValueError("No shares supplied")
    total = sum([share.long() for share in shares], torch.zeros_like(shares[0]).long())
    return torch.remainder(total, modulus)
