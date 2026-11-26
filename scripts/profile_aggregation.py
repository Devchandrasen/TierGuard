# ruff: noqa: E402
"""Profile trusted aggregation on synthetic inputs without training or a network."""

from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
import csv
import json
from pathlib import Path
import platform
from statistics import median, quantiles
import struct
import sys
from time import perf_counter_ns
from unittest.mock import patch

import torch

ROOT = Path(__file__).resolve().parents[1]
# Keep the profiler bound to this checkout even when another version is installed.
sys.path.insert(0, str(ROOT / "src"))

from tierguard.aggregators.tierguard import TierGuardAggregator
from tierguard.config import load_config
from tierguard.fl.client import ClientUpdate
from tierguard.fl.hierarchical_runner import _aggregate_round, _backdoor_audit_multipliers
from tierguard.fl.update_utils import flatten_model
from tierguard.models.mnist_cnn import MnistCNN


TOPOLOGIES = ((20, 5), (40, 5), (40, 10), (80, 10))
METHODS = ("HFL-FedAvg", "TierGuard Core", "TierGuard-PTA")
CPU = torch.device("cpu")


def vector_bytes(update: torch.Tensor) -> bytes:
    return update.numpy().astype("<f4", copy=False).tobytes()


def profile_round(model, updates, root_batch, config, reference, edges):
    score_ns = 0
    anomaly_paths = []
    score_updates = TierGuardAggregator.score_updates
    aggregate = TierGuardAggregator.aggregate

    def record_scores(aggregator, *args, **kwargs):
        nonlocal score_ns
        started = perf_counter_ns()
        result = score_updates(aggregator, *args, **kwargs)
        score_ns += perf_counter_ns() - started
        return result

    def record_path(aggregator, *args, **kwargs):
        result = aggregate(aggregator, *args, **kwargs)
        anomaly_paths.append((result.anomaly_mass, len(args[0]), result.metadata["mode"]))
        return result

    auditing = config["tierguard"]["use_backdoor_audit"]
    audit_ns = 0
    if auditing:
        started = perf_counter_ns()
        multipliers, risks = _backdoor_audit_multipliers(
            model, [item.update for item in updates], root_batch, config, CPU
        )
        for item, multiplier, risk in zip(updates, multipliers, risks, strict=True):
            item.num_samples = max(1.0, item.num_samples * multiplier)
            item.audit_suspicion = min(1.0, risk)
        audit_ns = perf_counter_ns() - started

    with patch.object(TierGuardAggregator, "score_updates", record_scores), patch.object(
        TierGuardAggregator, "aggregate", record_path
    ):
        started = perf_counter_ns()
        result, _, _ = _aggregate_round(updates, config, reference, reference.numel())
        total_ns = perf_counter_ns() - started

    if not torch.isfinite(result).all():
        raise ValueError("Non-finite aggregate")
    is_tierguard = config["aggregation"]["method"] == "tierguard"
    if is_tierguard and len(anomaly_paths) != edges + 1:
        raise ValueError("Unexpected number of aggregation groups")
    for mass, count, mode in anomaly_paths:
        if mass > (count // 2) / count + 1e-7 or mode != "weighted_clipped_mean":
            raise ValueError("Unexpected anomaly bound or aggregation branch")

    return {
        "statistics_ms": score_ns / 1e6,
        "aggregation_ms": (total_ns - score_ns) / 1e6,
        "pta_ms": audit_ns / 1e6,
        "total_ms": (total_ns + audit_ns) / 1e6,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=30)
    parser.add_argument("--warmups", type=int, default=5)
    args = parser.parse_args()
    if args.rounds < 2 or args.warmups < 0:
        parser.error("Specify at least two rounds and a nonnegative warmup count")
    torch.set_num_threads(1)
    torch.manual_seed(2026)
    draws = torch.Generator().manual_seed(2609)
    model = MnistCNN().eval()
    model_vector = flatten_model(model)
    size = model_vector.numel()
    base = load_config(ROOT / "configs" / "confirmatory_v1" / "mnist.yaml")
    configs = {}
    for method in METHODS:
        config = deepcopy(base)
        config["aggregation"]["method"] = "hfl_fedavg" if method == METHODS[0] else "tierguard"
        config["tierguard"]["use_backdoor_audit"] = method == METHODS[-1]
        configs[method] = config

    images = torch.rand((64, 1, 28, 28), generator=draws)
    labels = torch.arange(1, 65, dtype=torch.long) % 9 + 1
    root_batch = [(images, labels)]
    calibration_payload = vector_bytes(images) + labels.numpy().astype("<i8").tobytes()
    model_payload = vector_bytes(model_vector)
    rows = []
    observations = defaultdict(list)
    for clients, edges in TOPOLOGIES:
        active = clients // 2
        for round_index in range(args.rounds + args.warmups):
            reference = torch.randn(size, generator=draws) * 0.001
            vectors = reference + 0.001 * torch.randn((active, size), generator=draws)
            counts = [int(n) for n in torch.randint(48, 129, (active,), generator=draws)]
            client_upload = sum(
                len(vector_bytes(update) + struct.pack("<Q", count))
                for update, count in zip(vectors, counts, strict=True)
            )
            edge_upload = edges * len(model_payload + struct.pack("<d", 1.0))
            for offset in range(len(METHODS)):
                method = METHODS[(round_index + offset) % len(METHODS)]
                updates = [
                    ClientUpdate(update, i, i % edges, counts[i], False, 0.0, 0.0)
                    for i, update in enumerate(vectors)
                ]
                times = profile_round(model, updates, root_batch, configs[method], reference, edges)
                if round_index >= args.warmups:
                    row = {"clients": clients, "edges": edges, "method": method,
                           "round": round_index - args.warmups + 1, **times}
                    observations[clients, edges, method].append(row)

        for method in METHODS:
            row = {
                "clients": clients, "edges": edges, "active_clients": active, "method": method,
                "audit_candidates": active if method == METHODS[-1] else 0,
                "forward_images": 64 * (active + 1) if method == METHODS[-1] else 0,
                "client_edge_upload_bytes": client_upload,
                "client_edge_download_bytes": active * len(model_payload),
                "edge_cloud_upload_bytes": edge_upload,
                "edge_cloud_download_bytes": edges * len(model_payload),
                "local_pta_batch_bytes": len(calibration_payload) if method == METHODS[-1] else 0,
            }
            for metric in times:
                sample = [item[metric] for item in observations[clients, edges, method]]
                row[f"{metric}_median"] = median(sample)
                row[f"{metric}_p95"] = quantiles(sample, n=100, method="inclusive")[94]
            rows.append(row)

    args.output.mkdir(parents=True, exist_ok=True)
    for file_name, records in (
        ("summary.csv", rows),
        ("round_timings.csv", [row for group in observations.values() for row in group]),
    ):
        with (args.output / file_name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
    meta = {
        "model_parameters": size, "warmup_rounds": args.warmups, "measured_rounds": args.rounds,
        "torch_threads": 1, "python": sys.version.split()[0], "torch": torch.__version__,
        "platform": platform.platform(), "processor": platform.processor(),
        "model_seed": 2026, "workload_seed": 2609,
        "local_workload": "Synthetic updates, precomputed root direction, and one resident 64-item calibration batch",
        "payload": "Little-endian float32 vectors, uint64 counts and float64 edge masses; unicast, no framing",
    }
    (args.output / "environment.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
