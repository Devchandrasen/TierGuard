from __future__ import annotations

import torch
from torch import nn
from torch.utils.data import DataLoader


@torch.no_grad()
def attack_success_rate(model: nn.Module, loader: DataLoader, device: torch.device) -> float:
    model = model.to(device)
    model.eval()
    total = 0
    success = 0
    for inputs, targets in loader:
        inputs = inputs.to(device)
        targets = targets.to(device).long()
        pred = model(inputs).argmax(dim=1)
        success += int((pred == targets).sum().detach().cpu())
        total += targets.numel()
    return success / max(1, total)
