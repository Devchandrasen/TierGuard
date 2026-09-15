from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def set_by_dotted_key(config: dict[str, Any], dotted_key: str, value: Any) -> None:
    cursor = config
    parts = dotted_key.split(".")
    for part in parts[:-1]:
        cursor = cursor.setdefault(part, {})
    cursor[parts[-1]] = value


def parse_override(override: str) -> tuple[str, Any]:
    if "=" not in override:
        raise ValueError(f"Override must be key=value, got {override!r}")
    key, raw_value = override.split("=", 1)
    try:
        value = yaml.safe_load(raw_value)
    except yaml.YAMLError:
        value = raw_value
    return key, value


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"YAML config must be a mapping: {path}")
    return loaded


def load_config(config_path: str | Path, overrides: list[str] | None = None) -> dict[str, Any]:
    project_root = Path(__file__).resolve().parents[2]
    base_path = project_root / "configs" / "base.yaml"
    base = load_yaml(base_path) if base_path.exists() else {}
    config = deep_merge(base, load_yaml(config_path))
    for override in overrides or []:
        key, value = parse_override(override)
        set_by_dotted_key(config, key, value)
    return config


def make_run_dir(config: dict[str, Any], root: str | Path = "results") -> Path:
    dataset = config.get("data", {}).get("dataset", "unknown")
    method = config.get("aggregation", {}).get("method", "unknown")
    attack = config.get("attack", {}).get("name", "none")
    alpha = config.get("data", {}).get("dirichlet_alpha", "iid")
    mal = config.get("attack", {}).get("malicious_fraction", 0.0)
    seed = config.get("experiment", {}).get("seed", 0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return (
        Path(root)
        / str(dataset)
        / str(method)
        / str(attack)
        / f"alpha_{alpha}"
        / f"mal_{mal}"
        / f"seed_{seed}"
        / timestamp
    )


def save_resolved_config(config: dict[str, Any], run_dir: str | Path) -> None:
    path = Path(run_dir)
    path.mkdir(parents=True, exist_ok=True)
    with (path / "resolved_config.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)


def save_json(data: dict[str, Any], path: str | Path) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)


@dataclass(frozen=True)
class RunArtifacts:
    run_dir: Path
    metrics_csv: Path
    final_metrics_json: Path
    overhead_json: Path
    privacy_json: Path
    detection_csv: Path
    command_txt: Path
    provenance_json: Path


def artifact_paths(run_dir: str | Path) -> RunArtifacts:
    root = Path(run_dir)
    return RunArtifacts(
        run_dir=root,
        metrics_csv=root / "metrics_per_round.csv",
        final_metrics_json=root / "final_metrics.json",
        overhead_json=root / "overhead.json",
        privacy_json=root / "privacy_accounting.json",
        detection_csv=root / "detection_metrics.csv",
        command_txt=root / "command.txt",
        provenance_json=root / "provenance.json",
    )
