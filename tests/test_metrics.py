from __future__ import annotations

from tierguard.metrics.detection import detection_scores


def test_detection_metrics_are_valid():
    scores = detection_scores([False, True, True, False], [0.1, 0.9, 0.8, 0.2], threshold=0.5)
    assert scores["detection_precision"] == 1.0
    assert scores["detection_recall"] == 1.0
    assert scores["detection_f1"] == 1.0
