from __future__ import annotations

import torch

from tierguard.attacks.adaptive import adaptive_tierguard_update
from tierguard.attacks.backdoor import poison_batch
from tierguard.attacks.label_flip import flip_labels
from tierguard.attacks.model_replacement import model_replacement
from tierguard.attacks.sign_flip import sign_flip


def test_sign_flip_reverses_update():
    update = torch.tensor([1.0, -2.0])
    assert torch.allclose(sign_flip(update, scale=3), torch.tensor([-3.0, 6.0]))


def test_label_flip_changes_labels():
    labels = torch.tensor([0, 1, 2, 3])
    flipped = flip_labels(labels, num_classes=4)
    assert flipped.tolist() == [3, 2, 1, 0]
    targeted = flip_labels(labels, num_classes=4, source_label=1, target_label=0)
    assert targeted.tolist() == [0, 0, 2, 3]


def test_backdoor_trigger_modifies_image_tensor():
    x = torch.zeros(2, 1, 28, 28)
    y = torch.tensor([1, 2])
    poisoned_x, poisoned_y = poison_batch(x, y, target_label=0, fraction=0.5)
    assert poisoned_x[0, :, -3:, -3:].sum() > 0
    assert poisoned_y[0].item() == 0


def test_backdoor_trigger_modifies_tabular_tensor():
    x = torch.zeros(4, 10)
    y = torch.tensor([1, 1, 1, 1])
    poisoned_x, poisoned_y = poison_batch(x, y, target_label=0, fraction=0.5)
    assert torch.all(poisoned_x[:2, -3:] == 1.0)
    assert torch.all(poisoned_y[:2] == 0)
    assert torch.all(poisoned_y[2:] == 1)


def test_model_replacement_scales_update():
    update = torch.ones(3)
    assert torch.allclose(model_replacement(update, 5), torch.ones(3) * 5)


def test_adaptive_attack_respects_norm_constraint():
    update = torch.ones(10) * 10
    root = torch.ones(10)
    out = adaptive_tierguard_update(update, root, norm_bound=2.0)
    assert torch.linalg.vector_norm(out) <= 2.0001
