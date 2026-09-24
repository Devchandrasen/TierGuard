from __future__ import annotations

import json

import pytest
import yaml

from scripts.calibrate_tierguard2 import calibrate


def _development_run(root, seed: int, clip: float = 8.0, dirty: bool = False):
    path = root / f"seed_{seed}"
    path.mkdir()
    config = {
        "experiment": {"name": "tierguard2_clean_development_unfrozen",
                       "seed": seed, "rounds": 40},
        "data": {"dataset": "fashionmnist"},
        "attack": {"name": "none"},
        "aggregation": {"method": "tierguard2"},
        "tierguard2": {"calibrated_gain_threshold": 1.0,
                       "clip_reference_multiplier": clip},
    }
    (path / "resolved_config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    (path / "provenance.json").write_text(json.dumps({
        "git_commit": "a" * 40, "git_worktree_dirty": dirty,
    }), encoding="utf-8")
    (path / "final_metrics.json").write_text(json.dumps({"final_round": 40}),
                                              encoding="utf-8")
    for round_idx in range(1, 41):
        (path / f"audit_round_{round_idx:03d}.json").write_text(json.dumps({
            "client_audits": [{"heldout_target_gain": seed / 100_000}],
            "edge_audits": [{"heldout_target_gain": seed / 100_000}],
        }), encoding="utf-8")
    return path


def test_calibration_requires_one_clean_configuration_and_source(tmp_path):
    paths = [_development_run(tmp_path, seed) for seed in (2001, 2002, 2003)]
    result = calibrate(paths)
    assert result["development_seeds"] == [2001, 2002, 2003]
    assert result["number_of_scores"] == 240
    assert result["git_commit"] == "a" * 40


def test_calibration_rejects_mixed_clip_settings(tmp_path):
    paths = [_development_run(tmp_path, 2001), _development_run(tmp_path, 2002),
             _development_run(tmp_path, 2003, clip=16.0)]
    with pytest.raises(ValueError, match="one configuration"):
        calibrate(paths)


def test_calibration_rejects_dirty_source(tmp_path):
    paths = [_development_run(tmp_path, 2001), _development_run(tmp_path, 2002),
             _development_run(tmp_path, 2003, dirty=True)]
    with pytest.raises(ValueError, match="dirty"):
        calibrate(paths)
