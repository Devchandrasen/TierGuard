from __future__ import annotations

import torch

from tierguard.data.backdoor import add_bottom_right_square


def poison_batch(
    inputs: torch.Tensor,
    targets: torch.Tensor,
    target_label: int = 0,
    fraction: float = 0.3,
) -> tuple[torch.Tensor, torch.Tensor]:
    if fraction <= 0:
        return inputs, targets
    batch = inputs.size(0)
    count = max(1, int(round(batch * min(1.0, fraction))))
    poisoned_inputs = inputs.clone()
    poisoned_targets = targets.clone()
    poisoned_inputs[:count] = add_bottom_right_square(poisoned_inputs[:count])
    poisoned_targets[:count] = int(target_label)
    return poisoned_inputs, poisoned_targets
