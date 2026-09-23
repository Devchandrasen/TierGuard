import numpy as np
import pytest

from tierguard.analysis.tierguard2_decision import (
    exact_sign_flip_p, primary_decision, select_development_baseline,
)


def test_exact_sign_flip_and_all_three_gates():
    assert exact_sign_flip_p(np.ones(12)) == 2 / 4096
    result = primary_decision(
        baseline_name="hfl_median",
        baseline_asr=np.full((12, 9), 0.40),
        tierguard2_asr=np.full((12, 9), 0.30),
        baseline_clean_accuracy=np.full((12, 3), 0.90),
        tierguard2_clean_accuracy=np.full((12, 3), 0.895),
    )
    assert result.superiority_claim_allowed
    assert result.mean_asr_reduction == pytest.approx(0.10)
    assert result.clean_accuracy_lower_95 == pytest.approx(-0.005)


def test_development_baseline_is_selected_before_confirmation():
    assert select_development_baseline({
        "hfl_rfa": np.full((3, 9), 0.3),
        "hfl_median": np.full((3, 9), 0.2),
    }) == "hfl_median"


def test_primary_decision_rejects_missing_cells_and_noisy_clean_drop():
    with pytest.raises(ValueError, match="Incomplete"):
        primary_decision(
            baseline_name="x", baseline_asr=np.zeros((11, 9)),
            tierguard2_asr=np.zeros((11, 9)),
            baseline_clean_accuracy=np.zeros((12, 3)),
            tierguard2_clean_accuracy=np.zeros((12, 3)),
        )
    result = primary_decision(
        baseline_name="x", baseline_asr=np.full((12, 9), 0.5),
        tierguard2_asr=np.full((12, 9), 0.4),
        baseline_clean_accuracy=np.full((12, 3), 0.9),
        tierguard2_clean_accuracy=np.full((12, 3), 0.85),
    )
    assert not result.clean_noninferiority_met
    assert not result.superiority_claim_allowed
