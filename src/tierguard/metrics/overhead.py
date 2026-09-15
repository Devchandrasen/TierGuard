from __future__ import annotations


def bytes_to_mb(num_bytes: float) -> float:
    return float(num_bytes) / (1024.0 * 1024.0)


def communication_mb(num_vectors: int, dimension: int, bits: int, fanout: int = 1) -> float:
    return bytes_to_mb(num_vectors * dimension * bits / 8 * fanout)
