"""Documented two-tier FLAME adaptation of Nguyen et al., USENIX Security 2022.

The paper's cosine/HDBSCAN majority filter, median-norm clipping, equal
averaging and adaptive Gaussian noising are applied independently at each
hierarchy level. The published flat-server guarantee is not transferred to
this adaptation. Noise is keyed by seed/round/edge for challenge replay.
"""

from __future__ import annotations

import numpy as np
import torch
from sklearn.cluster import HDBSCAN
from torch.nn import functional as F

from .base import AggregationResult, BaseAggregator, clip_by_norm, stack_updates


class HierarchicalFlameAggregator(BaseAggregator):
    def aggregate(self, updates, weights=None, *, round_idx=0, edge_id=-1,
                  global_vector=None, **kwargs):
        settings = self.config.get("flame", {})
        if "noise_multiplier" not in settings:
            raise ValueError("Hierarchical FLAME needs a development-tuned noise_multiplier")
        stacked = stack_updates(updates)
        n = stacked.shape[0]
        norms = torch.linalg.vector_norm(stacked, dim=1)
        bound = float(torch.quantile(norms, 0.5).clamp_min(1e-12))
        admitted = np.ones(n, dtype=bool)
        labels = np.zeros(n, dtype=int)
        if n >= 3:
            # The paper's pairwise cosine compares local model vectors W_i,
            # while Euclidean clipping is relative to the global model.
            if global_vector is None:
                raise ValueError("FLAME needs the current global model vector")
            local_models = stacked + global_vector.detach().cpu().float().view(1, -1)
            unit = F.normalize(local_models, p=2, dim=1)
            distances = (1.0 - unit @ unit.T).clamp(0.0, 2.0).numpy()
            np.fill_diagonal(distances, 0.0)
            labels = HDBSCAN(
                min_cluster_size=n // 2 + 1,
                min_samples=1,
                metric="precomputed",
                allow_single_cluster=True,
                copy=True,
            ).fit_predict(distances)
            valid = labels[labels >= 0]
            if len(valid):
                values, counts = np.unique(valid, return_counts=True)
                majority = int(values[np.argmax(counts)])
                admitted = labels == majority
            # If no stable cluster exists at a small edge, retain all and
            # disclose this failure rather than silently dropping all updates.
        selected = [clip_by_norm(update, bound) for update, keep
                    in zip(stacked, admitted) if keep]
        combined = torch.stack(selected).mean(dim=0)
        noise_multiplier = float(settings["noise_multiplier"])
        if noise_multiplier < 0:
            raise ValueError("FLAME noise multiplier cannot be negative")
        generator = torch.Generator(device="cpu").manual_seed(
            int(self.config.get("experiment", {}).get("seed", 1))
            + int(round_idx) * 100_003 + (int(edge_id) + 1) * 1009
        )
        if noise_multiplier:
            combined = combined + torch.randn(
                combined.shape, generator=generator, dtype=combined.dtype
            ) * (noise_multiplier * bound)
        suspicion = torch.tensor((~admitted).astype(np.float32))
        return AggregationResult(
            update=combined,
            suspicion=suspicion,
            reliability=float(admitted.mean()),
            anomaly_mass=float((~admitted).mean()),
            metadata={
                "mode": "hierarchical_flame_adaptation",
                "clustering_labels": labels.tolist(),
                "no_stable_cluster": bool(n >= 3 and not np.any(labels >= 0)),
                "clip_bound": bound,
                "noise_multiplier": noise_multiplier,
                "equal_weighted_admitted_count": len(selected),
            },
        )
