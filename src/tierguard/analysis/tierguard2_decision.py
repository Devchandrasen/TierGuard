"""Prespecified primary decision rule for the TierGuard 2 confirmatory study."""

from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np
from scipy.stats import t


@dataclass(frozen=True)
class PrimaryDecision:
    selected_baseline: str
    mean_asr_reduction: float
    exact_two_sided_p: float
    mean_clean_accuracy_difference: float
    clean_accuracy_lower_95: float
    asr_margin_met: bool
    sign_flip_met: bool
    clean_noninferiority_met: bool
    superiority_claim_allowed: bool


def select_development_baseline(dev_asr: dict[str, np.ndarray]) -> str:
    """Select lowest pooled development ASR, with a frozen lexical tie-break."""
    if not dev_asr:
        raise ValueError("No development baselines")
    means = {}
    for name, values in dev_asr.items():
        array = np.asarray(values, dtype=float)
        if array.shape != (3, 9) or not np.isfinite(array).all():
            raise ValueError(f"Incomplete development matrix for {name}")
        means[name] = float(array.mean())
    return min(sorted(means), key=lambda name: means[name])


def exact_sign_flip_p(differences: np.ndarray) -> float:
    values = np.asarray(differences, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
        raise ValueError("Sign-flip test requires a finite vector")
    if len(values) > 20:
        raise ValueError("Exact enumeration is limited to 20 pairs")
    observed = abs(float(np.mean(values)))
    extreme = 0
    total = 1 << len(values)
    for signs in itertools.product((-1, 1), repeat=len(values)):
        statistic = abs(float(np.mean(values * np.asarray(signs))))
        if statistic >= observed - 1e-12:
            extreme += 1
    return extreme / total


def primary_decision(
    *,
    baseline_name: str,
    baseline_asr: np.ndarray,
    tierguard2_asr: np.ndarray,
    baseline_clean_accuracy: np.ndarray,
    tierguard2_clean_accuracy: np.ndarray,
) -> PrimaryDecision:
    """Arrays are seed-by-cell (12x9 ASR; 12x3 clean accuracy).

    ``baseline_name`` must already have been selected from the development
    results. This function deliberately has no baseline-selection step.
    """
    baseline_asr = np.asarray(baseline_asr, dtype=float)
    tierguard2_asr = np.asarray(tierguard2_asr, dtype=float)
    baseline_clean_accuracy = np.asarray(baseline_clean_accuracy, dtype=float)
    tierguard2_clean_accuracy = np.asarray(tierguard2_clean_accuracy, dtype=float)
    if (baseline_asr.shape != (12, 9) or tierguard2_asr.shape != (12, 9)
            or baseline_clean_accuracy.shape != (12, 3)
            or tierguard2_clean_accuracy.shape != (12, 3)):
        raise ValueError("Incomplete primary matrix: require 12 paired seeds, 9 ASR and 3 clean cells")
    if not all(np.isfinite(array).all() for array in (
        baseline_asr, tierguard2_asr, baseline_clean_accuracy,
        tierguard2_clean_accuracy,
    )):
        raise ValueError("Primary matrix contains missing or nonfinite outcomes")
    seed_asr = (baseline_asr - tierguard2_asr).mean(axis=1)
    asr_reduction = float(seed_asr.mean())
    p = exact_sign_flip_p(seed_asr)
    seed_clean = (tierguard2_clean_accuracy - baseline_clean_accuracy).mean(axis=1)
    clean_mean = float(seed_clean.mean())
    clean_se = float(seed_clean.std(ddof=1) / np.sqrt(len(seed_clean)))
    clean_lower = clean_mean - float(t.ppf(0.95, df=11)) * clean_se
    asr_gate = asr_reduction >= 0.05
    p_gate = p < 0.05
    clean_gate = clean_lower > -0.02
    return PrimaryDecision(
        selected_baseline=baseline_name,
        mean_asr_reduction=asr_reduction,
        exact_two_sided_p=p,
        mean_clean_accuracy_difference=clean_mean,
        clean_accuracy_lower_95=clean_lower,
        asr_margin_met=asr_gate,
        sign_flip_met=p_gate,
        clean_noninferiority_met=clean_gate,
        superiority_claim_allowed=asr_gate and p_gate and clean_gate,
    )
