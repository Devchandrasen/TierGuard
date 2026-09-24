"""Prepare and checksum the three real TierGuard 2 image benchmarks.

Run only in a dedicated data directory. The JSON manifest records file hashes
and class counts but does not substitute for a later protocol freeze.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from torchvision.datasets import CIFAR10, FashionMNIST, MNIST


DATASETS = (
    ("MNIST", MNIST, 60_000, 10_000),
    ("FashionMNIST", FashionMNIST, 60_000, 10_000),
    ("CIFAR10", CIFAR10, 50_000, 10_000),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def class_counts(targets: list[int]) -> dict[str, int]:
    counts = {str(label): 0 for label in range(10)}
    for label in targets:
        counts[str(int(label))] += 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--download-missing", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name, dataset_cls, train_size, test_size in DATASETS:
        train = dataset_cls(root=str(root), train=True, download=args.download_missing)
        test = dataset_cls(root=str(root), train=False, download=args.download_missing)
        if len(train) != train_size or len(test) != test_size:
            raise ValueError(f"Unexpected {name} train/test sizes")
        train_counts = class_counts(train.targets)
        test_counts = class_counts(test.targets)
        if min(train_counts.values()) <= 0 or min(test_counts.values()) <= 0:
            raise ValueError(f"{name} is missing at least one class")
        summary[name] = {
            "train_size": train_size,
            "test_size": test_size,
            "train_class_counts": train_counts,
            "test_class_counts": test_counts,
        }
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            files[path.relative_to(root).as_posix()] = sha256_file(path)
    if not files:
        raise ValueError("No dataset files were found")
    payload = {"datasets": summary, "files_sha256": files}
    manifest = args.manifest.resolve()
    if manifest.exists():
        raise FileExistsError(f"Refusing to replace existing manifest: {manifest}")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "manifest": str(manifest),
        "file_count": len(files),
        "datasets": {name: {"train": data["train_size"], "test": data["test_size"]}
                     for name, data in summary.items()},
        "status": "pass",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
