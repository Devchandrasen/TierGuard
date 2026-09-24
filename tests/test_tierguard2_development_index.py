from __future__ import annotations

import csv
import json

import yaml

from scripts.index_tierguard2_clean_development import EXPECTED, index_runs


def _write_run(root, method: str, seed: int, clip: float, dataset: str = 'fashionmnist'):
    path = root / method / str(seed) / str(clip)
    path.mkdir(parents=True)
    config = {
        'experiment': {'name': 'tierguard2_clean_development_source_attested',
                       'seed': seed, 'rounds': 40},
        'aggregation': {'method': method},
        'attack': {'name': 'none'},
        'data': {'dataset': dataset, 'test_size': 10000},
        'provenance': {'require_clean_git': True},
        'tierguard2': {'clip_reference_multiplier': clip,
                       'probes_per_class': 2, 'calibrated_gain_threshold': 1.0},
    }
    (path / 'resolved_config.yaml').write_text(yaml.safe_dump(config), encoding='utf-8')
    (path / 'final_metrics.json').write_text(json.dumps({
        'experiment_name': 'tierguard2_clean_development_source_attested',
        'final_round': 40, 'clean_accuracy': 0.8, 'macro_f1': 0.79,
        'attack_success_rate': None, 'stability_failures': 0,
    }), encoding='utf-8')
    (path / 'provenance.json').write_text(json.dumps({
        'git_commit': 'a' * 40, 'git_worktree_dirty': False,
        'config_sha256': 'b' * 64,
    }), encoding='utf-8')
    (path / 'partition_indices.json').write_text(json.dumps({'seed': seed}),
                                                 encoding='utf-8')
    with (path / 'metrics_per_round.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['round'])
        writer.writeheader()
        writer.writerows({'round': index} for index in range(1, 41))
    for round_idx in range(1, 41):
        (path / f'audit_round_{round_idx:03d}.json').write_text('{}', encoding='utf-8')
    return path


def test_clean_development_index_requires_all_matched_runs(tmp_path):
    assert len(EXPECTED) == 9
    for method, seed, clip in EXPECTED:
        _write_run(tmp_path, method, seed, clip)
    result = index_runs(tmp_path)
    assert result['complete']
    assert len(result['paired_clean_accuracy_differences']) == 6


def test_clean_development_index_catches_partition_mismatch(tmp_path):
    for method, seed, clip in EXPECTED:
        path = _write_run(tmp_path, method, seed, clip)
        if method == 'tierguard2' and seed == 2001 and clip == 16.0:
            (path / 'partition_indices.json').write_text('{"seed": 999}', encoding='utf-8')
    result = index_runs(tmp_path)
    assert not result['complete']
    assert 'non-identical paired partitions for seed 2001' in result['errors']


def test_clean_development_index_accepts_prespecified_mnist_matrix(tmp_path):
    for method, seed, clip in EXPECTED:
        _write_run(tmp_path, method, seed, clip, dataset='mnist')
    assert index_runs(tmp_path, dataset='mnist')['complete']
    assert not index_runs(tmp_path, dataset='cifar10')['complete']
