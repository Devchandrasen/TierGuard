from __future__ import annotations

import pytest

from scripts.verify_tierguard2_preflight import verify_frozen_evidence
from scripts.create_cloud_challenge_secret import create_secret
from tierguard.fl.hierarchical_runner import run_experiment


def test_status_string_alone_cannot_release_confirmation(tmp_path):
    protocol = {"preconfirmation_gates": ["all_partitions_and_attack_instances_frozen"]}
    errors = verify_frozen_evidence(protocol, tmp_path)
    assert "missing freeze_manifest" in errors
    assert "missing freeze_tag" in errors
    assert any("missing hashed evidence for gate" in error for error in errors)


def test_frozen_guard_rejects_unhashed_source_and_bad_gate_hash(tmp_path):
    source = tmp_path / "src" / "tierguard" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    manifest = tmp_path / "manifest.txt"
    manifest.write_text("", encoding="utf-8")
    evidence = tmp_path / "evidence.json"
    evidence.write_text("{}\n", encoding="utf-8")
    protocol = {
        "freeze_manifest": "manifest.txt",
        "preconfirmation_gates": ["all_partitions_and_attack_instances_frozen"],
        "gate_artifacts": {
            "all_partitions_and_attack_instances_frozen": {
                "path": "evidence.json", "sha256": "0" * 64,
            },
        },
    }
    errors = verify_frozen_evidence(protocol, tmp_path)
    assert "unfrozen source/configuration: src/tierguard/example.py" in errors
    assert "gate evidence hash mismatch: all_partitions_and_attack_instances_frozen" in errors


def test_frozen_guard_rejects_path_escape(tmp_path):
    protocol = {
        "freeze_manifest": "../outside.txt",
        "preconfirmation_gates": [],
    }
    errors = verify_frozen_evidence(protocol, tmp_path)
    assert any("escapes repository" in error for error in errors)


def test_run_aborts_before_training_without_clean_git_attestation(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "tierguard.fl.hierarchical_runner._run_provenance",
        lambda config, device: {"git_commit": "unavailable", "git_worktree_dirty": None},
    )
    config = {
        "experiment": {"seed": 1, "device": "cpu"},
        "data": {"dataset": "mnist", "synthetic": True},
        "aggregation": {"method": "tierguard2"},
        "attack": {"name": "none"},
        "provenance": {"require_clean_git": True},
    }
    with pytest.raises(ValueError, match="readable, clean Git checkout"):
        run_experiment(config, results_root=tmp_path)


def test_cloud_challenge_key_is_write_once(tmp_path):
    path = tmp_path / "cloud-secret.bin"
    digest = create_secret(path)
    assert len(path.read_bytes()) == 32
    assert len(digest) == 64
    with pytest.raises(FileExistsError):
        create_secret(path)
