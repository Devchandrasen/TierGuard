from __future__ import annotations

import torch

from .adaptive import adaptive_tierguard_update
from .alie import alie_attack as alie_attack
from .gaussian import gaussian_attack
from .model_replacement import model_replacement
from .sign_flip import sign_flip
from .sybil import make_sybil_updates as make_sybil_updates


POST_UPDATE_ATTACKS = {
    "sign_flip",
    "gaussian",
    "alie",
    "model_replacement",
    "backdoor_model_replacement",
    "sybil_backdoor",
    "adaptive_tierguard_aware",
    "unknown_patch_model_replacement",
    "defence_aware_optimized_trigger",
}


def apply_post_update_attack(
    name: str,
    update: torch.Tensor,
    config: dict,
    num_malicious_selected: int = 1,
    reference_update: torch.Tensor | None = None,
) -> torch.Tensor:
    key = name.lower()
    if key == "sign_flip":
        return sign_flip(update, scale=float(config.get("scale", 1.0)))
    if key == "gaussian":
        return gaussian_attack(update, sigma=float(config.get("sigma", 1.0)))
    if key in {"model_replacement", "backdoor_model_replacement", "sybil_backdoor",
               "unknown_patch_model_replacement", "defence_aware_optimized_trigger"}:
        scale = config.get("scale_factor")
        if scale is None:
            scale = float(config.get("clients_per_round", 1)) / max(1, num_malicious_selected)
        return model_replacement(update, float(scale))
    if key == "adaptive_tierguard_aware":
        if reference_update is None:
            return update
        return adaptive_tierguard_update(
            update,
            reference_update,
            norm_bound=float(config.get("adaptive_norm_bound", config.get("clipping_norm", 5.0))),
        )
    return update
