from __future__ import annotations

from .base import AggregationResult as AggregationResult
from .base import BaseAggregator
from .brea_sim import BreaSimAggregator
from .fedavg import FedAvgAggregator
from .fltrust import FLTrustAggregator
from .flame_hierarchical import HierarchicalFlameAggregator
from .fedgame_hierarchical import HierarchicalFedGameAggregator
from .foolsgold import FoolsGoldAggregator
from .hfl_fedavg import HFLFedAvgAggregator
from .krum import KrumAggregator
from .median import MedianAggregator
from .multikrum import MultiKrumAggregator
from .rfa import RFAAggregator
from .roppfl_like import RoPPFLLikeAggregator
from .shield_like import ShieldLikeAggregator
from .tapfed_sim import TAPFedSimAggregator
from .tierguard import TierGuardAggregator
from .trimmed_mean import TrimmedMeanAggregator


def build_aggregator(method: str, config: dict, dimension: int | None = None) -> BaseAggregator:
    key = method.lower()
    mapping = {
        "fedavg": FedAvgAggregator,
        "hfl_fedavg": HFLFedAvgAggregator,
        "hfl_fltrust": FLTrustAggregator,
        "hfl_flame": HierarchicalFlameAggregator,
        "hfl_fedgame": HierarchicalFedGameAggregator,
        "hfl_trimmed_mean": TrimmedMeanAggregator,
        "hfl_rfa": RFAAggregator,
        "krum": KrumAggregator,
        "multikrum": MultiKrumAggregator,
        "median": MedianAggregator,
        "hfl_median": MedianAggregator,
        "trimmed_mean": TrimmedMeanAggregator,
        "rfa": RFAAggregator,
        "foolsgold": FoolsGoldAggregator,
        "fltrust": FLTrustAggregator,
        "roppfl_like": RoPPFLLikeAggregator,
        "roppfl_like_reimplementation": RoPPFLLikeAggregator,
        "shield_like": ShieldLikeAggregator,
        "shield_like_reimplementation": ShieldLikeAggregator,
        "tapfed_sim": TAPFedSimAggregator,
        "brea_sim": BreaSimAggregator,
        "tierguard": TierGuardAggregator,
    }
    if key not in mapping:
        raise ValueError(f"Unknown aggregation method: {method}")
    return mapping[key](config=config, dimension=dimension)
