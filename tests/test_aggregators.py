from __future__ import annotations

import torch

from tierguard.aggregators import build_aggregator
from tierguard.aggregators.fedavg import FedAvgAggregator
from tierguard.aggregators.fltrust import FLTrustAggregator
from tierguard.aggregators.krum import KrumAggregator
from tierguard.aggregators.median import MedianAggregator
from tierguard.aggregators.rfa import RFAAggregator
from tierguard.aggregators.tierguard import TierGuardAggregator
from tierguard.aggregators.trimmed_mean import TrimmedMeanAggregator
from tierguard.fl.client import ClientUpdate
from tierguard.fl.hierarchical_runner import HIERARCHICAL_METHODS, _aggregate_round


def _cfg():
    return {
        "attack": {"malicious_fraction": 0.25},
        "aggregation": {"trim_beta": 0.2},
        "tierguard": {
            "clip_multiplier": 2.0,
            "gamma": 4.0,
            "tau_low": 0.25,
            "tau_high": 0.55,
            "trim_beta": 0.2,
            "norm_weight": 1.0,
            "cosine_weight": 1.0,
            "sign_weight": 0.5,
            "sign_sample_size": 16,
        },
    }


def test_fedavg_identical_updates():
    updates = [torch.ones(5), torch.ones(5), torch.ones(5)]
    result = FedAvgAggregator(_cfg()).aggregate(updates)
    assert torch.allclose(result.update, torch.ones(5))


def test_median_resists_outlier():
    updates = [torch.ones(4), torch.ones(4) * 1.1, torch.ones(4) * 100]
    result = MedianAggregator(_cfg()).aggregate(updates)
    assert torch.all(result.update < 2.0)


def test_trimmed_mean_resists_outlier():
    updates = [torch.ones(4), torch.ones(4) * 1.1, torch.ones(4) * 0.9, torch.ones(4) * 100]
    cfg = _cfg()
    cfg["aggregation"]["trim_beta"] = 0.25
    result = TrimmedMeanAggregator(cfg).aggregate(updates)
    assert torch.all(result.update < 2.0)


def test_krum_selects_honest_cluster():
    updates = [torch.tensor([1.0, 1.0]), torch.tensor([1.1, 0.9]), torch.tensor([0.9, 1.1]), torch.tensor([100.0, 100.0])]
    result = KrumAggregator(_cfg()).aggregate(updates)
    assert torch.linalg.vector_norm(result.update - torch.tensor([1.0, 1.0])) < 0.25


def test_rfa_close_to_honest_cluster():
    updates = [torch.tensor([1.0, 1.0]), torch.tensor([1.1, 0.9]), torch.tensor([0.9, 1.1]), torch.tensor([100.0, 100.0])]
    result = RFAAggregator(_cfg()).aggregate(updates)
    assert torch.linalg.vector_norm(result.update - torch.tensor([1.0, 1.0])) < 1.0


def test_fltrust_zero_weight_opposite_direction():
    updates = [torch.tensor([1.0, 0.0]), torch.tensor([-1.0, 0.0])]
    result = FLTrustAggregator(_cfg()).aggregate(updates, reference_update=torch.tensor([1.0, 0.0]))
    assert result.weights[1] < 1e-6


def test_matched_hierarchical_aliases_use_expected_aggregators():
    cfg = _cfg()
    assert isinstance(build_aggregator("hfl_fltrust", cfg), FLTrustAggregator)
    assert isinstance(build_aggregator("hfl_trimmed_mean", cfg), TrimmedMeanAggregator)
    assert isinstance(build_aggregator("hfl_rfa", cfg), RFAAggregator)
    assert {
        "hfl_fedavg",
        "hfl_fltrust",
        "hfl_trimmed_mean",
        "hfl_rfa",
    }.issubset(HIERARCHICAL_METHODS)


def test_matched_hierarchical_baselines_execute_two_level_route():
    updates = [
        ClientUpdate(torch.tensor([1.0, 0.0]), 0, 0, 2, False, 0.0, 1.0),
        ClientUpdate(torch.tensor([0.8, 0.2]), 1, 0, 2, False, 0.0, 1.0),
        ClientUpdate(torch.tensor([0.9, 0.1]), 2, 1, 2, False, 0.0, 1.0),
        ClientUpdate(torch.tensor([1.1, -0.1]), 3, 1, 2, False, 0.0, 1.0),
    ]
    reference = torch.tensor([1.0, 0.0])
    for method in ("hfl_fedavg", "hfl_fltrust", "hfl_trimmed_mean", "hfl_rfa"):
        cfg = _cfg()
        cfg["aggregation"]["method"] = method
        result, metadata, suspicion = _aggregate_round(updates, cfg, reference, model_dim=2)
        assert torch.isfinite(result).all()
        assert len(suspicion) == len(updates)
        assert metadata["cloud_reliability_mean"] > 0.0


def test_tierguard_suspicion_for_anomalies():
    tg = TierGuardAggregator(_cfg())
    ref = torch.ones(16)
    honest = torch.ones(16)
    large = torch.ones(16) * 100
    opposite = -torch.ones(16)
    low_sign = torch.tensor([1.0, -1.0] * 8)
    scores = tg.score_updates([honest, large, opposite, low_sign], reference_update=ref)["suspicion"]
    assert scores[1] > scores[0]
    assert scores[2] > scores[0]
    assert scores[3] > scores[0]


def test_tierguard_relative_scoring_preserves_honest_cluster():
    cfg = _cfg()
    cfg["tierguard"].update(
        {
            "clip_multiplier": 4.0,
            "gamma": 1.0,
            "adaptive_gamma": True,
            "min_gamma_scale": 0.15,
            "tau_low": 0.65,
            "tau_high": 0.85,
            "score_mode": "relative",
            "score_margin": 0.05,
            "score_scale_floor": 0.10,
            "absolute_suspicion_cutoff": 0.90,
            "z_norm_cap": 6.0,
        }
    )
    tg = TierGuardAggregator(cfg)
    ref = torch.ones(16)
    updates = [torch.ones(16), torch.ones(16) * 1.02, torch.ones(16) * 0.98, torch.ones(16) * 1.01]
    result = tg.aggregate(updates, reference_update=ref)
    assert result.anomaly_mass < cfg["tierguard"]["tau_low"]
    assert result.metadata["mode"] == "weighted_clipped_mean"
    assert float(result.weights.max() - result.weights.min()) < 0.05
