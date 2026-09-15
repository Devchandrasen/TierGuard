from __future__ import annotations

from pathlib import Path

from tierguard.protocol import (
    locked_requirements,
    verify_frozen_manifest,
    verify_runtime_environment,
    write_frozen_manifest,
)


def test_frozen_manifest_detects_changes(tmp_path: Path):
    source = tmp_path / "src" / "tierguard" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    config = tmp_path / "configs" / "confirmatory_v1" / "matrix.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("frozen: true\n", encoding="utf-8")

    write_frozen_manifest(tmp_path)
    ok, errors = verify_frozen_manifest(tmp_path)
    assert ok
    assert errors == []

    source.write_text("VALUE = 2\n", encoding="utf-8")
    ok, errors = verify_frozen_manifest(tmp_path)
    assert not ok
    assert errors == ["hash mismatch: src/tierguard/example.py"]


def test_release_environment_matches_every_exact_lock_pin():
    repo_root = Path(__file__).resolve().parents[1]
    pins = locked_requirements(repo_root)
    assert pins["torch"].endswith("+cu128")
    assert len(pins) >= 40
    ok, errors = verify_runtime_environment(repo_root)
    assert ok, errors
