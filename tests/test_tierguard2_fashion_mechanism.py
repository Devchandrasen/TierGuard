from __future__ import annotations
import copy
import csv
import json
from pathlib import Path

import pytest
import torch
import yaml

from scripts.fashion_mechanism_common import cells, cell_config, cell_results, canonical_hash, digest
from scripts.index_tierguard2_fashion_mechanism import index_runs
from scripts.submit_tierguard2_fashion_mechanism_one_job import check_ledger
from tierguard.aggregators.tierguard2 import AuditResult, applied_risks, weighting_enabled
from tierguard.fl.client import ClientUpdate
from tierguard.fl.hierarchical_runner import _aggregate_tierguard2
from tierguard.security.edge_receipts import ReceiptAuthority

def manifest():
    return {"phase": "fashion_mechanism_v1", "cells": cells(),
            "config_hashes": {cell["id"]: canonical_hash(cell_config(cell)) for cell in cells()},
            "source_files": {}, "source_commit": "a" * 40,
            "environment_lock_sha256": "b" * 64, "python_version": "3.12.13",
            "provenance_packages": {"torch": "2.11.0+cu128"}, "partition_hashes": {}}

def write(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")

def fixture_run(root, frozen, cell=None):
    cell = cell or cells()[0]
    folder = cell_results(root, cell) / "attempt"
    folder.mkdir(parents=True)
    cfg = cell_config(cell)
    (folder / "resolved_config.yaml").write_text(yaml.safe_dump(cfg))
    write(folder / "partition_indices.json", {"fixture": True})
    frozen["partition_hashes"][str(cell["seed"])] = digest(folder / "partition_indices.json")
    write(folder / "provenance.json", {
        "git_commit": frozen["source_commit"], "git_worktree_dirty": False,
        "config_sha256": canonical_hash(cfg), "environment_lock_sha256": frozen["environment_lock_sha256"],
        "device": "cuda", "python": "3.12.13 (fixture)", "torch_num_threads": 2,
        "packages": frozen["provenance_packages"], "pbs_job_id": "1.mgmt01",
    })
    final = {"final_round": 40, "stability_failures": 0, "seed": cell["seed"],
             "method": cfg["aggregation"]["method"], "attack": cell["attack"],
             "dataset": "fashionmnist", "experiment_name": "tierguard2_fashion_mechanism_v1",
             "git_commit": frozen["source_commit"], "config_sha256": canonical_hash(cfg),
             "clean_accuracy": 0.8, "macro_f1": 0.79, "attack_success_rate": None}
    write(folder / "final_metrics.json", final)
    with (folder / "metrics_per_round.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["round", "stability_failures", "clean_accuracy", "macro_f1", "asr"])
        writer.writeheader()
        writer.writerows({"round": n, "stability_failures": 0, "clean_accuracy": 0.8,
                          "macro_f1": 0.79, "asr": ""} for n in range(1, 41))
    audit = {"expected_edge_reports": 6, "received_edge_reports": 6,
             "challenged_edges": [0, 1, 2], "rejected_edges": [], "missing_edge_reports": [],
             "client_edge_update_bytes": 1, "client_cloud_receipt_bytes": 1,
             "edge_cloud_report_bytes": 1, "challenge_raw_upload_bytes": 1}
    if cfg["aggregation"]["method"] == "tierguard2":
        audit.update(clip_radius=1.0, edge_minus_client_risk=[0.0] * 6)
        for level, size in (("client", 30), ("edge", 6)):
            enabled = cfg["tierguard2"][f"{level}_risk_weighting"]
            audit[f"{level}_risk_weighting"] = enabled
            audit[f"{level}_audits"] = [{"risk": 0.2, "heldout_target_gain": 0.3,
                                         "clean_loss_change": 0.1} for _ in range(size)]
            audit[f"{level}_applied_risks"] = [0.2 if enabled else 0.0] * size
    for n in range(1, 41):
        write(folder / f"audit_round_{n:03d}.json", audit)
    write(folder / "attack_assignment.json", {"malicious_client_ids": [], "distributed_components": {}})
    return folder

def test_bounded_matrix_has_exactly_96_unique_paired_cells():
    assert len(cells()) == len({c["id"] for c in cells()}) == 96
    assert {c["seed"] for c in cells()} == {2001, 2002, 2003}
    for attack in {cell["attack"] for cell in cells()} - {"none"}:
        for seed in (2001, 2002, 2003):
            configs = [cell_config(c) for c in cells() if c["attack"] == attack and c["seed"] == seed]
            assert len({cfg["attack"]["instance_sha256"] for cfg in configs}) == 1
            assert all(cfg["data"] == configs[0]["data"] and cfg["federated"] == configs[0]["federated"]
                       for cfg in configs)
    with pytest.raises(ValueError):
        cell_config({**cells()[0], "seed": 3001})

def test_ablation_settings_validate_boolean_and_preserve_default():
    assert applied_risks([0.2], {}, "client") == [0.2]
    assert applied_risks([0.2], {"client_risk_weighting": False}, "client") == [0.0]
    with pytest.raises(ValueError):
        weighting_enabled({"client_risk_weighting": "false"}, "client")
    with pytest.raises(ValueError):
        weighting_enabled({}, "cloud")

@pytest.mark.parametrize("client_enabled,edge_enabled", [(True, True), (True, False), (False, True), (False, False)])
def test_ablation_recomputes_authenticated_edges_consistently(monkeypatch, client_enabled, edge_enabled):
    monkeypatch.setattr("tierguard.fl.hierarchical_runner.choose_challenges",
                        lambda reports: {report.edge_id for report in reports})
    class Auditor:
        profile_records = []
        def audit(self, model, update, server_lr, level):
            risk = max(0.0, float(update[0]))
            return AuditResult(risk, risk, 0.0, "fixture", 1)
    clients = [ClientUpdate(client_id=i, edge_id=i // 2, update=torch.tensor([v]),
                             num_samples=10, malicious=False, local_loss=0.0, local_accuracy=0.0)
               for i, v in enumerate((0.0, 0.2, 0.6, 0.8))]
    settings = {"clip_floor": 1.0, "client_risk_weighting": client_enabled,
                "edge_risk_weighting": edge_enabled, "risk_gamma": 8.0}
    cfg = {"tierguard2": settings, "federated": {"server_lr": 1.0}}
    update, metadata, _ = _aggregate_tierguard2(
        clients, torch.nn.Linear(1, 1, bias=False), Auditor(), torch.tensor([1.0]),
        cfg, ReceiptAuthority(list(range(4))), 1)
    audit = metadata["aggregation_metadata"]
    assert audit["rejected_edges"] == []
    assert audit["client_applied_risks"] == (audit["client_risks"] if client_enabled else [0.0] * 4)
    assert audit["edge_applied_risks"] == (audit["edge_risks"] if edge_enabled else [0.0] * 2)
    if not client_enabled and not edge_enabled:
        assert float(update) == pytest.approx(0.4)
    else:
        assert float(update) < 0.4

def test_partial_index_accepts_only_unattempted_missing_cells(tmp_path):
    frozen = manifest()
    assert index_runs(tmp_path, frozen)["valid_partial"]
    folder = fixture_run(tmp_path, frozen)
    result = index_runs(tmp_path, frozen)
    assert result["valid_partial"] and not result["complete"] and result["observed_run_count"] == 1
    (folder / "final_metrics.json").unlink()
    assert not index_runs(tmp_path, frozen)["valid_partial"]

@pytest.mark.parametrize("failure", ["nan", "dirty", "config", "partition", "audit", "duplicate", "unknown"])
def test_index_rejects_invalid_evidence(tmp_path, failure):
    frozen = manifest()
    folder = fixture_run(tmp_path, frozen)
    if failure == "nan":
        data = json.loads((folder / "final_metrics.json").read_text())
        data["clean_accuracy"] = float("nan")
        write(folder / "final_metrics.json", data)
    elif failure == "dirty":
        data = json.loads((folder / "provenance.json").read_text())
        data["git_worktree_dirty"] = True
        write(folder / "provenance.json", data)
    elif failure == "config":
        cfg = yaml.safe_load((folder / "resolved_config.yaml").read_text())
        cfg["federated"]["client_lr"] = 0.1
        (folder / "resolved_config.yaml").write_text(yaml.safe_dump(cfg))
    elif failure == "partition":
        write(folder / "partition_indices.json", {"changed": True})
    elif failure == "audit":
        (folder / "audit_round_040.json").unlink()
    elif failure == "duplicate":
        (folder.parent / "other_attempt").mkdir()
    else:
        (tmp_path / "unexpected_file.json").write_text("{}")
    assert not index_runs(tmp_path, frozen)["valid_partial"]

def test_index_verifies_ablation_applied_risks(tmp_path):
    frozen = manifest()
    cell = next(c for c in cells() if c["variant"] == "clip_only" and c["attack"] == "none")
    folder = fixture_run(tmp_path, frozen, cell)
    assert index_runs(tmp_path, frozen)["valid_partial"]
    audit = json.loads((folder / "audit_round_001.json").read_text())
    audit["client_applied_risks"][0] = 0.2
    write(folder / "audit_round_001.json", audit)
    assert not index_runs(tmp_path, frozen)["valid_partial"]

def test_ledger_stops_ambiguous_duplicate_and_unrecorded_attempts():
    index = {"valid_partial": True, "errors": [], "runs": []}
    assert check_ledger([], index) == []
    intent = {"mode": "submission_intent", "cell": cells()[0]}
    done = {**intent, "mode": "submitted", "job_id": "1.mgmt01"}
    with pytest.raises(ValueError, match="ambiguous"):
        check_ledger([intent], index)
    with pytest.raises(ValueError, match="ledger/results"):
        check_ledger([intent, done], index)
    index["runs"] = [{"id": cells()[0]["id"], "job_id": "1.mgmt01"}]
    assert check_ledger([intent, done], index) == [done]
    with pytest.raises(ValueError, match="duplicate"):
        check_ledger([intent, done, intent, done], index)
    index["runs"][0]["job_id"] = "2.mgmt01"
    with pytest.raises(ValueError, match="different scheduler"):
        check_ledger([intent, done], index)


@pytest.mark.parametrize("variant", ["median", "fltrust", "rfa", "clip_only", "client_only", "cloud_only", "full", "fedavg"])
def test_all_variants_synthetic_pipeline_and_receipt_smoke(tmp_path, variant):
    from tierguard.fl.hierarchical_runner import run_experiment
    cell = next(c for c in cells() if c["variant"] == variant and c["attack"] == "none")
    cfg = cell_config(cell)
    cfg["experiment"].update(device="cpu", rounds=1, eval_every=1)
    cfg["federated"].update(num_clients=10, num_edges=2, clients_per_round=4,
                             clients_per_edge_per_round=2, local_epochs=1, batch_size=10)
    cfg["data"].update(synthetic=True, train_size=100, test_size=30, iid=True,
                      root_dataset_size=20, audit_search_size=10, audit_eval_size=10)
    cfg["tierguard2"]["probes_per_class"] = 1
    cfg["provenance"]["require_clean_git"] = False
    folder = run_experiment(cfg, results_root=tmp_path)
    final = json.loads((folder / "final_metrics.json").read_text())
    audit = json.loads((folder / "audit_round_001.json").read_text())
    assert final["stability_failures"] == 0 and final["attack_success_rate"] is None
    assert audit["rejected_edges"] == [] and audit["expected_edge_reports"] == 2
