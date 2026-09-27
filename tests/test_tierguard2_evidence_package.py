import pytest

from scripts.package_tierguard2_development_evidence import REMOTE_ROOT, local_path, validate


def test_evidence_mapper_keeps_remote_records_within_snapshot(tmp_path):
    remote = REMOTE_ROOT + "project_t2_attack_dev/results/example/final_metrics.json"
    assert local_path(tmp_path, remote) == (
        tmp_path / "raw/project_t2_attack_dev/results/example/final_metrics.json"
    )
    with pytest.raises(ValueError, match="outside evidence scope"):
        local_path(tmp_path, REMOTE_ROOT + "project_t2_attack_dev/../../secret")
    with pytest.raises(ValueError, match="Unexpected remote path"):
        local_path(tmp_path, "/elsewhere/results.json")


def test_empty_snapshot_cannot_pass(tmp_path):
    result = validate(tmp_path)
    assert not result["snapshot_integrity_passed"]
    assert result["run_count"] == 0
    assert result["confirmatory_runs"] == 0
    assert len(result["errors"]) == 4
