from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy import stats

from tierguard.protocol import (
    frozen_manifest_sha256,
    locked_requirements,
    verify_frozen_manifest,
    verify_runtime_environment,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FROZEN_MATRIX_PATH = (REPO_ROOT / "configs" / "confirmatory_v1" / "matrix.yaml").resolve()


def _load_matrix(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _expected_keys(matrix: dict) -> set[tuple[str, str, str, int]]:
    return {
        (dataset["name"], method, attack["name"], int(seed))
        for dataset in matrix["datasets"]
        for method in matrix["methods"]
        for attack in matrix["attacks"]
        for seed in matrix["seeds"]
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_runs(results_root: Path, protocol_id: str, manifest_hash: str) -> tuple[pd.DataFrame, list[str]]:
    rows: list[dict] = []
    errors: list[str] = []
    expected_versions = locked_requirements(REPO_ROOT)
    expected_python = (REPO_ROOT / ".python-version").read_text(encoding="utf-8").strip()
    for final_path in sorted(results_root.rglob("final_metrics.json")):
        provenance_path = final_path.with_name("provenance.json")
        config_path = final_path.with_name("resolved_config.yaml")
        if not provenance_path.exists() or not config_path.exists():
            errors.append(f"incomplete run directory: {final_path.parent}")
            continue
        try:
            final = json.loads(final_path.read_text(encoding="utf-8"))
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except (OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
            errors.append(f"unreadable run directory: {final_path.parent}: {type(exc).__name__}")
            continue
        if final.get("experiment_name") != protocol_id:
            continue
        if provenance.get("protocol_manifest_sha256") != manifest_hash:
            errors.append(f"protocol hash mismatch: {final_path.parent}")
        if provenance.get("git_worktree_dirty") is not False:
            errors.append(f"run was not produced from a clean worktree: {final_path.parent}")
        if not final.get("hierarchical_aggregation"):
            errors.append(f"non-hierarchical run in confirmatory matrix: {final_path.parent}")
        if final.get("git_commit") != provenance.get("git_commit"):
            errors.append(f"git provenance mismatch: {final_path.parent}")
        if final.get("config_sha256") != provenance.get("config_sha256"):
            errors.append(f"config provenance mismatch: {final_path.parent}")
        configured = {
            "dataset": config.get("data", {}).get("dataset"),
            "method": config.get("aggregation", {}).get("method"),
            "attack": config.get("attack", {}).get("name"),
            "seed": config.get("experiment", {}).get("seed"),
            "malicious_fraction": config.get("attack", {}).get("malicious_fraction"),
        }
        for field, expected in configured.items():
            if final.get(field) != expected:
                errors.append(f"resolved-config mismatch for {field}: {final_path.parent}")
        configured_rounds = config.get("experiment", {}).get("rounds")
        if final.get("final_round") != configured_rounds:
            errors.append(f"incomplete round count: {final_path.parent}")
        if provenance.get("device") != "cpu":
            errors.append(f"confirmatory run did not use CPU: {final_path.parent}")
        if not str(provenance.get("python", "")).startswith(expected_python + " "):
            errors.append(f"Python provenance mismatch: {final_path.parent}")
        recorded_versions = provenance.get("packages", {})
        for package, expected in expected_versions.items():
            if recorded_versions.get(package) != expected:
                errors.append(
                    f"package provenance mismatch for {package}: {final_path.parent}"
                )
        rows.append(
            {
                **final,
                "protocol_id": protocol_id,
                "protocol_manifest_sha256": provenance.get("protocol_manifest_sha256"),
                "python": provenance.get("python"),
                "platform": provenance.get("platform"),
                "device": provenance.get("device"),
                "torch_version": provenance.get("packages", {}).get("torch"),
                "torchvision_version": provenance.get("packages", {}).get("torchvision"),
                "run_dir": final_path.parent.relative_to(REPO_ROOT).as_posix(),
                "resolved_config_sha256": _sha256(config_path),
                "configured_rounds": config.get("experiment", {}).get("rounds"),
            }
        )
    return pd.DataFrame(rows), errors


def _t_ci(values: np.ndarray, confidence: float = 0.95) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    if values.size < 2:
        return math.nan, math.nan
    mean = float(values.mean())
    sem = float(stats.sem(values))
    critical = float(stats.t.ppf((1.0 + confidence) / 2.0, values.size - 1))
    return mean - critical * sem, mean + critical * sem


def _exact_sign_flip_paired_pvalue(differences: np.ndarray) -> float:
    differences = np.asarray(differences, dtype=float)
    if differences.size == 0:
        return math.nan
    observed = abs(float(differences.mean()))
    extreme = 0
    total = 2 ** differences.size
    for signs in itertools.product((-1.0, 1.0), repeat=differences.size):
        statistic = abs(float(np.mean(differences * np.asarray(signs))))
        if statistic >= observed - 1e-15:
            extreme += 1
    return extreme / total


def _holm_adjust(values: pd.Series) -> pd.Series:
    indexed = [(index, float(value)) for index, value in values.items()]
    ordered = sorted(indexed, key=lambda pair: pair[1])
    adjusted: dict[int, float] = {}
    running = 0.0
    count = len(ordered)
    for rank, (index, value) in enumerate(ordered):
        candidate = min(1.0, (count - rank) * value)
        running = max(running, candidate)
        adjusted[index] = running
    return pd.Series(adjusted).reindex(values.index)


def _descriptive(frame: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    rows = []
    for keys, group in frame.groupby(["dataset", "attack", "method"], sort=True):
        dataset, attack, method = keys
        for metric in metrics:
            values = group[metric].astype(float).to_numpy()
            low, high = _t_ci(values)
            rows.append(
                {
                    "dataset": dataset,
                    "attack": attack,
                    "method": method,
                    "metric": metric,
                    "n": len(values),
                    "mean": float(values.mean()),
                    "sample_sd": float(values.std(ddof=1)),
                    "ci95_low": low,
                    "ci95_high": high,
                }
            )
    return pd.DataFrame(rows)


def _paired_comparisons(frame: pd.DataFrame, matrix: dict) -> pd.DataFrame:
    target_method = matrix["target_method"]
    baselines = [method for method in matrix["methods"] if method != target_method]
    directions = {item["name"]: item["direction"] for item in matrix["analysis"]["metrics"]}
    rows = []
    for dataset in sorted(frame["dataset"].unique()):
        for attack in sorted(frame["attack"].unique()):
            condition = frame[(frame["dataset"] == dataset) & (frame["attack"] == attack)]
            for metric, direction in directions.items():
                target = condition[condition["method"] == target_method][["seed", metric]]
                for baseline_method in baselines:
                    baseline = condition[condition["method"] == baseline_method][["seed", metric]]
                    paired = target.merge(baseline, on="seed", suffixes=("_target", "_baseline"))
                    raw_diff = (
                        paired[f"{metric}_target"].astype(float).to_numpy()
                        - paired[f"{metric}_baseline"].astype(float).to_numpy()
                    )
                    oriented = raw_diff if direction == "higher" else -raw_diff
                    low, high = _t_ci(raw_diff)
                    sd = float(oriented.std(ddof=1)) if len(oriented) > 1 else math.nan
                    rows.append(
                        {
                            "dataset": dataset,
                            "attack": attack,
                            "metric": metric,
                            "direction": direction,
                            "target_method": target_method,
                            "baseline_method": baseline_method,
                            "n_pairs": len(paired),
                            "target_mean": float(paired[f"{metric}_target"].mean()),
                            "baseline_mean": float(paired[f"{metric}_baseline"].mean()),
                            "mean_difference_target_minus_baseline": float(raw_diff.mean()),
                            "difference_ci95_low": low,
                            "difference_ci95_high": high,
                            "paired_cohens_dz_favoring_target": (
                                float(oriented.mean() / sd) if sd > 0.0 else math.nan
                            ),
                            "exact_two_sided_p": _exact_sign_flip_paired_pvalue(oriented),
                        }
                    )
    result = pd.DataFrame(rows)
    result["holm_adjusted_p"] = result.groupby(
        ["dataset", "attack", "metric"], group_keys=False
    )["exact_two_sided_p"].transform(_holm_adjust)
    result["holm_reject_0_05"] = result["holm_adjusted_p"] < 0.05
    return result


def _write_markdown(
    path: Path,
    validation: dict,
    descriptive: pd.DataFrame,
    comparisons: pd.DataFrame,
) -> None:
    lines = [
        "# TierGuard confirmatory-v1 report",
        "",
        f"Validation: **{validation['status']}** ({validation['observed_runs']}/{validation['expected_runs']} runs).",
        "",
        "The protocol uses six paired held-out seeds. All methods share the same hierarchy, client sampling, data partitions, local training, root set, rounds, and attack configuration. Exact two-sided paired sign-flip permutation tests are Holm-adjusted within each dataset × attack × metric family. Results are not promoted beyond this simulation scope.",
        "",
        "## Means and 95% t intervals",
        "",
        "| Dataset | Attack | Method | Clean accuracy | Attack success rate |",
        "|---|---|---|---:|---:|",
    ]
    pivot = descriptive.pivot_table(
        index=["dataset", "attack", "method"], columns="metric", values=["mean", "ci95_low", "ci95_high"]
    )
    for (dataset, attack, method), row in pivot.iterrows():
        clean = f"{row[('mean', 'clean_accuracy')]:.4f} [{row[('ci95_low', 'clean_accuracy')]:.4f}, {row[('ci95_high', 'clean_accuracy')]:.4f}]"
        asr = f"{row[('mean', 'attack_success_rate')]:.4f} [{row[('ci95_low', 'attack_success_rate')]:.4f}, {row[('ci95_high', 'attack_success_rate')]:.4f}]"
        lines.append(f"| {dataset} | {attack} | {method} | {clean} | {asr} |")
    lines.extend(
        [
            "",
            "## Paired inference",
            "",
            "Full pre-specified comparisons are in `paired_comparisons.csv`. A Holm rejection is reported only when the adjusted p-value is below 0.05; no post-hoc best-baseline selection is used.",
            "",
            f"Holm-adjusted rejections: {int(comparisons['holm_reject_0_05'].sum())}/{len(comparisons)}.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and analyze confirmatory-v1 outputs")
    parser.add_argument("--matrix", default="configs/confirmatory_v1/matrix.yaml")
    parser.add_argument("--results-root", default="results/confirmatory_v1")
    parser.add_argument("--out", default="artifacts/confirmatory_v1")
    args = parser.parse_args()

    ok, manifest_errors = verify_frozen_manifest(REPO_ROOT)
    if not ok:
        raise SystemExit("frozen protocol verification failed: " + "; ".join(manifest_errors))
    environment_ok, environment_errors = verify_runtime_environment(REPO_ROOT)
    if not environment_ok:
        raise SystemExit("pinned environment verification failed: " + "; ".join(environment_errors))
    matrix_path = (REPO_ROOT / args.matrix).resolve()
    if matrix_path != FROZEN_MATRIX_PATH:
        raise SystemExit(f"confirmatory-v1 requires the frozen matrix: {FROZEN_MATRIX_PATH}")
    matrix = _load_matrix(matrix_path)
    manifest_hash = frozen_manifest_sha256(REPO_ROOT)
    results_root = (REPO_ROOT / args.results_root).resolve()
    out = (REPO_ROOT / args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    frame, errors = _read_runs(results_root, matrix["protocol_id"], manifest_hash)

    expected = _expected_keys(matrix)
    observed_keys = [
        (str(row.dataset), str(row.method), str(row.attack), int(row.seed))
        for row in frame.itertuples()
    ]
    observed = set(observed_keys)
    missing = sorted(expected - observed)
    extras = sorted(observed - expected)
    duplicates = sorted({key for key in observed if observed_keys.count(key) > 1})
    if missing:
        errors.append(f"missing combinations: {missing}")
    if extras:
        errors.append(f"unexpected combinations: {extras}")
    if duplicates:
        errors.append(f"duplicate combinations: {duplicates}")
    commits = sorted(set(frame["git_commit"].dropna().astype(str))) if not frame.empty else []
    if len(commits) != 1:
        errors.append(f"expected one frozen git commit, observed: {commits}")
    if not frame.empty and any(frame["stability_failures"].astype(int) != 0):
        errors.append("one or more runs recorded non-finite-update stability failures")
    if not frame.empty:
        metrics = [item["name"] for item in matrix["analysis"]["metrics"]]
        non_finite = ~np.isfinite(frame[metrics].astype(float).to_numpy())
        if non_finite.any():
            errors.append("one or more confirmatory outcomes are non-finite")

    validation = {
        "status": "PASS" if not errors else "FAIL",
        "protocol_id": matrix["protocol_id"],
        "protocol_manifest_sha256": manifest_hash,
        "expected_runs": len(expected),
        "observed_runs": len(frame),
        "expected_seeds": matrix["seeds"],
        "git_commits": commits,
        "errors": errors,
    }
    (out / "campaign_validation.json").write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if errors:
        raise SystemExit("campaign validation failed; see campaign_validation.json")

    metrics = [item["name"] for item in matrix["analysis"]["metrics"]]
    frame.sort_values(["dataset", "attack", "method", "seed"]).to_csv(
        out / "per_run_metrics.csv", index=False
    )
    descriptive = _descriptive(frame, metrics)
    descriptive.to_csv(out / "descriptive_summary.csv", index=False)
    comparisons = _paired_comparisons(frame, matrix)
    comparisons.to_csv(out / "paired_comparisons.csv", index=False)
    _write_markdown(out / "CONFIRMATORY_REPORT.md", validation, descriptive, comparisons)

    checksum_lines = []
    for path in sorted(results_root.rglob("*")):
        if path.is_file() and path.name != "RAW_SHA256SUMS":
            checksum_lines.append(f"{_sha256(path)}  {path.relative_to(results_root).as_posix()}")
    (results_root / "RAW_SHA256SUMS").write_text(
        "\n".join(checksum_lines) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(validation, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
