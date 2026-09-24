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


def add_configured_trigger(inputs: torch.Tensor, attack_config: dict) -> torch.Tensor:
    """Attack-side trigger constructor; never imported by TierGuard 2's auditor."""
    name = str(attack_config.get("name", "backdoor"))
    if name not in {"unknown_patch_model_replacement", "distributed_backdoor",
                    "defence_aware_optimized_trigger"}:
        return add_bottom_right_square(inputs)
    out = inputs.clone()
    if out.dim() == 3:
        view = out.unsqueeze(0)
    elif out.dim() == 4:
        view = out
    else:
        raise ValueError("Configured image trigger requires CHW or NCHW tensor")
    height, width = view.shape[-2:]
    size = int(attack_config.get("trigger_size", 3))
    value = float(attack_config.get("trigger_value", 1.0))
    if size < 1 or size > min(height, width):
        raise ValueError("Invalid trigger size")
    if name == "distributed_backdoor":
        span = max(1, size // 2)
        corners = ((0, 0), (0, width - span), (height - span, 0),
                   (height - span, width - span))
        component = attack_config.get("distributed_component")
        if component is not None:
            component = int(component)
            if component not in range(4):
                raise ValueError("Distributed trigger component must be 0, 1, 2 or 3")
            corners = (corners[component],)
        for top, left in corners:
            view[:, :, top:top + span, left:left + span] = value
    else:
        top = int(attack_config.get("trigger_top", height - size))
        left = int(attack_config.get("trigger_left", width - size))
        if not (0 <= top <= height - size and 0 <= left <= width - size):
            raise ValueError("Configured trigger location is outside the image")
        value_tensor = attack_config.get("trigger_tensor")
        if value_tensor is not None:
            patch = value_tensor.to(device=view.device, dtype=view.dtype)
            if tuple(patch.shape) != (view.shape[1], size, size):
                raise ValueError("Optimized trigger tensor has the wrong shape")
            view[:, :, top:top + size, left:left + size] = patch
        else:
            view[:, :, top:top + size, left:left + size] = value
    return out


class BackdoorDataset(Dataset):
    def __init__(self, base: Dataset, target_label: int = 0, source_label: int | None = None,
                 attack_config: dict | None = None):
        self.base = base
        self.target_label = int(target_label)
        self.source_label = source_label
        self.attack_config = attack_config
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
        trigger = (add_configured_trigger(image, self.attack_config)
                   if self.attack_config is not None else add_bottom_right_square(image))
        return trigger, self.target_label
