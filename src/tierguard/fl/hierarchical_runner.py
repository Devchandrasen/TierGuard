from __future__ import annotations

import json
import math
import hashlib
import importlib.metadata
import os
import platform
import random
import subprocess
import sys
import time
import copy
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.nn import functional as F

from tierguard.aggregators import build_aggregator
from tierguard.aggregators.fedavg import FedAvgAggregator
from tierguard.aggregators.tierguard2 import CounterfactualAuditor, aggregate_level, continuous_weight
from tierguard.attacks import apply_post_update_attack
from tierguard.attacks.instances import resolve_attack_instance
from tierguard.attacks.alie import alie_attack
from tierguard.attacks.optimized_trigger import optimize_trigger
from tierguard.config import artifact_paths, make_run_dir, save_json, save_resolved_config
from tierguard.data.backdoor import BackdoorDataset, add_bottom_right_square
from tierguard.data.datasets import make_data_bundle
from tierguard.data.partition import client_to_edge
from tierguard.fl.client import ClientUpdate, FederatedClient
from tierguard.fl.local_training import compute_reference_update
from tierguard.fl.update_utils import apply_update, flatten_model
from tierguard.metrics.attack_metrics import attack_success_rate
from tierguard.metrics.classification import evaluate_classifier
from tierguard.metrics.detection import detection_scores
from tierguard.metrics.overhead import bytes_to_mb
from tierguard.models import build_model
from tierguard.privacy.clipping import clip_update
from tierguard.privacy.gaussian_noise import add_gaussian_noise
from tierguard.privacy.privacy_budget import privacy_accounting
from tierguard.protocol import locked_requirements
from tierguard.security.comm_cost import threshold_comm_cost
from tierguard.security.edge_receipts import (
    ReceiptAuthority,
    choose_challenges,
    commit_edge,
    update_digest,
    verify_challenged_report,
    single_report_escape_probability,
)
from tierguard.seed import seed_everything


HIERARCHICAL_METHODS = {
    "hfl_fedavg",
    "hfl_fltrust",
    "hfl_flame",
    "hfl_fedgame",
    "hfl_hflmnd",
    "hfl_trimmed_mean",
    "hfl_rfa",
    "hfl_median",
    "tierguard",
    "tierguard2",
    "shield_like",
    "shield_like_reimplementation",
    "roppfl_like",
    "roppfl_like_reimplementation",
    "tapfed_sim",
    "brea_sim",
}


def _choose_study_challenges(reports, config: dict, round_idx: int) -> set[int]:
    secret_path = config.get("security", {}).get("challenge_secret_path")
    if not secret_path:
        return choose_challenges(reports)
    secret = Path(secret_path).read_bytes()
    context = (
        f"tierguard2|{config['data']['dataset']}|"
        f"{int(config['experiment']['seed'])}|{int(round_idx)}"
    )
    return choose_challenges(reports, secret=secret, context=context)


def _aggregate_tierguard2(client_results, model, auditor, reference_update,
                          config, authority, round_idx):
    """Independent client and edge audits with post-commit receipt challenges."""
    settings = config["tierguard2"]
    radius = max(float(settings.get("clip_floor", 0.1)),
                 float(settings.get("clip_reference_multiplier", 2.0)) *
                 float(torch.linalg.vector_norm(reference_update)))
    client_norms = [float(torch.linalg.vector_norm(item.update)) for item in client_results]
    model_hash = update_digest(flatten_model(model))
    server_lr = float(config["federated"].get("server_lr", 1.0))
    by_edge = {}
    for index, item in enumerate(client_results):
        by_edge.setdefault(item.edge_id, []).append((index, item))
    reports = []
    raw_by_edge = {}
    direct_receipts = {}
    client_risks = [0.0] * len(client_results)
    client_audits = [None] * len(client_results)
    edge_suggested_risks = {}
    for edge_id, indexed in sorted(by_edge.items()):
        updates = [item.update for _, item in indexed]
        masses = [int(item.num_samples) for _, item in indexed]
        local_risks = []
        receipts = []
        for (index, item), update in zip(indexed, updates):
            clipped = clip_update(update, radius)
            result = auditor.audit(model, clipped, server_lr=server_lr)
            client_risks[index] = result.risk
            client_audits[index] = {
                "client_id": item.client_id,
                "risk": result.risk,
                "heldout_target_gain": result.heldout_target_gain,
                "clean_loss_change": result.clean_loss_change,
                "pattern": result.pattern,
                "target_class": result.target_class,
            }
            local_risks.append(result.risk)
            receipts.append(authority.sign(
                round_idx=round_idx, model_hash=model_hash,
                client_id=item.client_id, edge_id=edge_id,
                sample_mass=int(item.num_samples), update=update,
            ))
        aggregate, effective = aggregate_level(updates, masses, local_risks, radius, settings)
        edge_suggested_risks[edge_id] = sum(risk * mass for risk, mass in zip(local_risks, masses)) / sum(masses)
        raw_by_edge[edge_id] = {item.client_id: item.update for _, item in indexed}
        direct_receipts[edge_id] = tuple(receipts)
        reports.append(commit_edge(round_idx, edge_id, aggregate, receipts))

    # The report is committed before the cloud samples challenges.  A
    # compromised edge can alter its aggregate or receipt, but cannot produce
    # valid client signatures for altered raw updates.
    edge_attack = config.get("edge_attack", {})
    if edge_attack.get("name") not in (None, "none"):
        compromised = int(edge_attack["edge_id"])
        for index, report in enumerate(reports):
            if report.edge_id != compromised:
                continue
            if edge_attack["name"] == "aggregate_replacement":
                forged = -float(edge_attack.get("scale", 2.0)) * report.aggregate
                reports[index] = commit_edge(round_idx, compromised, forged, list(report.receipts))
            elif edge_attack["name"] == "report_forgery":
                forged_receipt = copy.copy(report.receipts[0])
                from dataclasses import replace
                forged_receipt = replace(forged_receipt, sample_mass=forged_receipt.sample_mass + 1)
                reports[index] = commit_edge(
                    round_idx, compromised, report.aggregate,
                    [forged_receipt, *report.receipts[1:]],
                )
            else:
                raise ValueError("Unknown edge attack")
    challenged = _choose_study_challenges(reports, config, round_idx)
    verified_bytes = 0
    rejected = set()
    report_lookup = {report.edge_id: report for report in reports}
    for report in reports:
        try:
            if report.receipts != direct_receipts[report.edge_id]:
                raise ValueError("Edge receipt list differs from direct client receipts")
            for receipt in report.receipts:
                authority.verify_signature(receipt, round_idx=round_idx,
                                           model_hash=model_hash, edge_id=report.edge_id)
        except ValueError:
            rejected.add(report.edge_id)
    for edge_id in challenged:
        if edge_id in rejected:
            continue
        report = report_lookup[edge_id]
        verified_bytes += sum(update.numel() * update.element_size()
                              for update in raw_by_edge[edge_id].values())
        def recompute(updates, masses):
            risks = [auditor.audit(model, clip_update(update, radius), server_lr=server_lr).risk
                     for update in updates]
            return aggregate_level(updates, masses, risks, radius, settings)[0]
        try:
            verify_challenged_report(
                report, raw_by_edge[edge_id], authority,
                round_idx=round_idx, model_hash=model_hash, recompute=recompute,
            )
        except ValueError:
            rejected.add(edge_id)

    surviving = [report for report in reports if report.edge_id not in rejected]
    if not surviving:
        raise ValueError("All active edge reports were rejected")
    edge_audits = [auditor.audit(model, clip_update(report.aggregate, radius),
                                 server_lr=server_lr) for report in surviving]
    edge_norms = [float(torch.linalg.vector_norm(report.aggregate)) for report in surviving]
    edge_risks = [item.risk for item in edge_audits]
    edge_masses = [sum(item.sample_mass for item in report.receipts) for report in surviving]
    cloud_update, _ = aggregate_level(
        [report.aggregate for report in surviving], edge_masses, edge_risks, radius, settings
    )
    separation = [risk - edge_suggested_risks[report.edge_id]
                  for report, risk in zip(surviving, edge_risks)]
    metadata = {
        "edge_anomaly_mean": float(np.mean(edge_risks)),
        "edge_anomaly_max": float(np.max(edge_risks)),
        "cloud_reliability_mean": float(np.mean([
            continuous_weight(risk, settings) for risk in edge_risks])),
        "aggregation_metadata": {
            "mode": "two_level_continuous_weighted_mean",
            "clip_radius": radius,
            "client_update_norm_mean": float(np.mean(client_norms)),
            "client_update_norm_max": float(np.max(client_norms)),
            "client_update_clipped_fraction": float(np.mean(
                [norm > radius for norm in client_norms])),
            "edge_aggregate_norm_mean": float(np.mean(edge_norms)),
            "edge_aggregate_clipped_fraction": float(np.mean(
                [norm > radius for norm in edge_norms])),
            "challenged_edges": sorted(challenged),
            "single_report_escape_probability": single_report_escape_probability(len(reports)),
            "rejected_edges": sorted(rejected),
            "challenge_raw_upload_bytes": verified_bytes,
            "client_edge_update_bytes": sum(item.update.numel() * item.update.element_size()
                                            for item in client_results),
            "client_cloud_receipt_bytes": sum(
                len(json.dumps(receipt.__dict__, sort_keys=True).encode("utf-8"))
                for report in reports for receipt in report.receipts
            ),
            "edge_cloud_report_bytes": sum(
                report.aggregate.numel() * report.aggregate.element_size()
                + len(report.commitment.encode("ascii")) for report in reports
            ),
            "edge_minus_client_risk": separation,
            "edge_risks": edge_risks,
            "client_risks": client_risks,
            "client_audits": client_audits,
            "edge_audits": [
                {
                    "edge_id": report.edge_id,
                    "risk": result.risk,
                    "heldout_target_gain": result.heldout_target_gain,
                    "clean_loss_change": result.clean_loss_change,
                    "pattern": result.pattern,
                    "target_class": result.target_class,
                }
                for report, result in zip(surviving, edge_audits)
            ],
            **({"audit_profile": {
                "base_cache_seconds": auditor.begin_round_seconds,
                "sampled_calls": auditor.profile_records,
            }} if auditor.profile_records else {}),
        },
    }
    return cloud_update, metadata, client_risks


def _run_provenance(config: dict, device: torch.device) -> dict:
    project_root = Path(__file__).resolve().parents[3]
    commit = "unavailable"
    dirty = None
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=no"],
                cwd=project_root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    versions = {}
    for package in locked_requirements(project_root):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "unavailable"
    new_study = (
        str(config.get("aggregation", {}).get("method", "")).lower() == "tierguard2"
        or bool(config.get("security", {}).get("edge_challenges", False))
    )
    if new_study:
        for package in ("cryptography", "cffi", "pycparser"):
            try:
                versions[package] = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                versions[package] = "unavailable"
    lock_path = project_root / (
        "requirements-tierguard2-cu128.txt" if new_study else "requirements-lock-cu128.txt"
    )
    challenge_secret_path = config.get("security", {}).get("challenge_secret_path")
    challenge_secret_sha256 = (
        hashlib.sha256(Path(challenge_secret_path).read_bytes()).hexdigest()
        if challenge_secret_path else None
    )
    driver = None
    if device.type == "cuda":
        try:
            queried = subprocess.run(
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                capture_output=True, text=True, check=False,
            )
            if queried.returncode == 0:
                driver = queried.stdout.splitlines()[0].strip()
        except (FileNotFoundError, IndexError):
            pass

    canonical = json.dumps(config, sort_keys=True, separators=(",", ":"), default=str)
    return {
        "git_commit": commit,
        "git_worktree_dirty": dirty,
        "config_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "protocol_manifest_sha256": config.get("provenance", {}).get(
            "protocol_manifest_sha256"
        ),
        "python": sys.version,
        "platform": platform.platform(),
        "hostname": platform.node(),
        "device": str(device),
        "device_name": (
            torch.cuda.get_device_name(device) if device.type == "cuda" else "cpu"
        ),
        "gpu_driver_version": driver,
        "pbs_job_id": os.environ.get("PBS_JOBID"),
        "torch_num_threads": torch.get_num_threads(),
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
        "mkl_num_threads": os.environ.get("MKL_NUM_THREADS"),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_version": torch.version.cuda,
        "cudnn_version": torch.backends.cudnn.version(),
        "packages": versions,
        "environment_lock_sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        "challenge_secret_sha256": challenge_secret_sha256,
    }


def _device_from_config(config: dict) -> torch.device:
    requested = str(config.get("experiment", {}).get("device", "cpu"))
    if requested == "cuda" and not torch.cuda.is_available():
        return torch.device("cpu")
    return torch.device(requested)


def _select_malicious(num_clients: int, fraction: float, seed: int) -> set[int]:
    count = int(round(num_clients * fraction))
    rng = random.Random(seed)
    return set(rng.sample(range(num_clients), count)) if count > 0 else set()


def _selected_clients(num_clients: int, clients_per_round: int, seed: int, round_idx: int) -> list[int]:
    rng = np.random.default_rng(seed + round_idx * 9973)
    count = min(num_clients, clients_per_round)
    return rng.choice(num_clients, size=count, replace=False).tolist()


def _selected_clients_per_edge(edge_mapping: dict[int, list[int]], per_edge: int,
                               seed: int, round_idx: int) -> list[int]:
    if per_edge <= 0:
        raise ValueError("clients_per_edge_per_round must be positive")
    selected = []
    for edge_id, clients in sorted(edge_mapping.items()):
        if len(clients) < per_edge:
            raise ValueError(f"Edge {edge_id} has fewer than {per_edge} clients")
        rng = np.random.default_rng(seed + round_idx * 9973 + edge_id * 104729)
        selected.extend(int(value) for value in rng.choice(clients, size=per_edge, replace=False))
    return selected


def _post_process_attacks(
    results: list[ClientUpdate],
    config: dict,
    reference_update: torch.Tensor | None,
) -> list[ClientUpdate]:
    attack = config.get("attack", {})
    name = str(attack.get("name", "none")).lower()
    malicious = [item for item in results if item.malicious]
    honest = [item for item in results if not item.malicious]
    if name == "alie" and malicious and honest:
        replacement = alie_attack([item.update for item in honest], z=float(attack.get("alie_z", 1.0)))
        for item in malicious:
            item.update = replacement.clone()
        return results
    if name == "sybil_backdoor" and malicious:
        base = malicious[0].update.clone()
        for item in malicious:
            item.update = base + 1e-4 * torch.randn_like(base)

    attack_ext = dict(attack)
    attack_ext["clients_per_round"] = len(results)
    attack_ext["clipping_norm"] = config.get("privacy", {}).get("clipping_norm", 5.0)
    for item in malicious:
        item.update = apply_post_update_attack(
            name,
            item.update,
            attack_ext,
            num_malicious_selected=len(malicious),
            reference_update=reference_update,
        )
    return results


def _apply_privacy(update: torch.Tensor, config: dict) -> torch.Tensor:
    privacy = config.get("privacy", {})
    if not bool(privacy.get("enabled", False)):
        return update
    clipped = clip_update(update, float(privacy.get("clipping_norm", 5.0)))
    return add_gaussian_noise(
        clipped,
        float(privacy.get("clipping_norm", 5.0)),
        float(privacy.get("dp_noise_multiplier", 0.0)),
    )


def _backdoor_audit_multipliers(
    model: torch.nn.Module,
    updates: list[torch.Tensor],
    root_loader,
    config: dict,
    device: torch.device,
) -> tuple[list[float], list[float]]:
    tier_cfg = config.get("tierguard", {})
    if not bool(tier_cfg.get("use_backdoor_audit", False)) or not updates:
        return [1.0 for _ in updates], [0.0 for _ in updates]
    try:
        images, labels = next(iter(root_loader))
    except StopIteration:
        return [1.0 for _ in updates], [0.0 for _ in updates]
    target_label = int(config.get("attack", {}).get("target_label", 0))
    max_items = int(tier_cfg.get("audit_batch_size", 64))
    mask = labels != target_label
    if mask.any():
        images = images[mask]
    images = images[:max_items]
    if images.numel() == 0:
        return [1.0 for _ in updates], [0.0 for _ in updates]
    triggered = add_bottom_right_square(images).to(device)
    model = model.to(device)
    model.eval()
    with torch.no_grad():
        base_probs = F.softmax(model(triggered), dim=1)[:, target_label]
        base_mean = float(base_probs.mean().item())
    gamma = float(tier_cfg.get("audit_gamma", 8.0))
    margin = float(tier_cfg.get("audit_margin", 0.05))
    min_risk = float(tier_cfg.get("audit_min_risk", 0.0))
    weight_floor = float(tier_cfg.get("audit_weight_floor", 0.25))
    server_lr = float(tier_cfg.get("audit_server_lr", config.get("federated", {}).get("server_lr", 1.0)))
    multipliers: list[float] = []
    risks: list[float] = []
    for update in updates:
        candidate = copy.deepcopy(model).to(device)
        apply_update(candidate, update, server_lr=server_lr)
        candidate.eval()
        with torch.no_grad():
            probs = F.softmax(candidate(triggered), dim=1)[:, target_label]
            post_mean = float(probs.mean().item())
        risk = max(0.0, post_mean - base_mean - margin)
        if risk < min_risk:
            risk = 0.0
        risks.append(risk)
        multipliers.append(max(weight_floor, float(math.exp(-gamma * risk))))
    return multipliers, risks


def _aggregate_round(
    client_results: list[ClientUpdate],
    config: dict,
    reference_update: torch.Tensor | None,
    model_dim: int,
    receipt_authority=None,
    round_idx: int | None = None,
    model_hash: str | None = None,
    model: torch.nn.Module | None = None,
    audit_loader=None,
    full_root_loader=None,
    device: torch.device | None = None,
    hflmnd_history: dict[tuple[int, int], int] | None = None,
) -> tuple[torch.Tensor, dict, list[float]]:
    method = str(config.get("aggregation", {}).get("method", "fedavg")).lower()
    aggregator = build_aggregator(method, config, dimension=model_dim)
    selected_ids = [item.client_id for item in client_results]
    sample_weights = [float(item.num_samples) * float(getattr(item, "audit_multiplier", 1.0))
                      for item in client_results]
    updates = [item.update for item in client_results]
    client_suspicion = [0.0 for _ in client_results]

    if method not in HIERARCHICAL_METHODS:
        result = aggregator.aggregate(
            updates,
            weights=sample_weights,
            client_ids=selected_ids,
            reference_update=reference_update,
        )
        if result.suspicion is not None:
            client_suspicion = [float(x) for x in result.suspicion.tolist()]
        client_suspicion = [
            max(score, float(getattr(item, "audit_suspicion", 0.0)))
            for score, item in zip(client_suspicion, client_results)
        ]
        return result.update, {
            "edge_anomaly_mean": float(result.anomaly_mass),
            "edge_anomaly_max": float(result.anomaly_mass),
            "cloud_reliability_mean": float(result.reliability),
            "aggregation_metadata": result.metadata,
        }, client_suspicion

    edge_to_items: dict[int, list[tuple[int, ClientUpdate]]] = {}
    for idx, item in enumerate(client_results):
        edge_to_items.setdefault(item.edge_id, []).append((idx, item))
    edge_updates: list[torch.Tensor] = []
    edge_ids: list[int] = []
    edge_weights: list[float] = []
    reliabilities: list[float] = []
    anomalies: list[float] = []
    edge_inputs = {}
    edge_history_before = {}
    edge_detection_metadata = {}
    for edge_id in sorted(edge_to_items):
        if method == "hfl_hflmnd":
            if hflmnd_history is None:
                raise ValueError("HFLMND requires persistent cross-round history")
            edge_history_before[edge_id] = dict(hflmnd_history)
        indexed = edge_to_items[edge_id]
        local_updates = [item.update for _, item in indexed]
        local_weights = [float(item.num_samples) * float(getattr(item, "audit_multiplier", 1.0))
                         for _, item in indexed]
        local_ids = [item.client_id for _, item in indexed]
        edge_result = aggregator.aggregate(
            local_updates,
            weights=local_weights,
            client_ids=local_ids,
            reference_update=reference_update,
            round_idx=round_idx or 0,
            edge_id=edge_id,
            global_vector=flatten_model(model) if model is not None else None,
            model=model,
            root_loader=full_root_loader,
            device=device,
            history=hflmnd_history,
        )
        if edge_result.suspicion is not None:
            for (original_idx, _), suspicion in zip(indexed, edge_result.suspicion.tolist()):
                audit_suspicion = float(getattr(client_results[original_idx], "audit_suspicion", 0.0))
                client_suspicion[original_idx] = max(float(suspicion), audit_suspicion)
        edge_updates.append(edge_result.update)
        edge_ids.append(edge_id)
        edge_weights.append(max(1.0, sum(local_weights)) * float(edge_result.reliability))
        reliabilities.append(float(edge_result.reliability))
        anomalies.append(float(edge_result.anomaly_mass))
        edge_inputs[edge_id] = indexed
        if method == "hfl_hflmnd":
            edge_detection_metadata[str(edge_id)] = edge_result.metadata

    security_metadata = {}
    if receipt_authority is not None:
        if round_idx is None or model_hash is None:
            raise ValueError("Challenge protocol requires round and model hash")
        reports = []
        direct_receipts = {}
        for edge_id, edge_update in zip(edge_ids, edge_updates):
            receipts = [receipt_authority.sign(
                round_idx=round_idx, model_hash=model_hash, client_id=item.client_id,
                edge_id=edge_id, sample_mass=int(item.num_samples), update=item.update,
            ) for _, item in edge_inputs[edge_id]]
            direct_receipts[edge_id] = tuple(receipts)
            reports.append(commit_edge(round_idx, edge_id, edge_update, receipts))
        edge_attack = config.get("edge_attack", {})
        if edge_attack.get("name") not in (None, "none"):
            compromised = int(edge_attack["edge_id"])
            from dataclasses import replace
            for index, report in enumerate(reports):
                if report.edge_id != compromised:
                    continue
                if edge_attack["name"] == "aggregate_replacement":
                    forged = -float(edge_attack.get("scale", 2.0)) * report.aggregate
                    reports[index] = commit_edge(round_idx, compromised, forged, list(report.receipts))
                elif edge_attack["name"] == "report_forgery":
                    forged = replace(report.receipts[0], sample_mass=report.receipts[0].sample_mass + 1)
                    reports[index] = commit_edge(round_idx, compromised, report.aggregate,
                                                 [forged, *report.receipts[1:]])
                else:
                    raise ValueError("Unknown edge attack")
        challenged = _choose_study_challenges(reports, config, int(round_idx or 0))
        rejected = set()
        challenge_bytes = 0
        for report in reports:
            try:
                if report.receipts != direct_receipts[report.edge_id]:
                    raise ValueError("Edge report does not match direct client receipts")
                for receipt in report.receipts:
                    receipt_authority.verify_signature(
                        receipt, round_idx=round_idx, model_hash=model_hash,
                        edge_id=report.edge_id,
                    )
            except ValueError:
                rejected.add(report.edge_id)
        for report in reports:
            if report.edge_id not in challenged or report.edge_id in rejected:
                continue
            indexed = edge_inputs[report.edge_id]
            raw = {item.client_id: item.update for _, item in indexed}
            challenge_bytes += sum(item.update.numel() * item.update.element_size()
                                   for _, item in indexed)
            def recompute(updates, masses, items=indexed):
                ids = [item.client_id for _, item in items]
                independent = build_aggregator(method, config, dimension=model_dim)
                if method == "tierguard":
                    if model is None or audit_loader is None or device is None:
                        raise ValueError("TierGuard challenge requires its audit context")
                    multipliers, _ = _backdoor_audit_multipliers(
                        model, updates, audit_loader, config, device,
                    )
                    masses = [max(1.0, mass * multiplier)
                              for mass, multiplier in zip(masses, multipliers)]
                return independent.aggregate(
                    updates, weights=masses, client_ids=ids,
                    reference_update=reference_update,
                    round_idx=round_idx, edge_id=items[0][1].edge_id,
                    global_vector=flatten_model(model) if model is not None else None,
                    model=model,
                    root_loader=full_root_loader,
                    device=device,
                    history=(dict(edge_history_before[items[0][1].edge_id])
                             if method == "hfl_hflmnd" else None),
                ).update
            try:
                verify_challenged_report(
                    report, raw, receipt_authority, round_idx=round_idx,
                    model_hash=model_hash, recompute=recompute,
                )
            except ValueError:
                rejected.add(report.edge_id)
        surviving = [(report, weight) for report, weight in zip(reports, edge_weights)
                     if report.edge_id not in rejected]
        if not surviving:
            raise ValueError("All active edge reports were rejected")
        edge_updates = [report.aggregate for report, _ in surviving]
        edge_weights = [weight for _, weight in surviving]
        security_metadata = {
            "challenged_edges": sorted(challenged),
            "single_report_escape_probability": single_report_escape_probability(len(reports)),
            "rejected_edges": sorted(rejected),
            "challenge_raw_upload_bytes": challenge_bytes,
            "client_edge_update_bytes": sum(item.update.numel() * item.update.element_size()
                                            for item in client_results),
            "client_cloud_receipt_bytes": sum(
                len(json.dumps(receipt.__dict__, sort_keys=True).encode("utf-8"))
                for report in reports for receipt in report.receipts
            ),
            "edge_cloud_report_bytes": sum(
                report.aggregate.numel() * report.aggregate.element_size()
                + len(report.commitment.encode("ascii")) for report in reports
            ),
        }

    if method == "tierguard":
        cloud_result = aggregator.aggregate(
            edge_updates,
            weights=edge_weights,
            reference_update=reference_update,
        )
    elif method in {"hfl_fedavg", "tapfed_sim"}:
        cloud_result = FedAvgAggregator(config).aggregate(edge_updates, weights=edge_weights)
    else:
        cloud_result = aggregator.aggregate(
            edge_updates, weights=edge_weights, reference_update=reference_update,
            client_ids=[report.edge_id for report, _ in surviving]
            if receipt_authority is not None else edge_ids,
            round_idx=round_idx or 0, edge_id=-1,
            global_vector=flatten_model(model) if model is not None else None,
            model=model,
            root_loader=full_root_loader,
            device=device,
            history=hflmnd_history,
        )
    return cloud_result.update, {
        "edge_anomaly_mean": float(np.mean(anomalies)) if anomalies else 0.0,
        "edge_anomaly_max": float(np.max(anomalies)) if anomalies else 0.0,
        "cloud_reliability_mean": float(np.mean(reliabilities)) if reliabilities else 1.0,
        "aggregation_metadata": {
            **cloud_result.metadata,
            **security_metadata,
            **({"edge_detection": edge_detection_metadata}
               if method == "hfl_hflmnd" else {}),
        },
    }, client_suspicion


def _communication_overhead(config: dict, selected_clients: int, num_edges_active: int, model_dim: int) -> dict:
    bits = int(config.get("security", {}).get("quantization_bits", 16))
    client_edge_bytes = selected_clients * model_dim * bits / 8
    edge_cloud_bytes = num_edges_active * model_dim * bits / 8
    if bool(config.get("security", {}).get("secure_sim", False)):
        sec = config["security"]
        edge_comm = threshold_comm_cost(
            selected_clients, model_dim, bits, int(sec.get("edge_committee_size", 3))
        )
        cloud_comm = threshold_comm_cost(
            num_edges_active, model_dim, bits, int(sec.get("cloud_committee_size", 5))
        )
        client_edge_bytes = edge_comm["total_bytes"]
        edge_cloud_bytes = cloud_comm["total_bytes"]
    total = client_edge_bytes + edge_cloud_bytes
    return {
        "comm_client_edge_mb": bytes_to_mb(client_edge_bytes),
        "comm_edge_cloud_mb": bytes_to_mb(edge_cloud_bytes),
        "total_comm_mb": bytes_to_mb(total),
    }


def run_experiment(config: dict, command: str | None = None, results_root: str | Path = "results") -> Path:
    config = resolve_attack_instance(config)
    seed = int(config.get("experiment", {}).get("seed", 1))
    seed_everything(seed)
    run_dir = make_run_dir(config, results_root)
    artifacts = artifact_paths(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    save_resolved_config(config, run_dir)
    artifacts.command_txt.write_text(command or " ".join(sys.argv), encoding="utf-8")

    device = _device_from_config(config)
    provenance = _run_provenance(config, device)
    if config.get("provenance", {}).get("require_clean_git", False):
        if (provenance["git_commit"] == "unavailable" or
                provenance["git_worktree_dirty"] is not False):
            raise ValueError("Source attestation requires a readable, clean Git checkout")
    challenge_secret_path = config.get("security", {}).get("challenge_secret_path")
    if challenge_secret_path and len(Path(challenge_secret_path).read_bytes()) < 32:
        raise ValueError("Cloud challenge secret must contain at least 32 bytes")
    save_json(provenance, artifacts.provenance_json)
    data = make_data_bundle(config)
    semantic_train_images = None
    if data.semantic_train_dataset is not None:
        semantic_train_images = torch.stack(
            [data.semantic_train_dataset[index][0]
             for index in range(len(data.semantic_train_dataset))]
        )
    if data.partition_indices is not None:
        save_json(data.partition_indices, run_dir / "partition_indices.json")
    model = build_model(
        config.get("model", {}).get("name", "mnist_cnn"),
        num_classes=data.num_classes,
        input_dim=data.input_dim,
    )
    model_dim = int(flatten_model(model).numel())
    num_clients = int(config["federated"]["num_clients"])
    edge_lookup = client_to_edge(data.edge_mapping)
    malicious_clients = _select_malicious(
        num_clients,
        float(config.get("attack", {}).get("malicious_fraction", 0.0)),
        seed + 17,
    )
    distributed_components = (
        {client_id: index % 4 for index, client_id in enumerate(sorted(malicious_clients))}
        if str(config.get("attack", {}).get("name", "")) == "distributed_backdoor"
        else {}
    )
    save_json({
        "malicious_client_ids": sorted(malicious_clients),
        "distributed_components": {str(key): value for key, value in
                                   distributed_components.items()},
    }, run_dir / "attack_assignment.json")
    clients = [
        FederatedClient(
            client_id=client_id,
            edge_id=edge_lookup[client_id],
            loader=data.client_loaders[client_id],
            malicious=client_id in malicious_clients,
            distributed_component=distributed_components.get(client_id),
        )
        for client_id in range(num_clients)
    ]
    method = str(config.get("aggregation", {}).get("method", "fedavg")).lower()
    auditor = None
    receipt_authority = None
    hflmnd_history: dict[tuple[int, int], int] | None = (
        {} if method == "hfl_hflmnd" else None
    )
    if method == "tierguard2":
        if bool(config.get("privacy", {}).get("enabled", False)) or bool(config.get("security", {}).get("secure_sim", False)):
            raise ValueError("TierGuard 2 is a plaintext method; disable DP and secure simulation")
        if data.audit_search_loader is None or data.audit_eval_loader is None:
            raise ValueError("TierGuard 2 requires disjoint search and evaluation roots")
        auditor = CounterfactualAuditor(
            data.audit_search_loader, data.audit_eval_loader, data.num_classes,
            config["tierguard2"], device,
        )
        receipt_authority = ReceiptAuthority(list(range(num_clients)))
        save_json({str(client_id): receipt_authority.public_key_bytes(client_id).hex()
                   for client_id in range(num_clients)}, run_dir / "client_public_keys.json")
    elif bool(config.get("security", {}).get("edge_challenges", False)):
        if method not in HIERARCHICAL_METHODS:
            raise ValueError("Edge challenges require a hierarchical method")
        if bool(config.get("security", {}).get("secure_sim", False)):
            raise ValueError("Edge challenges require plaintext updates")
        receipt_authority = ReceiptAuthority(list(range(num_clients)))
        save_json({str(client_id): receipt_authority.public_key_bytes(client_id).hex()
                   for client_id in range(num_clients)}, run_dir / "client_public_keys.json")
    if (config.get("edge_attack", {}).get("name") not in (None, "none")
            and receipt_authority is None):
        raise ValueError("Compromised-edge experiments require matched receipt challenges")

    rounds = int(config.get("experiment", {}).get("rounds", 1))
    eval_every = int(config.get("experiment", {}).get("eval_every", 1))
    metrics_rows: list[dict] = []
    detection_rows: list[dict] = []
    overhead_totals = {"comm_client_edge_mb": 0.0, "comm_edge_cloud_mb": 0.0, "total_comm_mb": 0.0}
    last_metrics: dict[str, float] = {}
    stability_failures = 0
    latest_attack_trigger = None

    for round_idx in range(1, rounds + 1):
        start = time.time()
        if config["federated"].get("clients_per_edge_per_round") is not None:
            selected = _selected_clients_per_edge(
                data.edge_mapping,
                int(config["federated"]["clients_per_edge_per_round"]),
                seed, round_idx,
            )
        else:
            selected = _selected_clients(
                num_clients,
                int(config["federated"]["clients_per_round"]),
                seed,
                round_idx,
            )
        reference_update = compute_reference_update(
            model,
            data.root_loader,
            config["federated"],
            device,
            data.num_classes,
        )
        round_config = config
        if semantic_train_images is not None:
            round_config = copy.deepcopy(config)
            round_config["attack"]["semantic_train_images"] = semantic_train_images
        if str(config.get("attack", {}).get("name", "none")) == "defence_aware_optimized_trigger":
            malicious_selected = [client_id for client_id in selected if client_id in malicious_clients]
            if malicious_selected:
                latest_attack_trigger = None
                for attacker_id in sorted(malicious_selected):
                    try:
                        latest_attack_trigger = optimize_trigger(
                            model, clients[attacker_id].loader, config["attack"], device,
                            seed=seed + round_idx * 100_003 + attacker_id * 1009,
                        )
                        break
                    except ValueError as exc:
                        if "no non-target local examples" not in str(exc):
                            raise
                if latest_attack_trigger is None:
                    raise ValueError("No selected malicious client can optimize the trigger")
                round_config = copy.deepcopy(config)
                round_config["attack"]["trigger_tensor"] = latest_attack_trigger
        local_results = [
            clients[client_id].train(
                model, round_config, device=device, num_classes=data.num_classes,
                round_idx=round_idx,
            )
            for client_id in selected
        ]
        local_results = _post_process_attacks(local_results, config, reference_update)
        attack_instances = {
            str(item.client_id): item.attack_trigger.tolist()
            for item in local_results if item.attack_trigger is not None
        }
        if attack_instances:
            save_json(attack_instances, run_dir / f"attack_triggers_round_{round_idx:03d}.json")
        for item in local_results:
            item.update = _apply_privacy(item.update, config)
            if not torch.isfinite(item.update).all():
                stability_failures += 1
                item.update = torch.nan_to_num(item.update, nan=0.0, posinf=0.0, neginf=0.0)
        if method == "tierguard":
            audit_multipliers, audit_risks = _backdoor_audit_multipliers(
                model,
                [item.update for item in local_results],
                data.audit_loader,
                config,
                device,
            )
            for item, multiplier, risk in zip(local_results, audit_multipliers, audit_risks):
                if receipt_authority is not None:
                    setattr(item, "audit_multiplier", max(
                        1.0 / max(1.0, float(item.num_samples)), float(multiplier)
                    ))
                else:
                    item.num_samples = max(1.0, float(item.num_samples) * multiplier)
                setattr(item, "audit_suspicion", min(1.0, float(risk)))

        if method == "tierguard2":
            auditor.begin_round(model)

        if method == "tierguard2":
            update, agg_meta, suspicion = _aggregate_tierguard2(
                local_results, model, auditor, reference_update, config,
                receipt_authority, round_idx,
            )
            save_json(agg_meta["aggregation_metadata"], run_dir / f"audit_round_{round_idx:03d}.json")
        else:
            update, agg_meta, suspicion = _aggregate_round(
                local_results, config, reference_update, model_dim,
                receipt_authority=receipt_authority, round_idx=round_idx,
                model_hash=update_digest(flatten_model(model)) if receipt_authority is not None else None,
                model=model, audit_loader=data.audit_loader,
                full_root_loader=data.full_root_loader, device=device,
                hflmnd_history=hflmnd_history,
            )
            if receipt_authority is not None:
                save_json(agg_meta["aggregation_metadata"],
                          run_dir / f"audit_round_{round_idx:03d}.json")
        if not torch.isfinite(update).all():
            stability_failures += 1
            update = torch.nan_to_num(update, nan=0.0, posinf=0.0, neginf=0.0)
        apply_update(model, update, server_lr=float(config["federated"].get("server_lr", 1.0)))
        runtime = time.time() - start
        active_edges = len({item.edge_id for item in local_results})
        comm = _communication_overhead(config, len(local_results), active_edges, model_dim)
        if receipt_authority is not None:
            # Byte accounting for specified payloads, not measured latency or
            # actual network transfer.  Keep legacy field names for CSV schema.
            transport = agg_meta["aggregation_metadata"]
            comm["comm_client_edge_mb"] = transport["client_edge_update_bytes"] / 1_000_000
            comm["comm_edge_cloud_mb"] = (
                transport["edge_cloud_report_bytes"]
                + transport["client_cloud_receipt_bytes"]
                + transport["challenge_raw_upload_bytes"]
            ) / 1_000_000
            comm["total_comm_mb"] = comm["comm_client_edge_mb"] + comm["comm_edge_cloud_mb"]
            comm["challenge_raw_upload_mb"] = transport["challenge_raw_upload_bytes"] / 1_000_000
        for key in overhead_totals:
            overhead_totals[key] += comm[key]
        det = detection_scores([item.malicious for item in local_results], suspicion)
        detection_rows.append({"round": round_idx, **det})

        if round_idx % eval_every == 0 or round_idx == rounds:
            clean = evaluate_classifier(model, data.test_loader, device)
            if str(config.get("attack", {}).get("name", "none")) == "none":
                asr = None
            elif (str(config.get("attack", {}).get("name", "none"))
                  == "defence_aware_optimized_trigger" and latest_attack_trigger is not None):
                dynamic_attack = {**config["attack"], "trigger_tensor": latest_attack_trigger}
                dynamic_test = torch.utils.data.DataLoader(
                    BackdoorDataset(data.test_loader.dataset,
                                    target_label=int(config["attack"]["target_label"]),
                                    attack_config=dynamic_attack),
                    batch_size=int(config["federated"].get("batch_size", 64)),
                    shuffle=False,
                )
                asr = attack_success_rate(model, dynamic_test, device)
            elif data.semantic_test_loader is not None:
                asr = attack_success_rate(model, data.semantic_test_loader, device)
            else:
                asr = attack_success_rate(model, data.backdoor_test_loader, device)
            privacy = privacy_accounting(config, round_idx)
            last_metrics = {
                **clean,
                "asr": float(asr) if asr is not None else None,
                "attack_success_rate": float(asr) if asr is not None else None,
                "epsilon": float(privacy["epsilon"]) if math.isfinite(float(privacy["epsilon"])) else float("inf"),
                "delta": float(privacy["delta"]),
            }
        row = {
            "round": round_idx,
            "experiment_name": config.get("experiment", {}).get("name"),
            "dataset": config["data"].get("dataset"),
            "method": config["aggregation"].get("method"),
            "attack": config["attack"].get("name"),
            "seed": seed,
            "dirichlet_alpha": config["data"].get("dirichlet_alpha"),
            "malicious_fraction": config["attack"].get("malicious_fraction"),
            "clean_accuracy": last_metrics.get("clean_accuracy", np.nan),
            "clean_loss": last_metrics.get("clean_loss", np.nan),
            "macro_f1": last_metrics.get("macro_f1", np.nan),
            "asr": last_metrics.get("asr", np.nan),
            "attack_success_rate": last_metrics.get("attack_success_rate", np.nan),
            "edge_anomaly_mean": agg_meta["edge_anomaly_mean"],
            "edge_anomaly_max": agg_meta["edge_anomaly_max"],
            "detection_precision": det["detection_precision"],
            "detection_recall": det["detection_recall"],
            "detection_f1": det["detection_f1"],
            "epsilon": last_metrics.get("epsilon", 0.0),
            "delta": config.get("privacy", {}).get("delta", 1e-5),
            "round_runtime_sec": runtime,
            "stability_failures": stability_failures,
            **comm,
        }
        metrics_rows.append(row)
        pd.DataFrame(metrics_rows).to_csv(artifacts.metrics_csv, index=False)
        pd.DataFrame(detection_rows).to_csv(artifacts.detection_csv, index=False)

    tg_cfg = config.get("tierguard", {})
    project_root = Path(__file__).resolve().parents[3]
    try:
        recorded_run_dir = run_dir.resolve().relative_to(project_root).as_posix()
    except ValueError:
        recorded_run_dir = str(run_dir)
    final = {
        "experiment_name": config.get("experiment", {}).get("name"),
        "method": config["aggregation"].get("method"),
        "dataset": config["data"].get("dataset"),
        "attack": config["attack"].get("name"),
        "alpha": config["data"].get("dirichlet_alpha"),
        "malicious_fraction": config["attack"].get("malicious_fraction"),
        "seed": seed,
        "num_clients": config["federated"].get("num_clients"),
        "num_edges": config["federated"].get("num_edges"),
        "selected_clients_per_round": (
            int(config["federated"]["clients_per_edge_per_round"])
            * int(config["federated"]["num_edges"])
            if config["federated"].get("clients_per_edge_per_round") is not None
            else config["federated"].get("clients_per_round")
        ),
        "local_epochs": config["federated"].get("local_epochs"),
        "privacy_epsilon": last_metrics.get("epsilon", 0.0),
        "runtime": float(sum(row["round_runtime_sec"] for row in metrics_rows)),
        "communication": overhead_totals["total_comm_mb"],
        "clean_accuracy": last_metrics.get("clean_accuracy", 0.0),
        "macro_f1": last_metrics.get("macro_f1", 0.0),
        "attack_success_rate": last_metrics.get("attack_success_rate", 0.0),
        "detection_precision": detection_rows[-1].get("detection_precision", 0.0) if detection_rows else 0.0,
        "detection_recall": detection_rows[-1].get("detection_recall", 0.0) if detection_rows else 0.0,
        "detection_f1": detection_rows[-1].get("detection_f1", 0.0) if detection_rows else 0.0,
        "final_round": rounds,
        "run_dir": recorded_run_dir,
        "stability_failures": stability_failures,
        "hierarchical_aggregation": method in HIERARCHICAL_METHODS,
        "git_commit": provenance["git_commit"],
        "config_sha256": provenance["config_sha256"],
    }
    if method == "tierguard":
        final.update({
            "tierguard_score_mode": tg_cfg.get("score_mode"),
            "tierguard_gamma": tg_cfg.get("gamma"),
            "tierguard_adaptive_gamma": tg_cfg.get("adaptive_gamma"),
            "tierguard_clip_multiplier": tg_cfg.get("clip_multiplier"),
            "tierguard_tau_low": tg_cfg.get("tau_low"),
            "tierguard_tau_high": tg_cfg.get("tau_high"),
        })
    save_json(final, artifacts.final_metrics_json)
    save_json(
        {
            **overhead_totals,
            "model_dimension": model_dim,
            "secure_sim": bool(config.get("security", {}).get("secure_sim", False)),
        },
        artifacts.overhead_json,
    )
    save_json(privacy_accounting(config, rounds), artifacts.privacy_json)
    return run_dir
