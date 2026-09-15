from __future__ import annotations

import copy
from dataclasses import dataclass
import torch
from torch import nn
from torch.utils.data import DataLoader

from tierguard.attacks.backdoor import poison_batch
from tierguard.attacks.label_flip import flip_labels
from tierguard.fl.update_utils import get_update


@dataclass
class LocalTrainResult:
    model: nn.Module
    update: torch.Tensor
    loss: float
    accuracy: float
    num_samples: int


def make_optimizer(model: nn.Module, config: dict) -> torch.optim.Optimizer:
    opt_name = config.get("client_optimizer", "sgd").lower()
    lr = float(config.get("client_lr", 0.01))
    weight_decay = float(config.get("weight_decay", 0.0))
    if opt_name == "adam":
        return torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    return torch.optim.SGD(
        model.parameters(),
        lr=lr,
        momentum=float(config.get("momentum", 0.0)),
        weight_decay=weight_decay,
    )


def _label_flip_batch(targets: torch.Tensor, attack_config: dict, num_classes: int) -> torch.Tensor:
    return flip_labels(
        targets,
        num_classes=num_classes,
        source_label=attack_config.get("source_label"),
        target_label=attack_config.get("target_label"),
    )


def _poison_or_flip_batch(
    inputs: torch.Tensor,
    targets: torch.Tensor,
    attack_config: dict,
    num_classes: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    if inputs.dim() >= 2:
        return poison_batch(
            inputs,
            targets,
            target_label=int(attack_config.get("target_label", 0)),
            fraction=float(attack_config.get("backdoor_fraction", 0.3)),
        )
    return inputs, _label_flip_batch(targets, attack_config, num_classes)


def train_local_model(
    global_model: nn.Module,
    loader: DataLoader,
    federated_config: dict,
    device: torch.device,
    attack_config: dict | None = None,
    malicious: bool = False,
    num_classes: int = 10,
) -> LocalTrainResult:
    model = copy.deepcopy(global_model).to(device)
    model.train()
    optimizer = make_optimizer(model, federated_config)
    criterion = nn.CrossEntropyLoss(label_smoothing=float(federated_config.get("label_smoothing", 0.0)))
    attack_name = (attack_config or {}).get("name", "none") if malicious else "none"
    total_loss = 0.0
    total_correct = 0
    total = 0

    for _ in range(int(federated_config.get("local_epochs", 1))):
        for inputs, targets in loader:
            inputs = inputs.to(device)
            targets = targets.to(device).long()
            if attack_name == "label_flip":
                targets = _label_flip_batch(targets, attack_config, num_classes)
            elif attack_name in {
                "backdoor",
                "backdoor_model_replacement",
                "sybil_backdoor",
                "adaptive_tierguard_aware",
            }:
                inputs, targets = _poison_or_flip_batch(inputs, targets, attack_config, num_classes)

            optimizer.zero_grad(set_to_none=True)
            logits = model(inputs)
            loss = criterion(logits, targets)
            loss.backward()
            optimizer.step()

            batch_size = targets.numel()
            total_loss += float(loss.detach().cpu()) * batch_size
            total_correct += int((logits.argmax(dim=1) == targets).sum().detach().cpu())
            total += batch_size

    update = get_update(global_model.cpu(), model.cpu())
    return LocalTrainResult(
        model=model.cpu(),
        update=update,
        loss=total_loss / max(1, total),
        accuracy=total_correct / max(1, total),
        num_samples=total,
    )


def compute_reference_update(
    global_model: nn.Module,
    root_loader: DataLoader,
    federated_config: dict,
    device: torch.device,
    num_classes: int,
) -> torch.Tensor:
    short_config = dict(federated_config)
    short_config["local_epochs"] = 1
    return train_local_model(
        global_model,
        root_loader,
        short_config,
        device,
        attack_config={"name": "none"},
        malicious=False,
        num_classes=num_classes,
    ).update
