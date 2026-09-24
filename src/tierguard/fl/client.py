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
    attack_trigger: torch.Tensor | None = None


class FederatedClient:
    def __init__(self, client_id: int, edge_id: int, loader: DataLoader,
                 malicious: bool = False, distributed_component: int | None = None):
        self.client_id = client_id
        self.edge_id = edge_id
        self.loader = loader
        self.malicious = malicious
        self.distributed_component = distributed_component

    def train(self, model, config: dict, device: torch.device, num_classes: int,
              round_idx: int = 0) -> ClientUpdate:
        attack_config = config.get("attack", {})
        if (self.malicious and attack_config.get("name") == "distributed_backdoor"
                and self.distributed_component is not None):
            attack_config = {**attack_config,
                             "distributed_component": self.distributed_component}
        result = train_local_model(
            model,
            self.loader,
            config["federated"],
            device,
            attack_config=attack_config,
            malicious=self.malicious,
            num_classes=num_classes,
            attack_seed=int(config.get("experiment", {}).get("seed", 1))
            + self.client_id * 1009 + round_idx * 100_003,
        )
        return ClientUpdate(
            update=result.update,
            client_id=self.client_id,
            edge_id=self.edge_id,
            num_samples=result.num_samples,
            malicious=self.malicious,
            local_loss=result.loss,
            local_accuracy=result.accuracy,
            attack_trigger=result.attack_trigger,
        )
