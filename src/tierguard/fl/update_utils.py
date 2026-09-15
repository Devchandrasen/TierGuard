from __future__ import annotations

from collections import OrderedDict

import torch
from torch import nn


def _vector_state_items(model: nn.Module):
    """Return state entries that can be federated as floating-point deltas."""
    for key, value in model.state_dict().items():
        if torch.is_floating_point(value):
            yield key, value


def flatten_model(model: nn.Module) -> torch.Tensor:
    chunks = [value.detach().reshape(-1).cpu() for _, value in _vector_state_items(model)]
    if not chunks:
        return torch.empty(0)
    return torch.cat(chunks)


def state_dict_to_vector(state_dict: dict[str, torch.Tensor]) -> torch.Tensor:
    chunks = [
        value.detach().reshape(-1).cpu()
        for value in state_dict.values()
        if torch.is_floating_point(value)
    ]
    if not chunks:
        return torch.empty(0)
    return torch.cat(chunks)


def unflatten_model(vector: torch.Tensor, model: nn.Module) -> OrderedDict[str, torch.Tensor]:
    vector = vector.detach().cpu()
    new_state: OrderedDict[str, torch.Tensor] = OrderedDict(
        (key, value.detach().cpu().clone()) for key, value in model.state_dict().items()
    )
    cursor = 0
    for key, value in _vector_state_items(model):
        numel = value.numel()
        new_state[key] = vector[cursor : cursor + numel].view_as(value).to(dtype=value.dtype)
        cursor += numel
    if cursor != vector.numel():
        raise ValueError(f"Vector has {vector.numel()} values but model consumed {cursor}")
    return new_state


def get_update(global_model: nn.Module, local_model: nn.Module) -> torch.Tensor:
    return flatten_model(local_model) - flatten_model(global_model)


def apply_update(global_model: nn.Module, update: torch.Tensor, server_lr: float = 1.0) -> None:
    base = flatten_model(global_model)
    new_vector = base + server_lr * update.detach().cpu()
    state = unflatten_model(new_vector, global_model)
    global_model.load_state_dict(state)


def vector_to_model(vector: torch.Tensor, model: nn.Module) -> nn.Module:
    model.load_state_dict(unflatten_model(vector, model))
    return model
