from __future__ import annotations

import torch
from torch.utils.data import Dataset


def add_bottom_right_square(inputs: torch.Tensor, size: int = 3, value: float = 1.0) -> torch.Tensor:
    poisoned = inputs.clone()
    if poisoned.dim() == 1:
        poisoned[-min(size, poisoned.size(0)) :] = value
    elif poisoned.dim() == 2:
        poisoned[:, -min(size, poisoned.size(1)) :] = value
    elif poisoned.dim() == 3:
        poisoned[:, -size:, -size:] = value
    elif poisoned.dim() == 4:
        poisoned[:, :, -size:, -size:] = value
    else:
        raise ValueError(f"Expected image or tabular tensor with 1 to 4 dims, got {poisoned.shape}")
    return poisoned


class BackdoorDataset(Dataset):
    def __init__(self, base: Dataset, target_label: int = 0, source_label: int | None = None):
        self.base = base
        self.target_label = int(target_label)
        self.source_label = source_label
        self.indices = []
        for idx in range(len(base)):
            _, label = base[idx]
            label = int(label)
            if label == self.target_label:
                continue
            if self.source_label is not None and label != int(self.source_label):
                continue
            self.indices.append(idx)

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, idx: int):
        image, _ = self.base[self.indices[idx]]
        return add_bottom_right_square(image), self.target_label
