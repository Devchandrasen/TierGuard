"""Fixed, bounded development matrix; no scheduler calls or parameter tuning."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tierguard.attacks.instances import resolve_attack_instance
from tierguard.config import load_config

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/tierguard2/fashion_mechanism_v1.yaml"
SEEDS = (2001, 2002, 2003)
ATTACKS = ("none", "unknown_patch_model_replacement", "distributed_backdoor",
           "defence_aware_optimized_trigger")
VARIANTS = {
    "median": ("hfl_median", True, True),
    "fltrust": ("hfl_fltrust", True, True),
    "rfa": ("hfl_rfa", True, True),
    "clip_only": ("tierguard2", False, False),
    "client_only": ("tierguard2", True, False),
    "cloud_only": ("tierguard2", False, True),
    "full": ("tierguard2", True, True),
    "fedavg": ("hfl_fedavg", True, True),
}

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonical_hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     default=str).encode()).hexdigest()

def cells() -> list[dict]:
    return [{"variant": variant, "attack": attack, "seed": seed,
             "id": f"{variant}__{attack}__{seed}"}
            for variant in VARIANTS for attack in ATTACKS for seed in SEEDS]

def cell_config(cell: dict) -> dict:
    if cell not in cells():
        raise ValueError("Cell is outside the bounded development matrix")
    method, client, edge = VARIANTS[cell["variant"]]
    config = load_config(CONFIG)
    config["experiment"]["seed"] = cell["seed"]
    config["aggregation"]["method"] = method
    config["attack"].update(name=cell["attack"],
                            malicious_fraction=0.0 if cell["attack"] == "none" else 0.2,
                            instance_mode="fixed" if cell["attack"] == "none" else "deterministic")
    config["tierguard2"].update(client_risk_weighting=client, edge_risk_weighting=edge)
    config["development"] = {"phase": "fashion_mechanism_v1", "variant": cell["variant"],
                             "cell_id": cell["id"]}
    return resolve_attack_instance(config)

def cell_results(root: Path, cell: dict) -> Path:
    config = cell_config(cell)
    return (root / cell["variant"] / "fashionmnist" / config["aggregation"]["method"]
            / cell["attack"] / "alpha_0.3" / f"mal_{config['attack']['malicious_fraction']}"
            / f"seed_{cell['seed']}")

def check_manifest(manifest: dict) -> None:
    if manifest.get("phase") != "fashion_mechanism_v1" or manifest.get("cells") != cells():
        raise ValueError("Unexpected bounded phase or cell order")
    expected = {cell["id"]: canonical_hash(cell_config(cell)) for cell in cells()}
    if manifest.get("config_hashes") != expected:
        raise ValueError("Frozen resolved configuration changed")
    for relative, expected_hash in manifest["source_files"].items():
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT.resolve()) or digest(path) != expected_hash:
            raise ValueError(f"Frozen source changed: {relative}")
