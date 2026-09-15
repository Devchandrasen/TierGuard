from __future__ import annotations

import hashlib
import importlib.metadata
import platform
from pathlib import Path


MANIFEST_NAME = "FROZEN_SHA256SUMS"
LOCK_NAME = "requirements-lock-cu128.txt"


def frozen_protocol_files(repo_root: str | Path) -> list[Path]:
    root = Path(repo_root).resolve()
    files: set[Path] = set()
    for pattern in (
        "src/tierguard/**/*.py",
        "tests/**/*.py",
        "configs/confirmatory_v1/*.yaml",
        "configs/base.yaml",
        "scripts/freeze_protocol.py",
        "scripts/run_confirmatory.py",
        "scripts/analyze_confirmatory.py",
        "scripts/__init__.py",
        "pyproject.toml",
        "requirements-lock-cu128.txt",
        ".python-version",
        ".gitattributes",
        "VERSION",
    ):
        files.update(path for path in root.glob(pattern) if path.is_file())
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_path(repo_root: str | Path) -> Path:
    return Path(repo_root).resolve() / "configs" / "confirmatory_v1" / MANIFEST_NAME


def write_frozen_manifest(repo_root: str | Path) -> Path:
    root = Path(repo_root).resolve()
    output = manifest_path(root)
    lines = [
        f"{sha256_file(path)}  {path.relative_to(root).as_posix()}"
        for path in frozen_protocol_files(root)
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return output


def verify_frozen_manifest(repo_root: str | Path) -> tuple[bool, list[str]]:
    root = Path(repo_root).resolve()
    path = manifest_path(root)
    if not path.exists():
        return False, [f"missing manifest: {path}"]
    errors: list[str] = []
    listed: set[str] = set()
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        try:
            expected, relative = raw_line.split("  ", 1)
        except ValueError:
            errors.append(f"line {line_number}: malformed manifest entry")
            continue
        listed.add(relative)
        candidate = root / Path(relative)
        if not candidate.is_file():
            errors.append(f"missing: {relative}")
            continue
        actual = sha256_file(candidate)
        if actual != expected:
            errors.append(f"hash mismatch: {relative}")
    current = {path.relative_to(root).as_posix() for path in frozen_protocol_files(root)}
    for relative in sorted(current - listed):
        errors.append(f"unfrozen protocol file: {relative}")
    for relative in sorted(listed - current):
        errors.append(f"manifest references non-protocol file: {relative}")
    return not errors, errors


def frozen_manifest_sha256(repo_root: str | Path) -> str:
    return sha256_file(manifest_path(repo_root))


def locked_requirements(repo_root: str | Path) -> dict[str, str]:
    lock_path = Path(repo_root).resolve() / LOCK_NAME
    pins: dict[str, str] = {}
    for line_number, raw_line in enumerate(lock_path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith(("#", "--")):
            continue
        if "==" not in line:
            raise ValueError(f"{LOCK_NAME}:{line_number}: dependency is not exactly pinned")
        name, version = line.split("==", 1)
        if not name or not version:
            raise ValueError(f"{LOCK_NAME}:{line_number}: malformed exact pin")
        pins[name] = version
    if not pins:
        raise ValueError(f"{LOCK_NAME}: no dependency pins found")
    return pins


def verify_runtime_environment(repo_root: str | Path) -> tuple[bool, list[str]]:
    root = Path(repo_root).resolve()
    errors: list[str] = []
    expected_python = (root / ".python-version").read_text(encoding="utf-8").strip()
    actual_python = platform.python_version()
    if actual_python != expected_python:
        errors.append(f"Python mismatch: expected {expected_python}, observed {actual_python}")
    for package, expected in locked_requirements(root).items():
        try:
            actual = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            errors.append(f"missing package: {package}=={expected}")
            continue
        if actual != expected:
            errors.append(f"package mismatch: {package} expected {expected}, observed {actual}")
    return not errors, errors
