"""Read-only preflight for the small CIFAR-10 green-car stress set.

The 30 source indices are not a standard test set.  This check makes their
class labels, their separation from all ordinary training/root examples, and
the attacker/held-out split explicit before any stress experiment is run.
"""

from __future__ import annotations

import argparse
import json

from tierguard.data.datasets import make_data_bundle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--seed", type=int, default=2001)
    args = parser.parse_args()
    config = {
        "experiment": {"seed": args.seed},
        "federated": {"num_clients": 60, "num_edges": 6, "batch_size": 64},
        "data": {
            "dataset": "cifar10",
            "root": args.data_root,
            "root_dataset_size": 200,
            "audit_search_size": 200,
            "audit_eval_size": 200,
            "three_way_root_split": True,
            "iid": True,
        },
        "attack": {"name": "semantic_green_car", "target_label": 2},
        "aggregation": {"method": "tierguard2"},
    }
    bundle = make_data_bundle(config)
    partitions = bundle.partition_indices
    semantic = partitions["semantic_green_car"]
    reserved = set(semantic["reserved_original_train_indices"])
    attacker = set(semantic["attacker_train_original_indices"])
    heldout = set(semantic["heldout_semantic_original_indices"])
    ordinary = set().union(*(
        set(indices) for indices in partitions["clients"].values()
    ))
    roots = set().union(*(
        set(indices) for indices in partitions["root_reserved"].values()
    ))
    if len(reserved) != 30 or len(attacker) != 20 or len(heldout) != 10:
        raise AssertionError("Unexpected semantic source-set cardinality")
    if attacker & heldout or attacker | heldout != reserved:
        raise AssertionError("Semantic attacker and held-out sets overlap or omit an index")
    if reserved & (ordinary | roots):
        raise AssertionError("Green-car images leaked into ordinary clients or roots")
    if len(bundle.semantic_test_loader.dataset) != 10:
        raise AssertionError("Semantic evaluation set must contain ten held-out images")
    print(json.dumps({
        "seed": args.seed,
        "semantic_source_size": len(reserved),
        "semantic_attacker_size": len(attacker),
        "semantic_heldout_size": len(heldout),
        "root_sizes": {name: len(indices) for name, indices in partitions["root"].items()},
        "ordinary_client_count": len(partitions["clients"]),
        "reserved_source_overlap": 0,
        "status": "pass",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
