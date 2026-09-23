"""Fail closed until the TierGuard 2 protocol is genuinely frozen."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from tierguard.aggregators import build_aggregator
from tierguard.tierguard2_protocol import verify_tierguard2_environment


def verify_protocol(path: Path) -> list[str]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    errors = []
    if config.get("status") != "frozen":
        errors.append("protocol is not frozen")
    for method in config["methods_required"]:
        if method == "tierguard2":
            continue  # Dedicated two-level runner, not a legacy BaseAggregator.
        try:
            build_aggregator(method, {}, dimension=2)
        except ValueError:
            errors.append(f"missing baseline implementation: {method}")
    implemented_attacks = {
        "unknown_patch_model_replacement", "distributed_backdoor",
        "defence_aware_optimized_trigger",
    }
    for attack in config["main_attacks_required"]:
        if attack not in implemented_attacks:
            errors.append(f"missing main attack implementation: {attack}")
    if len(config["development_seeds"]) != 3 or len(config["confirmatory_seeds"]) != 12:
        errors.append("incorrect development or confirmatory seed count")
    if set(config["development_seeds"]) & set(config["confirmatory_seeds"]):
        errors.append("development and confirmatory seeds overlap")
    errors.extend(verify_tierguard2_environment(Path(__file__).resolve().parents[1]))
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path,
                        default=Path("configs/tierguard2/protocol_draft.yaml"))
    args = parser.parse_args()
    errors = verify_protocol(args.protocol)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)
    print("TierGuard 2 protocol preflight passed")


if __name__ == "__main__":
    main()
