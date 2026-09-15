from __future__ import annotations

import torch

from tierguard.fl.update_utils import apply_update, flatten_model
from tierguard.models.cifar_cnn import CifarCNN


def test_apply_update_handles_batchnorm_buffers():
    model = CifarCNN(num_classes=10)
    update = torch.zeros_like(flatten_model(model))
    apply_update(model, update, server_lr=1.0)
    assert flatten_model(model).numel() == update.numel()


def test_flatten_model_includes_batchnorm_running_stats():
    model = CifarCNN(num_classes=10)
    state_float_numel = sum(value.numel() for value in model.state_dict().values() if torch.is_floating_point(value))
    param_numel = sum(param.numel() for param in model.parameters())
    assert flatten_model(model).numel() == state_float_numel
    assert flatten_model(model).numel() > param_numel


def test_apply_update_updates_batchnorm_running_stats():
    model = CifarCNN(num_classes=10)
    base = flatten_model(model)
    update = torch.ones_like(base) * 0.01
    before = model.state_dict()["features.1.running_mean"].clone()
    apply_update(model, update, server_lr=1.0)
    after = model.state_dict()["features.1.running_mean"]
    assert not torch.allclose(before, after)
