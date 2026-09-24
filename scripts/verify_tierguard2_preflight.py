"""Fail closed until the TierGuard 2 protocol is genuinely frozen."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

import yaml

from tierguard.aggregators import build_aggregator
from tierguard.tierguard2_protocol import verify_tierguard2_environment


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inside_repo(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Evidence path escapes repository: {name}")
    return path


def _required_frozen_paths(root: Path) -> set[str]:
    paths = list((root / "src" / "tierguard").rglob("*.py"))
    paths += list((root / "configs" / "tierguard2").rglob("*.yaml"))
    paths += list((root / "scripts").glob("*.py"))
    paths += list((root / "scripts").glob("*.pbs"))
    paths += [root / name for name in (
        "configs/base.yaml", "pyproject.toml", ".python-version-tierguard2",
        "requirements-tierguard2-cu128.txt", "requirements-lock-cu128.txt",
    )]
    return {path.relative_to(root).as_posix() for path in paths if path.is_file()}


def verify_frozen_evidence(config: dict, root: Path) -> list[str]:
    """Require an immutable Git tag, hash manifest and evidence for each gate."""
    errors: list[str] = []
    manifest_name = config.get("freeze_manifest")
    freeze_tag = config.get("freeze_tag")
    gate_artifacts = config.get("gate_artifacts", {})
    if not isinstance(manifest_name, str) or not manifest_name:
        errors.append("missing freeze_manifest")
    else:
        try:
            manifest = _inside_repo(root, manifest_name)
            if not manifest.is_file():
                errors.append(f"missing freeze manifest: {manifest_name}")
            else:
                recorded: dict[str, str] = {}
                for line in manifest.read_text(encoding="utf-8").splitlines():
                    if not line.strip() or line.startswith("#"):
                        continue
                    digest, separator, name = line.partition("  ")
                    if (not separator or len(digest) != 64 or
                            any(char not in "0123456789abcdef" for char in digest)):
                        errors.append("malformed freeze manifest line")
                        continue
                    if name in recorded:
                        errors.append(f"duplicate freeze manifest entry: {name}")
                    recorded[name] = digest
                for name in sorted(_required_frozen_paths(root) - recorded.keys()):
                    errors.append(f"unfrozen source/configuration: {name}")
                for name, digest in recorded.items():
                    try:
                        path = _inside_repo(root, name)
                    except ValueError as exc:
                        errors.append(str(exc))
                        continue
                    if not path.is_file() or _sha256(path) != digest:
                        errors.append(f"freeze hash mismatch: {name}")
        except ValueError as exc:
            errors.append(str(exc))

    required_gates = config.get("preconfirmation_gates", [])
    if not isinstance(gate_artifacts, dict):
        errors.append("gate_artifacts must map every gate to a hashed evidence file")
        gate_artifacts = {}
    for gate in required_gates:
        record = gate_artifacts.get(gate)
        if not isinstance(record, dict) or not record.get("path") or not record.get("sha256"):
            errors.append(f"missing hashed evidence for gate: {gate}")
            continue
        try:
            path = _inside_repo(root, str(record["path"]))
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not path.is_file() or _sha256(path) != str(record["sha256"]):
            errors.append(f"gate evidence hash mismatch: {gate}")

    if not isinstance(freeze_tag, str) or not freeze_tag:
        errors.append("missing freeze_tag")
    else:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                              capture_output=True, text=True, check=False)
        tagged = subprocess.run(["git", "rev-parse", "-q", "--verify",
                                 f"refs/tags/{freeze_tag}^{{commit}}"], cwd=root,
                                capture_output=True, text=True, check=False)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                               capture_output=True, text=True, check=False)
        if (head.returncode or tagged.returncode or
                head.stdout.strip() != tagged.stdout.strip()):
            errors.append("current commit does not match the declared freeze tag")
        if dirty.returncode or dirty.stdout.strip():
            errors.append("frozen checkout is dirty")
    return errors


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
    root = Path(__file__).resolve().parents[1]
    if config.get("status") == "frozen":
        errors.extend(verify_frozen_evidence(config, root))
    errors.extend(verify_tierguard2_environment(root))
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
