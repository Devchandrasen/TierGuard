from __future__ import annotations

from pathlib import Path

import tierguard


def test_version_is_consistent_across_release_metadata():
    repo_root = Path(__file__).resolve().parents[1]
    version = (repo_root / "VERSION").read_text(encoding="utf-8").strip()
    assert version == "1.0.0.0"
    assert tierguard.__version__ == version
