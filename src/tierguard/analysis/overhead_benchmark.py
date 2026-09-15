from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd
import yaml

from tierguard.security.collusion_analysis import collusion_summary
from tierguard.security.comm_cost import threshold_comm_cost


def _as_list(value):
    return value if isinstance(value, list) else [value]


def run_overhead_benchmark(config_path: str | Path, out: str | Path) -> pd.DataFrame:
    config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}
    sec = config.get("security", {})
    grid = config.get("overhead", {})
    rows = []
    for num_clients in _as_list(grid.get("num_clients", [50])):
        for num_edges in _as_list(grid.get("num_edges", [5])):
            for dim in _as_list(grid.get("model_dimension", [100000])):
                for bits in _as_list(grid.get("quantization_bits", [16])):
                    start = time.time()
                    edge_comm = threshold_comm_cost(
                        int(num_clients),
                        int(dim),
                        int(bits),
                        int(sec.get("edge_committee_size", 3)),
                    )
                    cloud_comm = threshold_comm_cost(
                        int(num_edges),
                        int(dim),
                        int(bits),
                        int(sec.get("cloud_committee_size", 5)),
                    )
                    elapsed = time.time() - start
                    collusion = collusion_summary(
                        int(sec.get("edge_committee_size", 3)),
                        int(sec.get("edge_threshold", 2)),
                    )
                    dropout = float(sec.get("dropout_fraction", 0.0))
                    available = int(sec.get("edge_committee_size", 3)) - int(
                        round(int(sec.get("edge_committee_size", 3)) * dropout)
                    )
                    success = available >= int(sec.get("edge_threshold", 2))
                    total_bytes = edge_comm["total_bytes"] + cloud_comm["total_bytes"]
                    rows.append(
                        {
                            "dataset": "overhead",
                            "method": "tierguard",
                            "attack": "none",
                            "seed": config.get("experiment", {}).get("seed", 1),
                            "num_clients": int(num_clients),
                            "num_edges": int(num_edges),
                            "model_dimension": int(dim),
                            "quantization_bits": int(bits),
                            "threshold": int(sec.get("edge_threshold", 2)),
                            "committee_size": int(sec.get("edge_committee_size", 3)),
                            "dropout_fraction": dropout,
                            "reconstruction_success": bool(success),
                            "quantization_error_estimate": 1.0 / (2 ** max(1, int(bits) // 2)),
                            "aggregation_runtime_sec": elapsed,
                            "client_to_edge_bytes": edge_comm["total_bytes"],
                            "edge_to_cloud_bytes": cloud_comm["total_bytes"],
                            "total_comm_mb": total_bytes / (1024 * 1024),
                            "communication": total_bytes / (1024 * 1024),
                            **collusion,
                        }
                    )
    frame = pd.DataFrame(rows)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False)
    return frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    run_overhead_benchmark(args.config, args.out)


if __name__ == "__main__":
    main()
