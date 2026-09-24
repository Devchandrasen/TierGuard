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


def inspect_root(root: Path, download_missing: bool = False) -> dict:
    summary = {}
    for name, dataset_cls, train_size, test_size in DATASETS:
        train = dataset_cls(root=str(root), train=True, download=download_missing)
        test = dataset_cls(root=str(root), train=False, download=download_missing)
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
    return {"datasets": summary, "files_sha256": files}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--download-missing", action="store_true")
    parser.add_argument("--verify", action="store_true",
                        help="Recompute every dataset file hash and class count")
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = args.manifest.resolve()
    if args.verify:
        if args.download_missing:
            raise ValueError("Verification cannot download or modify datasets")
        if not manifest.is_file():
            raise FileNotFoundError(manifest)
        expected = json.loads(manifest.read_text(encoding="utf-8"))
        actual = inspect_root(root)
        if actual != expected:
            raise ValueError("Dataset files, sizes, or class counts differ from manifest")
        print(json.dumps({"manifest": str(manifest), "status": "verified",
                          "file_count": len(actual["files_sha256"])}, sort_keys=True))
        return
    root.mkdir(parents=True, exist_ok=True)
    if manifest.exists():
        raise FileExistsError(f"Refusing to replace existing manifest: {manifest}")
    payload = inspect_root(root, download_missing=args.download_missing)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(json.dumps({
        "manifest": str(manifest),
        "file_count": len(payload["files_sha256"]),
        "datasets": {name: {"train": data["train_size"], "test": data["test_size"]}
                     for name, data in payload["datasets"].items()},
        "status": "pass",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
