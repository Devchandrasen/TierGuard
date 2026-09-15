from __future__ import annotations


def vector_bytes(dimension: int, bits: int) -> int:
    return int(dimension * bits / 8)


def threshold_comm_cost(
    num_vectors: int,
    dimension: int,
    bits: int,
    committee_size: int,
) -> dict[str, float]:
    client_to_committee = num_vectors * committee_size * vector_bytes(dimension, bits)
    committee_to_agg = committee_size * vector_bytes(dimension, bits)
    return {
        "client_to_committee_bytes": float(client_to_committee),
        "committee_to_aggregator_bytes": float(committee_to_agg),
        "total_bytes": float(client_to_committee + committee_to_agg),
    }
