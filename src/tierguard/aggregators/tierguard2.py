"""Trigger/target-blind counterfactual audit and continuous two-level weighting.

This is a research implementation, not a secure-computation protocol.  The
auditor accepts only a model, candidate update, disjoint root splits and its
own frozen settings; attack configuration is intentionally absent.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass

import torch
from torch.nn import functional as F

from tierguard.aggregators.base import clip_by_norm, weighted_mean
from tierguard.fl.update_utils import apply_update


@dataclass(frozen=True)
class AuditResult:
    risk: float
    heldout_target_gain: float
    clean_loss_change: float
    pattern: str
    target_class: int


def _take_balanced_batch(loader, per_class: int) -> tuple[torch.Tensor, torch.Tensor]:
    images: list[torch.Tensor] = []
    labels: list[int] = []
    counts: dict[int, int] = {}
    for batch_images, batch_labels in loader:
        for image, label in zip(batch_images, batch_labels):
            cls = int(label)
            if counts.get(cls, 0) < per_class:
                images.append(image)
                labels.append(cls)
                counts[cls] = counts.get(cls, 0) + 1
    if not images:
        raise ValueError("Audit root is empty")
    if len(set(counts.values())) != 1:
        raise ValueError("Audit root cannot supply a balanced probe batch")
    return torch.stack(images), torch.tensor(labels, dtype=torch.long)


def _patch(images: torch.Tensor, kind: str, top: int, left: int, size: int,
           low: torch.Tensor, high: torch.Tensor) -> torch.Tensor:
    out = images.clone()
    height, width = out.shape[-2:]
    if kind == "distributed":
        # Four separated subpatches are one candidate distributed trigger.
        span = max(1, size // 2)
        for row, col in ((0, 0), (0, width - span), (height - span, 0),
                         (height - span, width - span)):
            out[:, :, row:row + span, col:col + span] = high
    elif kind == "checker":
        for row in range(size):
            for col in range(size):
                value = high if (row + col) % 2 == 0 else low
                out[:, :, top + row, left + col] = value[:, :, 0, 0]
    else:
        value = high if kind == "high" else low
        out[:, :, top:top + size, left:left + size] = value
    return out


class CounterfactualAuditor:
    def __init__(self, search_loader, eval_loader, num_classes: int, settings: dict,
                 device: torch.device):
        self.device = device
        self.num_classes = int(num_classes)
        self.settings = dict(settings)
        per_class = int(settings.get("probes_per_class", 2))
        self.search_images, self.search_labels = _take_balanced_batch(search_loader, per_class)
        self.eval_images, self.eval_labels = _take_balanced_batch(eval_loader, per_class)
        if self.search_images.shape[1:] != self.eval_images.shape[1:]:
            raise ValueError("Audit root splits have different image shapes")
        self.search_images = self.search_images.to(device)
        self.search_labels = self.search_labels.to(device)
        self.eval_images = self.eval_images.to(device)
        self.eval_labels = self.eval_labels.to(device)
        # Values are measured only from the search root. This also handles
        # normalized CIFAR-10 tensors without using attack configuration.
        self.low = self.search_images.amin(dim=(0, 2, 3), keepdim=True)
        self.high = self.search_images.amax(dim=(0, 2, 3), keepdim=True)
        height, width = self.search_images.shape[-2:]
        sizes = tuple(int(size) for size in settings.get("patch_sizes", [3]))
        patterns: list[tuple[str, int, int, int]] = []
        for size in sizes:
            if size < 1 or size > min(height, width):
                raise ValueError("Patch size is outside the image")
            for top in sorted({0, (height - size) // 2, height - size}):
                for left in sorted({0, (width - size) // 2, width - size}):
                    for kind in ("high", "low", "checker"):
                        patterns.append((kind, top, left, size))
            patterns.append(("distributed", 0, 0, size))
        self.patterns = patterns
        self.search_probes = torch.cat(
            [_patch(self.search_images, *pattern, self.low, self.high)
             for pattern in self.patterns], dim=0
        )
        self.eval_probes = torch.cat(
            [_patch(self.eval_images, *pattern, self.low, self.high)
             for pattern in self.patterns], dim=0
        )
        self._prepared = False

    @staticmethod
    def _target_gain(base: torch.Tensor, candidate: torch.Tensor,
                     labels: torch.Tensor) -> torch.Tensor:
        gains = []
        for target in range(base.shape[1]):
            mask = labels != target
            if bool(mask.any()):
                gains.append((candidate[mask, target] - base[mask, target]).mean())
            else:
                gains.append(torch.tensor(float("-inf"), device=base.device))
        return torch.stack(gains)

    def _probabilities(self, model: torch.nn.Module, images: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            chunk_size = int(self.settings.get("probe_forward_batch_size", 128))
            return torch.cat(
                [F.softmax(model(chunk), dim=1) for chunk in images.split(chunk_size)], dim=0
            )

    def begin_round(self, model: torch.nn.Module) -> None:
        """Cache the unchanged-model counterfactuals once per FL round."""
        base = model.to(self.device).eval()
        search_size = self.search_images.shape[0]
        eval_size = self.eval_images.shape[0]
        self._base_search = self._probabilities(base, self.search_probes).view(
            len(self.patterns), search_size, self.num_classes
        )
        self._base_eval = self._probabilities(base, self.eval_probes).view(
            len(self.patterns), eval_size, self.num_classes
        )
        with torch.no_grad():
            self._base_clean_loss = F.cross_entropy(base(self.eval_images), self.eval_labels)
        self._prepared = True

    def audit(self, model: torch.nn.Module, update: torch.Tensor,
              server_lr: float = 1.0) -> AuditResult:
        base = model.to(self.device).eval()
        if not self._prepared:
            self.begin_round(base)
        candidate = copy.deepcopy(base)
        apply_update(candidate, update, server_lr=server_lr)
        candidate = candidate.to(self.device).eval()
        best_gain = float("-inf")
        best_pattern = self.patterns[0]
        best_target = 0
        search_size = self.search_images.shape[0]
        candidate_search = self._probabilities(candidate, self.search_probes).view(
            len(self.patterns), search_size, self.num_classes
        )
        best_index = 0
        for index, pattern in enumerate(self.patterns):
            gains = self._target_gain(
                self._base_search[index],
                candidate_search[index],
                self.search_labels,
            )
            value, target = torch.max(gains, dim=0)
            if float(value) > best_gain:
                best_gain = float(value)
                best_pattern = pattern
                best_target = int(target)
                best_index = index
        eval_size = self.eval_images.shape[0]
        heldout = self.eval_probes[best_index * eval_size:(best_index + 1) * eval_size]
        with torch.no_grad():
            base_probed = self._base_eval[best_index]
            candidate_probed = self._probabilities(candidate, heldout)
            mask = self.eval_labels != best_target
            gain = float((candidate_probed[mask, best_target] -
                          base_probed[mask, best_target]).mean())
            loss_change = float(
                F.cross_entropy(candidate(self.eval_images), self.eval_labels)
                - self._base_clean_loss
            )
        # The threshold and credit must be frozen using clean development runs.
        threshold = float(self.settings["calibrated_gain_threshold"])
        clean_credit = float(self.settings.get("clean_improvement_credit", 0.25))
        risk = max(0.0, gain - threshold - clean_credit * max(0.0, -loss_change))
        return AuditResult(
            risk=risk,
            heldout_target_gain=gain,
            clean_loss_change=loss_change,
            pattern=f"{best_pattern[0]}:{best_pattern[1]}:{best_pattern[2]}:{best_pattern[3]}",
            target_class=best_target,
        )


def continuous_weight(risk: float, settings: dict) -> float:
    gamma = float(settings.get("risk_gamma", 8.0))
    floor = float(settings.get("weight_floor", 0.05))
    if gamma < 0 or not 0 < floor <= 1:
        raise ValueError("Invalid continuous weighting parameters")
    return max(floor, math.exp(-gamma * max(0.0, risk)))


def aggregate_level(updates: list[torch.Tensor], masses: list[float], risks: list[float],
                    clip_radius: float, settings: dict) -> tuple[torch.Tensor, list[float]]:
    if not (len(updates) == len(masses) == len(risks)) or not updates:
        raise ValueError("Updates, masses and risks must be nonempty and aligned")
    if clip_radius <= 0:
        raise ValueError("Clip radius must be positive")
    clipped = [clip_by_norm(update.detach().cpu().float(), clip_radius) for update in updates]
    effective = [float(mass) * continuous_weight(risk, settings)
                 for mass, risk in zip(masses, risks)]
    return weighted_mean(clipped, effective), effective
