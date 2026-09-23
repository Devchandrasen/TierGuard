"""Two-tier defender-side adaptation of the official FedGame implementation.

The official NeurIPS 2023 FedGame server builds an auxiliary average model,
reverse-engineers a mask/trigger for every class, selects the smallest mask,
and uses one minus induced target-class success as a client weight.  This
module applies those steps separately at each hierarchy level; it does not
transfer the paper's flat-server theoretical guarantee.
"""

from __future__ import annotations

import copy

import torch
from torch.nn import functional as F

from tierguard.fl.update_utils import apply_update

from .base import AggregationResult, BaseAggregator, stack_updates


def _root_batch(root_loader, limit: int, device: torch.device) -> torch.Tensor:
    chunks = []
    count = 0
    for images, _ in root_loader:
        take = images[:max(0, limit - count)]
        if len(take):
            chunks.append(take)
            count += len(take)
        if count >= limit:
            break
    if not chunks:
        raise ValueError("FedGame needs a nonempty clean root batch")
    batch = torch.cat(chunks).to(device)
    if batch.dim() != 4:
        raise ValueError("FedGame trigger reconstruction supports images only")
    return batch


class HierarchicalFedGameAggregator(BaseAggregator):
    def aggregate(self, updates, weights=None, *, model=None, root_loader=None,
                  device=None, round_idx=0, edge_id=-1, **kwargs):
        if model is None or root_loader is None or device is None:
            raise ValueError("FedGame needs global model, clean root data and device")
        settings = self.config.get("fedgame", {})
        required = ("reconstruction_steps", "reconstruction_lr", "mask_penalty", "root_items")
        if any(key not in settings for key in required):
            raise ValueError("FedGame development settings are incomplete")
        steps = int(settings["reconstruction_steps"])
        if steps <= 0:
            raise ValueError("FedGame reconstruction_steps must be positive")
        device = torch.device(device)
        images = _root_batch(root_loader, int(settings["root_items"]), device)
        stacked = stack_updates(updates)
        auxiliary = copy.deepcopy(model)
        apply_update(auxiliary, stacked.mean(dim=0), server_lr=1.0)
        auxiliary = auxiliary.to(device).eval()
        auxiliary.requires_grad_(False)
        channels, height, width = images.shape[1:]
        low = images.amin(dim=(0, 2, 3), keepdim=True)
        high = images.amax(dim=(0, 2, 3), keepdim=True)
        num_classes = int(auxiliary(images[:1]).shape[1])
        best = None
        mask_norms = []
        for target in range(num_classes):
            generator = torch.Generator(device="cpu").manual_seed(
                int(self.config.get("experiment", {}).get("seed", 1))
                + int(round_idx) * 100_003 + (int(edge_id) + 1) * 1009 + target * 73
            )
            trigger_raw = torch.randn((1, channels, height, width), generator=generator)
            trigger_raw = trigger_raw.to(device).requires_grad_(True)
            mask_raw = torch.full((1, 1, height, width), -3.0,
                                  device=device, requires_grad=True)
            optimizer = torch.optim.Adam(
                [trigger_raw, mask_raw], lr=float(settings["reconstruction_lr"])
            )
            target_labels = torch.full((len(images),), target,
                                       dtype=torch.long, device=device)
            for _ in range(steps):
                optimizer.zero_grad(set_to_none=True)
                mask = torch.sigmoid(mask_raw)
                trigger = low + (high - low) * torch.sigmoid(trigger_raw)
                probed = images * (1.0 - mask) + trigger * mask
                loss = F.cross_entropy(auxiliary(probed), target_labels)
                loss = loss + float(settings["mask_penalty"]) * mask.sum()
                loss.backward()
                optimizer.step()
            with torch.no_grad():
                mask = torch.sigmoid(mask_raw).detach()
                trigger = (low + (high - low) * torch.sigmoid(trigger_raw)).detach()
                mask_norm = float(mask.sum())
            mask_norms.append(mask_norm)
            if best is None or mask_norm < best[0]:
                best = (mask_norm, target, mask, trigger)
        _, target, mask, trigger = best
        probed = images * (1.0 - mask) + trigger * mask
        genuine_scores = []
        for update in stacked:
            candidate = copy.deepcopy(model)
            apply_update(candidate, update, server_lr=1.0)
            candidate = candidate.to(device).eval()
            with torch.no_grad():
                attack_success = float((candidate(probed).argmax(dim=1) == target).float().mean())
            genuine_scores.append(1.0 - attack_success)
        scores = torch.tensor(genuine_scores, dtype=torch.float32)
        if float(scores.sum()) <= 1e-12:
            normalized = torch.full_like(scores, 1.0 / len(scores))
        else:
            normalized = scores / scores.sum()
        combined = (stacked * normalized.view(-1, 1)).sum(dim=0)
        return AggregationResult(
            update=combined,
            weights=normalized,
            suspicion=1.0 - scores,
            reliability=float(scores.mean()),
            anomaly_mass=float((1.0 - scores).mean()),
            metadata={
                "mode": "hierarchical_fedgame_defender_adaptation",
                "reconstructed_target": target,
                "mask_norms": mask_norms,
                "genuine_scores": genuine_scores,
                "reconstruction_steps": steps,
            },
        )
