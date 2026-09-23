"""Minimal compute-node CUDA and dependency check; not a study run."""

from __future__ import annotations

import json

import cryptography
import torch
import torchvision


def main() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable on this compute node")
    device = torch.device("cuda:0")
    left = torch.arange(4096, device=device, dtype=torch.float32).reshape(64, 64)
    right = torch.eye(64, device=device)
    result = left @ right
    torch.cuda.synchronize(device)
    if not torch.equal(result, left):
        raise AssertionError("CUDA matrix multiplication failed")
    print(json.dumps({
        "status": "pass",
        "gpu": torch.cuda.get_device_name(device),
        "torch": torch.__version__,
        "torchvision": torchvision.__version__,
        "cryptography": cryptography.__version__,
        "cuda_runtime": torch.version.cuda,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
