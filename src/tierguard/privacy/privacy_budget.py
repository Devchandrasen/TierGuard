from __future__ import annotations

from .rdp_accountant import compute_epsilon


def privacy_accounting(config: dict, rounds: int) -> dict[str, float | bool]:
    privacy = config.get("privacy", {})
    fed = config.get("federated", {})
    enabled = bool(privacy.get("enabled", False))
    delta = float(privacy.get("delta", 1e-5))
    if not enabled:
        epsilon = 0.0
    else:
        sample_rate = float(fed.get("clients_per_round", 1)) / max(1.0, float(fed.get("num_clients", 1)))
        epsilon = compute_epsilon(
            float(privacy.get("dp_noise_multiplier", 0.0)),
            sample_rate,
            rounds,
            delta,
        )
    return {
        "privacy_enabled": enabled,
        "epsilon": epsilon,
        "delta": delta,
        "rounds": rounds,
        "client_edge_epsilon": epsilon,
        "edge_cloud_epsilon": epsilon,
    }
