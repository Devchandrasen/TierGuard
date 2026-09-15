from __future__ import annotations

import torch


def flip_labels(
    labels: torch.Tensor,
    num_classes: int,
    source_label: int | None = None,
    target_label: int | None = None,
) -> torch.Tensor:
    if source_label is not None and target_label is not None:
        flipped = labels.clone()
        flipped[labels == int(source_label)] = int(target_label)
        return flipped
    return (num_classes - 1 - labels).long()
