"""Attacker-side bounded trigger optimization without defender-root access."""

from __future__ import annotations

import copy

import torch
from torch.nn import functional as F


def optimize_trigger(model, loader, attack_config: dict, device: torch.device,
                     seed: int) -> torch.Tensor:
    try:
        images, labels = next(iter(loader))
    except StopIteration as exc:
        raise ValueError("Adaptive attacker has no local examples") from exc
    target = int(attack_config["target_label"])
    images = images[labels != target]
    if len(images) == 0:
        raise ValueError("Adaptive attacker has no non-target local examples")
    images = images[:int(attack_config.get("optimize_items", 16))].to(device)
    channels, height, width = images.shape[1:]
    size = int(attack_config.get("trigger_size", 3))
    top = int(attack_config.get("trigger_top", height - size))
    left = int(attack_config.get("trigger_left", width - size))
    if size < 1 or not (0 <= top <= height - size and 0 <= left <= width - size):
        raise ValueError("Invalid adaptive trigger dimensions or location")
    low = images.amin(dim=(0, 2, 3), keepdim=True)
    high = images.amax(dim=(0, 2, 3), keepdim=True)
    if not torch.isfinite(images).all():
        raise FloatingPointError("Adaptive trigger received non-finite local images")
    generator = torch.Generator(device="cpu").manual_seed(seed)
    raw = torch.randn((1, channels, size, size), generator=generator)
    raw = raw.to(device).requires_grad_(True)
    frozen_model = copy.deepcopy(model).to(device).eval()
    frozen_model.requires_grad_(False)
    optimizer = torch.optim.Adam([raw], lr=float(attack_config.get("optimize_lr", 0.05)))
    targets = torch.full((len(images),), target, dtype=torch.long, device=device)
    for _ in range(int(attack_config.get("optimize_steps", 20))):
        optimizer.zero_grad(set_to_none=True)
        patch = low + (high - low) * torch.sigmoid(raw)
        probed = images.clone()
        probed[:, :, top:top + size, left:left + size] = patch
        # Penalize resemblance to the auditor's fixed high/low/checker probes.
        normalized = torch.sigmoid(raw)
        row = torch.arange(size, device=device).view(-1, 1)
        col = torch.arange(size, device=device).view(1, -1)
        checker = ((row + col) % 2).float().view(1, 1, size, size)
        similarities = torch.stack([
            (normalized - template).square().mean()
            for template in (torch.zeros_like(normalized), torch.ones_like(normalized), checker)
        ])
        diversity = torch.min(similarities)
        loss = F.cross_entropy(frozen_model(probed), targets)
        loss = loss - float(attack_config.get("probe_avoidance_weight", 0.1)) * diversity
        if not torch.isfinite(loss):
            raise FloatingPointError("Adaptive trigger objective became non-finite")
        loss.backward()
        if raw.grad is None or not torch.isfinite(raw.grad).all():
            raise FloatingPointError("Adaptive trigger gradient became non-finite")
        optimizer.step()
    trigger = low + (high - low) * torch.sigmoid(raw)
    if not torch.isfinite(trigger).all():
        raise FloatingPointError("Adaptive trigger became non-finite")
    return trigger.detach().cpu().squeeze(0)
