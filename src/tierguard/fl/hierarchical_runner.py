from __future__ import annotations

import json
import math
import hashlib
import importlib.metadata
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
from tierguard.attacks import apply_post_update_attack
from tierguard.attacks.alie import alie_attack
from tierguard.config import artifact_paths, make_run_dir, save_json, save_resolved_config
from tierguard.data.backdoor import add_bottom_right_square
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
from tierguard.seed import seed_everything


HIERARCHICAL_METHODS = {
    "hfl_fedavg",
    "hfl_fltrust",
    "hfl_trimmed_mean",
    "hfl_rfa",
    "tierguard",
    "shield_like",
    "shield_like_reimplementation",
    "roppfl_like",
    "roppfl_like_reimplementation",
    "tapfed_sim",
    "brea_sim",
}


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
        "device": str(device),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_version": torch.version.cuda,
        "cudnn_version": torch.backends.cudnn.version(),
        "packages": versions,
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
    attack_ext["clients_per_round"] = config.get("federated", {}).get("clients_per_round", 1)
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
) -> tuple[torch.Tensor, dict, list[float]]:
    method = str(config.get("aggregation", {}).get("method", "fedavg")).lower()
    aggregator = build_aggregator(method, config, dimension=model_dim)
    selected_ids = [item.client_id for item in client_results]
    sample_weights = [float(item.num_samples) for item in client_results]
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
    edge_weights: list[float] = []
    reliabilities: list[float] = []
    anomalies: list[float] = []
    for edge_id in sorted(edge_to_items):
        indexed = edge_to_items[edge_id]
        local_updates = [item.update for _, item in indexed]
        local_weights = [float(item.num_samples) for _, item in indexed]
        local_ids = [item.client_id for _, item in indexed]
        edge_result = aggregator.aggregate(
            local_updates,
            weights=local_weights,
            client_ids=local_ids,
            reference_update=reference_update,
        )
        if edge_result.suspicion is not None:
            for (original_idx, _), suspicion in zip(indexed, edge_result.suspicion.tolist()):
                audit_suspicion = float(getattr(client_results[original_idx], "audit_suspicion", 0.0))
                client_suspicion[original_idx] = max(float(suspicion), audit_suspicion)
        edge_updates.append(edge_result.update)
        edge_weights.append(max(1.0, sum(local_weights)) * float(edge_result.reliability))
        reliabilities.append(float(edge_result.reliability))
        anomalies.append(float(edge_result.anomaly_mass))

    if method == "tierguard":
        cloud_result = aggregator.aggregate(
            edge_updates,
            weights=edge_weights,
            reference_update=reference_update,
        )
    elif method in {"hfl_fedavg", "tapfed_sim"}:
        cloud_result = FedAvgAggregator(config).aggregate(edge_updates, weights=edge_weights)
    else:
        cloud_result = aggregator.aggregate(edge_updates, weights=edge_weights, reference_update=reference_update)
    return cloud_result.update, {
        "edge_anomaly_mean": float(np.mean(anomalies)) if anomalies else 0.0,
        "edge_anomaly_max": float(np.max(anomalies)) if anomalies else 0.0,
        "cloud_reliability_mean": float(np.mean(reliabilities)) if reliabilities else 1.0,
        "aggregation_metadata": cloud_result.metadata,
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
    seed = int(config.get("experiment", {}).get("seed", 1))
    seed_everything(seed)
    run_dir = make_run_dir(config, results_root)
    artifacts = artifact_paths(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    save_resolved_config(config, run_dir)
    artifacts.command_txt.write_text(command or " ".join(sys.argv), encoding="utf-8")

    device = _device_from_config(config)
    provenance = _run_provenance(config, device)
    save_json(provenance, artifacts.provenance_json)
    data = make_data_bundle(config)
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
    clients = [
        FederatedClient(
            client_id=client_id,
            edge_id=edge_lookup[client_id],
            loader=data.client_loaders[client_id],
            malicious=client_id in malicious_clients,
        )
        for client_id in range(num_clients)
    ]

    rounds = int(config.get("experiment", {}).get("rounds", 1))
    eval_every = int(config.get("experiment", {}).get("eval_every", 1))
    metrics_rows: list[dict] = []
    detection_rows: list[dict] = []
    overhead_totals = {"comm_client_edge_mb": 0.0, "comm_edge_cloud_mb": 0.0, "total_comm_mb": 0.0}
    last_metrics: dict[str, float] = {}
    stability_failures = 0

    for round_idx in range(1, rounds + 1):
        start = time.time()
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
        local_results = [
            clients[client_id].train(model, config, device=device, num_classes=data.num_classes)
            for client_id in selected
        ]
        local_results = _post_process_attacks(local_results, config, reference_update)
        for item in local_results:
            item.update = _apply_privacy(item.update, config)
            if not torch.isfinite(item.update).all():
                stability_failures += 1
                item.update = torch.nan_to_num(item.update, nan=0.0, posinf=0.0, neginf=0.0)
        method = str(config.get("aggregation", {}).get("method", "fedavg")).lower()
        if method == "tierguard":
            audit_multipliers, audit_risks = _backdoor_audit_multipliers(
                model,
                [item.update for item in local_results],
                data.audit_loader,
                config,
                device,
            )
            for item, multiplier, risk in zip(local_results, audit_multipliers, audit_risks):
                item.num_samples = max(1.0, float(item.num_samples) * multiplier)
                setattr(item, "audit_suspicion", min(1.0, float(risk)))

        update, agg_meta, suspicion = _aggregate_round(local_results, config, reference_update, model_dim)
        if not torch.isfinite(update).all():
            stability_failures += 1
            update = torch.nan_to_num(update, nan=0.0, posinf=0.0, neginf=0.0)
        apply_update(model, update, server_lr=float(config["federated"].get("server_lr", 1.0)))
        runtime = time.time() - start
        active_edges = len({item.edge_id for item in local_results})
        comm = _communication_overhead(config, len(local_results), active_edges, model_dim)
        for key in overhead_totals:
            overhead_totals[key] += comm[key]
        det = detection_scores([item.malicious for item in local_results], suspicion)
        detection_rows.append({"round": round_idx, **det})

        if round_idx % eval_every == 0 or round_idx == rounds:
            clean = evaluate_classifier(model, data.test_loader, device)
            asr = attack_success_rate(model, data.backdoor_test_loader, device)
            privacy = privacy_accounting(config, round_idx)
            last_metrics = {
                **clean,
                "asr": float(asr),
                "attack_success_rate": float(asr),
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
        "selected_clients_per_round": config["federated"].get("clients_per_round"),
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
        "tierguard_score_mode": tg_cfg.get("score_mode"),
        "tierguard_gamma": tg_cfg.get("gamma"),
        "tierguard_adaptive_gamma": tg_cfg.get("adaptive_gamma"),
        "tierguard_clip_multiplier": tg_cfg.get("clip_multiplier"),
        "tierguard_tau_low": tg_cfg.get("tau_low"),
        "tierguard_tau_high": tg_cfg.get("tau_high"),
    }
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
