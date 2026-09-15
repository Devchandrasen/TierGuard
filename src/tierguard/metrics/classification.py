from __future__ import annotations

import torch
from sklearn.metrics import f1_score
from torch import nn
from torch.utils.data import DataLoader


@torch.no_grad()
def evaluate_classifier(
    model: nn.Module, loader: DataLoader, device: torch.device
) -> dict[str, float]:
    model = model.to(device)
    model.eval()
    criterion = nn.CrossEntropyLoss(reduction="sum")
    total_loss = 0.0
    total_correct = 0
    total = 0
    y_true: list[int] = []
    y_pred: list[int] = []
    for inputs, targets in loader:
        inputs = inputs.to(device)
        targets = targets.to(device).long()
        logits = model(inputs)
        total_loss += float(criterion(logits, targets).detach().cpu())
        pred = logits.argmax(dim=1)
        total_correct += int((pred == targets).sum().detach().cpu())
        total += targets.numel()
        y_true.extend(targets.cpu().tolist())
        y_pred.extend(pred.cpu().tolist())
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0) if y_true else 0.0
    weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0) if y_true else 0.0
    return {
        "clean_loss": total_loss / max(1, total),
        "clean_accuracy": total_correct / max(1, total),
        "macro_f1": float(macro_f1),
        "weighted_f1": float(weighted_f1),
    }
