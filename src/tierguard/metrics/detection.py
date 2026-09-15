from __future__ import annotations


def detection_scores(y_true: list[bool], scores: list[float], threshold: float | None = None) -> dict[str, float]:
    if not y_true or not scores:
        return {"detection_precision": 0.0, "detection_recall": 0.0, "detection_f1": 0.0}
    if threshold is None:
        ordered = sorted(scores)
        threshold = ordered[len(ordered) // 2]
    pred = [score >= threshold for score in scores]
    tp = sum(p and t for p, t in zip(pred, y_true))
    fp = sum(p and not t for p, t in zip(pred, y_true))
    fn = sum((not p) and t for p, t in zip(pred, y_true))
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    return {
        "detection_precision": precision,
        "detection_recall": recall,
        "detection_f1": f1,
    }
