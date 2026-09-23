"""The 30 CIFAR-10 green-car indices listed by the Backdoors101 authors.

Source: https://github.com/ebagdasa/backdoors101 at commit
9f48fbbb496aaed4ba696494950a5d71ee82a80c, configs/cifar_fed.yaml.
The first 20 are attacker-only training examples; the last 10 are held-out
semantic evaluation examples. This 20/10 split is ours, not the paper's.
"""

from __future__ import annotations

from torch.utils.data import Dataset


GREEN_CAR_INDICES = (
    389, 561, 874, 1605, 3378, 3678, 4528, 9744, 19165, 19500,
    21422, 22984, 32941, 34287, 34385, 36005, 37365, 37533, 38658,
    38735, 39824, 40138, 41336, 41861, 47001, 47026, 48003, 48030,
    49163, 49588,
)
GREEN_CAR_ATTACK_TRAIN = GREEN_CAR_INDICES[:20]
GREEN_CAR_HELDOUT_TEST = GREEN_CAR_INDICES[20:]


class SemanticTargetDataset(Dataset):
    def __init__(self, base: Dataset, target_label: int = 2):
        self.base = base
        self.target_label = target_label

    def __len__(self) -> int:
        return len(self.base)

    def __getitem__(self, index: int):
        image, _ = self.base[index]
        return image, self.target_label
