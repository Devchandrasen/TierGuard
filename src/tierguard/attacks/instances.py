"""Method-independent, reproducible attack instances for the new study."""

from __future__ import annotations

import copy
import hashlib
import random


INSTANCE_ATTACKS = {
    "unknown_patch_model_replacement",
    "distributed_backdoor",
    "defence_aware_optimized_trigger",
}


def resolve_attack_instance(config: dict) -> dict:
    """Resolve a hidden attack target/location without consulting a defence.

    The instance key intentionally excludes the aggregation method, so every
    method in a paired dataset/attack/seed cell receives the same attack.
    Only the attack generator and evaluation code consume these fields.
    """
    attack = config.get("attack", {})
    if attack.get("instance_mode") != "deterministic":
        return config
    name = str(attack.get("name", "none"))
    if name not in INSTANCE_ATTACKS:
        raise ValueError(f"Deterministic attack instances are unsupported for {name}")
    dataset = str(config["data"]["dataset"]).lower()
    if dataset not in {"mnist", "fashionmnist", "cifar10"}:
        raise ValueError(f"Unknown image geometry for {dataset}")
    seed = int(config["experiment"]["seed"])
    namespace = str(attack.get("instance_namespace", "tierguard2-draft-v1"))
    key = f"{namespace}|{dataset}|{name}|{seed}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    rng = random.Random(int(digest, 16))
    size = int(attack.get("trigger_size", 3))
    side = 32 if dataset == "cifar10" else 28
    if not 1 <= size <= side:
        raise ValueError("trigger_size exceeds dataset image geometry")
    resolved = copy.deepcopy(config)
    resolved_attack = resolved["attack"]
    resolved_attack["target_label"] = rng.randrange(10)
    if name != "distributed_backdoor":
        # The prespecified threat family is the auditor's nine-location
        # bounded search space. The chosen location is not given to it.
        positions = (0, (side - size) // 2, side - size)
        resolved_attack["trigger_top"] = rng.choice(positions)
        resolved_attack["trigger_left"] = rng.choice(positions)
    resolved_attack["instance_sha256"] = digest
    return resolved
