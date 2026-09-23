"""New-study environment verification without altering the v1 freeze."""

from __future__ import annotations

import importlib.metadata
import platform
from pathlib import Path

from tierguard.protocol import locked_requirements


def tierguard2_pins(repo_root: str | Path) -> dict[str, str]:
    root = Path(repo_root)
    pins = locked_requirements(root)
    for line in (root / "requirements-tierguard2-cu128.txt").read_text(
        encoding="utf-8"
    ).splitlines():
        line = line.strip()
        if (not line or line.startswith("#")
                or line.startswith(("-r ", "--extra-index-url ", "--index-url "))):
            continue
        if "==" not in line:
            raise ValueError(f"Unpinned TierGuard 2 requirement: {line}")
        name, version = line.split("==", 1)
        pins[name] = version
    return pins


def verify_tierguard2_environment(repo_root: str | Path) -> list[str]:
    root = Path(repo_root)
    errors = []
    expected_python = (root / ".python-version-tierguard2").read_text(encoding="utf-8").strip()
    if platform.python_version() != expected_python:
        errors.append(f"Python mismatch: expected {expected_python}, observed {platform.python_version()}")
    for package, expected in tierguard2_pins(root).items():
        try:
            actual = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            actual = "unavailable"
        if actual != expected:
            errors.append(f"package mismatch: {package} expected {expected}, observed {actual}")
    return errors
