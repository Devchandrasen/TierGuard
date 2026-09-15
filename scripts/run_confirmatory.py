from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import torch
import yaml

from tierguard.config import load_config
from tierguard.data.datasets import load_vision_datasets
from tierguard.fl.hierarchical_runner import run_experiment
from tierguard.protocol import (
    frozen_manifest_sha256,
    sha256_file,
    verify_frozen_manifest,
    verify_runtime_environment,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FROZEN_MATRIX_PATH = (REPO_ROOT / "configs" / "confirmatory_v1" / "matrix.yaml").resolve()


def _load_matrix(path: Path) -> dict:
    matrix = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not matrix.get("frozen"):
        raise ValueError("confirmatory matrix must declare frozen: true")
    if len(matrix.get("seeds", [])) < 5:
        raise ValueError("confirmatory protocol requires at least five seeds")
    return matrix


def _tasks(matrix: dict, device: str) -> list[dict]:
    frozen_device = str(matrix.get("device", "cpu"))
    if device != frozen_device:
        raise ValueError(f"confirmatory-v1 requires device={frozen_device}, received {device}")
    manifest_hash = frozen_manifest_sha256(REPO_ROOT)
    tasks = []
    for dataset in matrix["datasets"]:
        for attack in matrix["attacks"]:
            for method in matrix["methods"]:
                for seed in matrix["seeds"]:
                    tasks.append(
                        {
                            "protocol_id": matrix["protocol_id"],
                            "manifest_hash": manifest_hash,
                            "dataset": dataset["name"],
                            "config_path": str(REPO_ROOT / dataset["config"]),
                            "attack": attack["name"],
                            "malicious_fraction": float(attack["malicious_fraction"]),
                            "method": method,
                            "seed": int(seed),
                            "device": device,
                        }
                    )
    return tasks


def _existing_run(results_root: Path, task: dict) -> Path | None:
    seed_root = (
        results_root
        / task["dataset"]
        / task["method"]
        / task["attack"]
        / "alpha_0.5"
        / f"mal_{task['malicious_fraction']}"
        / f"seed_{task['seed']}"
    )
    for final_path in sorted(seed_root.glob("*/final_metrics.json"), reverse=True):
        provenance_path = final_path.with_name("provenance.json")
        if not provenance_path.exists():
            continue
        try:
            final = json.loads(final_path.read_text(encoding="utf-8"))
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (
            final.get("experiment_name") == task["protocol_id"]
            and provenance.get("protocol_manifest_sha256") == task["manifest_hash"]
            and not provenance.get("git_worktree_dirty")
        ):
            return final_path.parent
    return None


def _run_one(task: dict, results_root: str, torch_threads: int) -> str:
    os.environ["OMP_NUM_THREADS"] = str(torch_threads)
    os.environ["MKL_NUM_THREADS"] = str(torch_threads)
    torch.set_num_threads(torch_threads)
    results_path = Path(results_root)
    existing = _existing_run(results_path, task)
    if existing is not None:
        return f"SKIP {task['dataset']} {task['method']} {task['attack']} seed={task['seed']}"

    config = load_config(task["config_path"])
    config["experiment"]["name"] = task["protocol_id"]
    config["experiment"]["seed"] = task["seed"]
    config["experiment"]["device"] = task["device"]
    config["aggregation"]["method"] = task["method"]
    config["attack"]["name"] = task["attack"]
    config["attack"]["malicious_fraction"] = task["malicious_fraction"]
    config["provenance"] = {
        "protocol_id": task["protocol_id"],
        "protocol_manifest_sha256": task["manifest_hash"],
    }
    command = (
        "python scripts/run_confirmatory.py "
        f"# {task['dataset']} {task['method']} {task['attack']} seed={task['seed']}"
    )
    run_dir = run_experiment(config, command=command, results_root=results_path)
    return f"DONE {run_dir}"


def _write_status(
    path: Path,
    protocol_total: int,
    scheduled_total: int,
    completed: list[str],
    failures: list[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "protocol_total_tasks": protocol_total,
        "scheduled_tasks": scheduled_total,
        "completed_tasks": len(completed),
        "failed_tasks": len(failures),
        "complete": len(completed) == protocol_total and not failures,
        "failures": failures,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_dataset_checksums(results_root: Path) -> None:
    lines = []
    for dataset_dir in (REPO_ROOT / "data" / "MNIST", REPO_ROOT / "data" / "FashionMNIST"):
        for path in sorted(dataset_dir.rglob("*")) if dataset_dir.exists() else []:
            if not path.is_file():
                continue
            digest = sha256_file(path)
            lines.append(f"{digest}  {path.relative_to(REPO_ROOT).as_posix()}")
    output = results_root / "DATASET_SHA256SUMS"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _prepare_datasets(matrix: dict) -> None:
    first_seed = int(matrix["seeds"][0])
    for dataset in matrix["datasets"]:
        config = load_config(REPO_ROOT / dataset["config"])
        if config["data"].get("synthetic"):
            raise ValueError("confirmatory-v1 forbids synthetic datasets")
        load_vision_datasets(config["data"], first_seed)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the frozen TierGuard confirmatory matrix")
    parser.add_argument("--matrix", default="configs/confirmatory_v1/matrix.yaml")
    parser.add_argument("--results-root", default="results/confirmatory_v1")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--torch-threads", type=int, default=1)
    parser.add_argument("--max-tasks", type=int)
    args = parser.parse_args()

    ok, errors = verify_frozen_manifest(REPO_ROOT)
    if not ok:
        raise SystemExit("frozen protocol verification failed: " + "; ".join(errors))
    environment_ok, environment_errors = verify_runtime_environment(REPO_ROOT)
    if not environment_ok:
        raise SystemExit("pinned environment verification failed: " + "; ".join(environment_errors))
    matrix_path = (REPO_ROOT / args.matrix).resolve()
    if matrix_path != FROZEN_MATRIX_PATH:
        raise SystemExit(f"confirmatory-v1 requires the frozen matrix: {FROZEN_MATRIX_PATH}")
    matrix = _load_matrix(matrix_path)
    protocol_tasks = _tasks(matrix, args.device)
    tasks = protocol_tasks
    if args.max_tasks is not None:
        tasks = tasks[: args.max_tasks]
    results_root = (REPO_ROOT / args.results_root).resolve()
    _prepare_datasets(matrix)
    _write_dataset_checksums(results_root)
    status_path = results_root / "CAMPAIGN_STATUS.json"
    completed: list[str] = []
    failures: list[str] = []

    if args.workers == 1:
        for task in tasks:
            try:
                message = _run_one(task, str(results_root), args.torch_threads)
                completed.append(message)
                print(f"[{len(completed)}/{len(tasks)}] {message}", flush=True)
            except Exception as exc:  # pragma: no cover - campaign failure path
                failure = f"{task}: {type(exc).__name__}: {exc}"
                failures.append(failure)
                print(f"FAILED {failure}", file=sys.stderr, flush=True)
                break
            finally:
                _write_status(
                    status_path,
                    len(protocol_tasks),
                    len(tasks),
                    completed,
                    failures,
                )
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            future_to_task = {
                pool.submit(_run_one, task, str(results_root), args.torch_threads): task
                for task in tasks
            }
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    message = future.result()
                    completed.append(message)
                    print(f"[{len(completed)}/{len(tasks)}] {message}", flush=True)
                except Exception as exc:  # pragma: no cover - campaign failure path
                    failure = f"{task}: {type(exc).__name__}: {exc}"
                    failures.append(failure)
                    print(f"FAILED {failure}", file=sys.stderr, flush=True)
                _write_status(
                    status_path,
                    len(protocol_tasks),
                    len(tasks),
                    completed,
                    failures,
                )
    if failures:
        raise SystemExit(f"{len(failures)} confirmatory tasks failed")


if __name__ == "__main__":
    main()
