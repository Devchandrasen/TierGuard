"""Paper-derived HFLMND reconstruction for a matched two-tier experiment.

Bi et al., Knowledge-Based Systems 336 (2026), 115270, Eqs. (4)--(15)
and Algorithm 1 specify NSFE, a binary hierarchical-clustering stage,
historical suspicion correction, and equal averaging of accepted models.
The article does not identify the linkage, a cluster-to-benign labelling
rule, a zero-denominator convention, or an all-rejected fallback.  These
choices are fixed and disclosed here; this is not the authors' source code.
"""

from __future__ import annotations

import numpy as np
import torch
from scipy.cluster.hierarchy import cut_tree, linkage
from scipy.spatial.distance import pdist
from torch.nn import functional as F

from .base import AggregationResult, BaseAggregator, stack_updates


def _minmax(vector: torch.Tensor) -> torch.Tensor:
    """Equation (4), interpreted per model vector; constant vectors map to zero."""
    low = torch.min(vector)
    width = torch.max(vector) - low
    if float(width) <= 1e-12:
        return torch.zeros_like(vector)
    return (vector - low) / width


def _inverted_minmax(values: np.ndarray) -> np.ndarray:
    """Equations (6) and (8); tied values provide no separating signal."""
    width = float(np.max(values) - np.min(values))
    if width <= 1e-12:
        return np.ones_like(values)
    return 1.0 - (values - np.min(values)) / width


def node_similarity_features(local_models: torch.Tensor,
                             superior_model: torch.Tensor) -> tuple[np.ndarray, np.ndarray]:
    """NSFE features in Eq. (10), with Eq. (5)'s j set to the superior model.

    Fig. 2 names the superior model as the reference.  The article does not
    explicitly resolve j in the equation text, so this interpretation is
    recorded as an adaptation choice rather than a verified code match.
    """
    reference = _minmax(superior_model.detach().cpu().float().flatten())
    normalized = torch.stack([_minmax(model) for model in local_models])
    dot = (normalized * reference).sum(dim=1).numpy().astype(np.float64)
    cosine = F.cosine_similarity(
        normalized, reference.unsqueeze(0), dim=1, eps=1e-12
    ).clamp(0, 1).numpy().astype(np.float64)
    euclidean = torch.linalg.vector_norm(
        normalized - reference.unsqueeze(0), dim=1
    ).numpy().astype(np.float64)
    dot_bar = _inverted_minmax(dot)
    euc_bar = _inverted_minmax(euclidean)
    features = np.column_stack((dot_bar, cosine * euc_bar, cosine, euc_bar))
    return features, euclidean


def _potential_malicious(features: np.ndarray, distance_to_superior: np.ndarray) -> np.ndarray:
    """Two-cluster MFC with disclosed average-linkage and labelling choices."""
    count = len(features)
    if count < 3 or float(np.max(pdist(features))) <= 1e-12:
        return np.zeros(count, dtype=bool)
    pairwise = pdist(features, metric="euclidean")
    labels = cut_tree(linkage(pairwise, method="average"), n_clusters=2).flatten()
    clusters = sorted(set(labels))
    # The paper does not say which of the two clusters is benign.  Under its
    # <50% malicious assumption, the larger cluster is the natural choice.
    # An exact tie is resolved by lower mean distance to the superior model.
    benign = min(
        clusters,
        key=lambda label: (
            -int(np.sum(labels == label)),
            float(np.mean(distance_to_superior[labels == label])),
            int(label),
        ),
    )
    return labels != benign


class HFLMNDAggregator(BaseAggregator):
    def aggregate(
        self,
        updates: list[torch.Tensor],
        weights=None,
        client_ids: list[int] | None = None,
        *,
        global_vector: torch.Tensor | None = None,
        edge_id: int = -1,
        history: dict[tuple[int, int], int] | None = None,
        **kwargs,
    ) -> AggregationResult:
        if global_vector is None:
            raise ValueError("HFLMND needs the current superior model vector")
        if client_ids is None or len(client_ids) != len(updates):
            raise ValueError("HFLMND needs stable node identities for historical scores")
        if len(set(client_ids)) != len(client_ids):
            raise ValueError("HFLMND node identities must be unique within a layer")
        if history is None:
            raise ValueError("HFLMND needs a persistent history mapping")
        stacked = stack_updates(updates)
        superior = global_vector.detach().cpu().float().flatten()
        if superior.numel() != stacked.shape[1]:
            raise ValueError("HFLMND superior model has the wrong dimension")
        local_models = stacked + superior.unsqueeze(0)
        features, distances = node_similarity_features(local_models, superior)
        malicious = _potential_malicious(features, distances)
        scores = []
        accepted = []
        for node_id, is_malicious in zip(client_ids, malicious):
            key = (int(edge_id), int(node_id))
            score = int(history.get(key, 0)) + (1 if is_malicious else -1)
            history[key] = score
            scores.append(score)
            # Eq. (15) and Sec. 4.4 require BOTH a benign current label
            # and a strictly negative updated history score.
            accepted.append(not is_malicious and score < 0)
        admitted = np.asarray(accepted, dtype=bool)
        if bool(admitted.any()):
            # Algorithm 1 averages accepted client/edge *models* equally.
            # Since each has the same superior model, equal update averaging
            # is algebraically identical. Dataset masses are not used here.
            combined = stacked[torch.from_numpy(admitted)].mean(dim=0)
        else:
            # The article leaves this case undefined. Freeze the superior
            # model rather than silently re-admitting rejected nodes.
            combined = torch.zeros_like(stacked[0])
        return AggregationResult(
            update=combined,
            suspicion=torch.from_numpy((~admitted).astype(np.float32)),
            reliability=float(admitted.mean()),
            anomaly_mass=float((~admitted).mean()),
            metadata={
                "mode": "hflmnd_paper_derived_reconstruction",
                "features": features.tolist(),
                "current_cluster_malicious": malicious.tolist(),
                "historical_scores": scores,
                "accepted_node_ids": [int(node_id) for node_id, keep in zip(client_ids, admitted) if keep],
                "all_rejected_frozen_update": not bool(admitted.any()),
                "linkage": "average",
                "cluster_label_rule": "larger_cluster_then_superior_distance",
                "equal_average_ignores_sample_masses": True,
            },
        )
