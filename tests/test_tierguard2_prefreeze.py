from __future__ import annotations

from scripts.verify_tierguard2_preflight import verify_frozen_evidence


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
