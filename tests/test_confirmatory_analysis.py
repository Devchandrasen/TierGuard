from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from scripts.analyze_confirmatory import (
    _exact_sign_flip_paired_pvalue,
    _holm_adjust,
    _read_runs,
)
from scripts.run_confirmatory import _load_matrix, _tasks, _write_status
from tierguard.fl.hierarchical_runner import HIERARCHICAL_METHODS


def test_exact_sign_flip_test_has_six_seed_resolution():
    differences = np.ones(6)
    assert _exact_sign_flip_paired_pvalue(differences) == 0.03125


def test_holm_adjustment_is_monotone_and_familywise():
    raw = pd.Series([0.01, 0.03, 0.20, 0.80])
    adjusted = _holm_adjust(raw)
    assert np.allclose(adjusted.to_numpy(), [0.04, 0.09, 0.40, 0.80])


def test_frozen_matrix_expands_to_180_matched_hierarchical_runs():
    repo_root = Path(__file__).resolve().parents[1]
    matrix = _load_matrix(repo_root / "configs" / "confirmatory_v1" / "matrix.yaml")
    tasks = _tasks(matrix, "cpu")
    assert len(tasks) == 180
    assert len(set(matrix["seeds"])) == 6
    assert set(matrix["methods"]).issubset(HIERARCHICAL_METHODS)
    assert {task["device"] for task in tasks} == {"cpu"}


def test_frozen_matrix_rejects_a_device_override():
    repo_root = Path(__file__).resolve().parents[1]
    matrix = _load_matrix(repo_root / "configs" / "confirmatory_v1" / "matrix.yaml")
    with pytest.raises(ValueError, match="requires device=cpu"):
        _tasks(matrix, "cuda")


def test_partial_preflight_status_is_not_a_complete_campaign(tmp_path):
    status_path = tmp_path / "CAMPAIGN_STATUS.json"
    _write_status(status_path, protocol_total=180, scheduled_total=1, completed=["DONE"], failures=[])
    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert status["scheduled_tasks"] == 1
    assert status["complete"] is False


@pytest.mark.parametrize(
    "payload",
    [
        {"frozen": False, "seeds": [1, 2, 3, 4, 5]},
        {"frozen": True, "seeds": [1, 2, 3, 4]},
    ],
)
def test_confirmatory_matrix_rejects_unfrozen_or_too_few_seeds(tmp_path, payload):
    path = tmp_path / "matrix.yaml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        _load_matrix(path)


def test_run_reader_reports_corrupt_json_instead_of_crashing(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "final_metrics.json").write_text("{", encoding="utf-8")
    (run_dir / "provenance.json").write_text(json.dumps({}), encoding="utf-8")
    (run_dir / "resolved_config.yaml").write_text("experiment: {}\n", encoding="utf-8")
    frame, errors = _read_runs(tmp_path, "tierguard-confirmatory-v1", "unused")
    assert frame.empty
    assert len(errors) == 1
    assert errors[0].startswith("unreadable run directory:")
