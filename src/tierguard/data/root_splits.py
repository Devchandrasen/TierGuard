"""Disjoint, class-balanced root partitions for the TierGuard 2 protocol.

Indices refer to the dataset passed to :func:`stratified_root_split`.  The
caller is responsible for recording any enclosing ``Subset`` mapping.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from tierguard.data.partition import labels_to_numpy


def stratified_root_split(dataset, sizes: tuple[int, int, int], seed: int) -> dict[str, list[int]]:
    if any(size <= 0 for size in sizes):
        raise ValueError("Reference, search and evaluation roots must all be nonempty")
    labels = labels_to_numpy(dataset)
    requested = sum(sizes)
    if requested >= len(labels):
        raise ValueError("Root splits must leave examples for client training")
    classes = sorted(set(int(label) for label in labels))
    if any(size < len(classes) for size in sizes):
        raise ValueError("Each root split must contain at least one example per class")
    rng = np.random.default_rng(seed)
    by_class: dict[int, list[int]] = defaultdict(list)
    for index, label in enumerate(labels):
        by_class[int(label)].append(index)
    for indices in by_class.values():
        rng.shuffle(indices)
    output = {"reference": [], "search": [], "evaluation": []}
    names = tuple(output)
    # Balanced allocations differ by at most one example per class.  Reject
    # undersupplied classes rather than silently changing the protocol.
    for name, size in zip(names, sizes):
        per_class, remainder = divmod(size, len(classes))
        for class_rank, label in enumerate(classes):
            take = per_class + int(class_rank < remainder)
            if len(by_class[label]) < take:
                raise ValueError(f"Class {label} lacks examples for {name} root")
            output[name].extend(by_class[label][:take])
            del by_class[label][:take]
        rng.shuffle(output[name])
    output["clients"] = [index for indices in by_class.values() for index in indices]
    rng.shuffle(output["clients"])
    return output
