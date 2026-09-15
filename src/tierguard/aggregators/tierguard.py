from __future__ import annotations

import torch
from torch.nn import functional as F

from .base import (
    AggregationResult,
    BaseAggregator,
    clip_by_norm,
    coordinate_trimmed_mean,
    geometric_median,
    normalize_weights,
    stack_updates,
)


def _sample_indices(dim: int, sample_size: int) -> torch.Tensor:
    if sample_size >= dim:
        return torch.arange(dim)
    generator = torch.Generator().manual_seed(12345)
    return torch.randperm(dim, generator=generator)[:sample_size]


class TierGuardAggregator(BaseAggregator):
    def _compute_scores(
        self,
        clipped: torch.Tensor,
        norms: torch.Tensor,
        median_norm: torch.Tensor,
        mad: torch.Tensor,
        reference: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        cfg = self.config.get("tierguard", {})
        z_norm = torch.abs(norms - median_norm) / mad
        z_cap = cfg.get("z_norm_cap")
        z_component = z_norm.clamp(max=float(z_cap)) if z_cap is not None else z_norm

        cos = F.cosine_similarity(clipped, reference.view(1, -1), dim=1)
        cos_anom = 1.0 - cos.clamp_min(0.0)
        idx = _sample_indices(clipped.size(1), int(cfg.get("sign_sample_size", 4096)))
        ref_sign = torch.sign(reference[idx])
        upd_sign = torch.sign(clipped[:, idx])
        sign_agree = (upd_sign == ref_sign.view(1, -1)).float().mean(dim=1)
        sign_anom = 1.0 - sign_agree
        raw = (
            float(cfg.get("norm_weight", 1.0)) * z_component
            + float(cfg.get("cosine_weight", 1.0)) * cos_anom
            + float(cfg.get("sign_weight", 0.5)) * sign_anom
        )

        absolute = (2.0 * (torch.sigmoid(raw) - 0.5)).clamp(0.0, 1.0)
        score_mode = str(cfg.get("score_mode", "absolute")).lower()
        if score_mode == "relative":
            center = raw.median()
            scale = torch.median(torch.abs(raw - center)) * 1.4826
            scale = scale.clamp_min(float(cfg.get("score_scale_floor", 0.10)))
            margin = float(cfg.get("score_margin", 0.05))
            excess = ((raw - center - margin) / scale).clamp_min(0.0)
            relative = (1.0 - torch.exp(-excess)).clamp(0.0, 1.0)
            absolute_cutoff = float(cfg.get("absolute_suspicion_cutoff", 0.90))
            suspicion = torch.where(absolute >= absolute_cutoff, torch.maximum(relative, absolute), relative)
        else:
            suspicion = absolute

        return {
            "z_norm": z_norm,
            "cosine": cos,
            "sign_agree": sign_agree,
            "raw": raw,
            "suspicion": suspicion,
            "absolute_suspicion": absolute,
        }

    def score_updates(
        self,
        updates: list[torch.Tensor],
        reference_update: torch.Tensor | None = None,
        base_weights: list[float] | torch.Tensor | None = None,
    ):
        cfg = self.config.get("tierguard", {})
        stacked = stack_updates(updates)
        norms = torch.linalg.vector_norm(stacked, dim=1)
        median_norm = norms.median()
        mad = torch.median(torch.abs(norms - median_norm)).clamp_min(1e-6)
        clip_multiplier = float(cfg.get("clip_multiplier", 2.0))
        clip_threshold = float(clip_multiplier * median_norm.clamp_min(1e-6))
        clipped = torch.stack([clip_by_norm(update, clip_threshold) for update in stacked])

        if reference_update is None or torch.linalg.vector_norm(reference_update) <= 1e-12:
            reference = clipped.mean(dim=0)
        else:
            reference = reference_update.detach().cpu().float()
        if torch.linalg.vector_norm(reference) <= 1e-12:
            reference = torch.ones_like(clipped[0])

        pre_scores = self._compute_scores(clipped, norms, median_norm, mad, reference)
        root_norm_multiplier = cfg.get("root_norm_multiplier")
        root_cap = None
        if root_norm_multiplier is not None and torch.linalg.vector_norm(reference) > 1e-12:
            root_cap = float(root_norm_multiplier) * float(torch.linalg.vector_norm(reference))
            root_cap_mode = str(cfg.get("root_cap_mode", "global")).lower()
            if root_cap_mode == "suspect_only":
                suspicion_cutoff = float(cfg.get("root_cap_suspicion", 0.65))
                z_cutoff = float(cfg.get("root_cap_z", 3.0))
                suspect = (pre_scores["suspicion"] >= suspicion_cutoff) | (pre_scores["z_norm"] >= z_cutoff)
                clipped = torch.stack(
                    [
                        clip_by_norm(row, min(clip_threshold, root_cap)) if bool(is_suspect) else row
                        for row, is_suspect in zip(clipped, suspect)
                    ]
                )
            elif root_cap_mode == "adaptive":
                anomaly_mass_pre = float(pre_scores["suspicion"].mean().item())
                max_suspicion_pre = float(pre_scores["suspicion"].max().item())
                if (
                    anomaly_mass_pre >= float(cfg.get("root_cap_anomaly", 0.55))
                    or max_suspicion_pre >= float(cfg.get("root_cap_suspicion", 0.65))
                ):
                    clipped = torch.stack([clip_by_norm(update, min(clip_threshold, root_cap)) for update in stacked])
            else:
                clip_threshold = min(clip_threshold, root_cap)
                clipped = torch.stack([clip_by_norm(update, clip_threshold) for update in stacked])

        scores = self._compute_scores(clipped, norms, median_norm, mad, reference)
        suspicion = scores["suspicion"]
        anomaly_mass = float(suspicion.mean().item())

        gamma = float(cfg.get("gamma", 4.0))
        effective_gamma = gamma
        if bool(cfg.get("adaptive_gamma", False)):
            tau_low = max(1e-6, float(cfg.get("tau_low", 0.25)))
            min_scale = float(cfg.get("min_gamma_scale", 0.20))
            scale = min(1.0, max(min_scale, anomaly_mass / tau_low))
            effective_gamma = gamma * scale

        weights = normalize_weights(base_weights, len(updates)) * torch.exp(-effective_gamma * suspicion)
        if weights.sum() <= 1e-12:
            weights = torch.ones_like(weights)
        weights = weights / weights.sum()
        return {
            "clipped": clipped,
            "weights": weights,
            "suspicion": suspicion,
            "anomaly_mass": anomaly_mass,
            "clip_threshold": clip_threshold,
            "root_cap": root_cap,
            "cosine": scores["cosine"],
            "sign_agree": scores["sign_agree"],
            "z_norm": scores["z_norm"],
            "raw_score": scores["raw"],
            "absolute_suspicion": scores["absolute_suspicion"],
            "effective_gamma": effective_gamma,
            "score_mode": str(cfg.get("score_mode", "absolute")).lower(),
        }

    def aggregate(self, updates, weights=None, reference_update=None, **kwargs):
        cfg = self.config.get("tierguard", {})
        scores = self.score_updates(updates, reference_update=reference_update, base_weights=weights)
        clipped_list = [row for row in scores["clipped"]]
        anomaly_mass = scores["anomaly_mass"]
        tau_low = float(cfg.get("tau_low", 0.25))
        tau_high = float(cfg.get("tau_high", 0.55))
        if anomaly_mass < tau_low:
            update = (scores["clipped"] * scores["weights"].view(-1, 1)).sum(dim=0)
            mode = "weighted_clipped_mean"
        elif anomaly_mass < tau_high:
            update = coordinate_trimmed_mean(
                clipped_list,
                beta=float(cfg.get("trim_beta", 0.2)),
                weights=scores["weights"],
            )
            mode = "weighted_trimmed_mean"
        else:
            update = geometric_median(clipped_list, weights=scores["weights"], max_iter=10)
            mode = "weighted_geometric_median"
        min_reliability = float(cfg.get("min_reliability", 0.05))
        reliability = min(1.0, max(min_reliability, 1.0 - anomaly_mass))
        return AggregationResult(
            update=update,
            weights=scores["weights"],
            suspicion=scores["suspicion"],
            reliability=reliability,
            anomaly_mass=anomaly_mass,
            metadata={
                "mode": mode,
                "clip_threshold": scores["clip_threshold"],
                "effective_gamma": scores["effective_gamma"],
                "score_mode": scores["score_mode"],
                "cosine": scores["cosine"].tolist(),
                "sign_agree": scores["sign_agree"].tolist(),
                "z_norm": scores["z_norm"].tolist(),
                "raw_score": scores["raw_score"].tolist(),
                "absolute_suspicion": scores["absolute_suspicion"].tolist(),
            },
        )
