from __future__ import annotations

from dataclasses import dataclass

import torch
from torch.utils.data import DataLoader

from tierguard.fl.local_training import train_local_model


@dataclass
class ClientUpdate:
    update: torch.Tensor
    client_id: int
    edge_id: int
    num_samples: int
    malicious: bool
    local_loss: float
    local_accuracy: float


class FederatedClient:
    def __init__(self, client_id: int, edge_id: int, loader: DataLoader, malicious: bool = False):
        self.client_id = client_id
        self.edge_id = edge_id
        self.loader = loader
        self.malicious = malicious

    def train(self, model, config: dict, device: torch.device, num_classes: int) -> ClientUpdate:
        result = train_local_model(
            model,
            self.loader,
            config["federated"],
            device,
            attack_config=config.get("attack", {}),
            malicious=self.malicious,
            num_classes=num_classes,
        )
        return ClientUpdate(
            update=result.update,
            client_id=self.client_id,
            edge_id=self.edge_id,
            num_samples=result.num_samples,
            malicious=self.malicious,
            local_loss=result.loss,
            local_accuracy=result.accuracy,
        )
