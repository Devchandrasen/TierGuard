"""Validate the nine prespecified FashionMNIST clean-development runs.

This tool reports completeness and paired clean utility; it does not select
parameters or make a confirmatory inference.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import yaml


SEEDS = (2001, 2002, 2003)
EXPECTED = {
    *(('tierguard2', seed, clip) for seed in SEEDS for clip in (8.0, 16.0)),
    *(('hfl_fedavg', seed, 8.0) for seed in SEEDS),
}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def index_runs(results_root: Path) -> dict:
    found = {}
    errors = []
    commits = set()
    partitions_by_seed: dict[int, dict] = {}
    for final_path in sorted(results_root.rglob('final_metrics.json')):
        run_dir = final_path.parent
        final = json.loads(final_path.read_text(encoding='utf-8'))
        if final.get('experiment_name') != 'tierguard2_clean_development_source_attested':
            continue
        config = yaml.safe_load((run_dir / 'resolved_config.yaml').read_text(encoding='utf-8'))
        provenance = json.loads((run_dir / 'provenance.json').read_text(encoding='utf-8'))
        method = str(config['aggregation']['method'])
        seed = int(config['experiment']['seed'])
        clip = float(config['tierguard2']['clip_reference_multiplier'])
        key = (method, seed, clip)
        if key not in EXPECTED:
            errors.append(f'unexpected development task: {key}')
            continue
        if key in found:
            errors.append(f'duplicate completed development task: {key}')
            continue
        if (config['data']['dataset'] != 'fashionmnist' or
                config['attack']['name'] != 'none' or
                int(config['experiment']['rounds']) != 40 or
                int(final['final_round']) != 40 or
                int(config['data']['test_size']) != 10000 or
                config.get('provenance', {}).get('require_clean_git') is not True or
                int(config['tierguard2']['probes_per_class']) != 2 or
                float(config['tierguard2']['calibrated_gain_threshold']) != 1.0):
            errors.append(f'protocol mismatch in {run_dir}')
        if provenance.get('git_worktree_dirty') is not False:
            errors.append(f'dirty source in {run_dir}')
        commits.add(str(provenance.get('git_commit')))
        with (run_dir / 'metrics_per_round.csv').open(newline='', encoding='utf-8') as stream:
            if len(list(csv.DictReader(stream))) != 40:
                errors.append(f'incomplete round metrics in {run_dir}')
        audit_files = list(run_dir.glob('audit_round_*.json'))
        if len(audit_files) != 40:
            errors.append(f'incomplete audit records in {run_dir}')
        partition_path = run_dir / 'partition_indices.json'
        if not partition_path.is_file():
            errors.append(f'missing explicit partition indices in {run_dir}')
        else:
            partitions = json.loads(partition_path.read_text(encoding='utf-8'))
            previous = partitions_by_seed.setdefault(seed, partitions)
            if previous != partitions:
                errors.append(f'non-identical paired partitions for seed {seed}')
        if final.get('attack_success_rate') is not None:
            errors.append(f'ASR should be undefined for clean run: {run_dir}')
        if int(final['stability_failures']) != 0:
            errors.append(f'non-finite update in {run_dir}')
        found[key] = {
            'method': method,
            'seed': seed,
            'clip_reference_multiplier': clip,
            'clean_accuracy': float(final['clean_accuracy']),
            'macro_f1': float(final['macro_f1']),
            'git_commit': provenance.get('git_commit'),
            'config_sha256': provenance.get('config_sha256'),
            'partition_sha256': _digest(partition_path) if partition_path.is_file() else None,
            'run_dir': str(run_dir),
        }
    missing = sorted(EXPECTED - found.keys())
    if missing:
        errors.append(f'missing completed tasks: {missing}')
    if len(commits) != 1:
        errors.append(f'mixed source commits: {sorted(commits)}')
    paired = []
    for seed in SEEDS:
        baseline = found.get(('hfl_fedavg', seed, 8.0))
        if baseline is None:
            continue
        for clip in (8.0, 16.0):
            candidate = found.get(('tierguard2', seed, clip))
            if candidate is not None:
                paired.append({
                    'seed': seed,
                    'clip_reference_multiplier': clip,
                    'candidate_minus_fedavg_accuracy': (
                        candidate['clean_accuracy'] - baseline['clean_accuracy']
                    ),
                })
    return {
        'complete': not errors,
        'expected_run_count': len(EXPECTED),
        'observed_run_count': len(found),
        'errors': errors,
        'runs': sorted(found.values(), key=lambda item: (
            item['method'], item['seed'], item['clip_reference_multiplier'])),
        'paired_clean_accuracy_differences': paired,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-root', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = index_runs(args.results_root)
    if args.output:
        if args.output.exists():
            raise FileExistsError(args.output)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n',
                               encoding='utf-8')
    print(json.dumps({key: result[key] for key in (
        'complete', 'expected_run_count', 'observed_run_count', 'errors')},
        indent=2))
    if not result['complete']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
