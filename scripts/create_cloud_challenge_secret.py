"""Create one private cloud challenge key without printing or replacing it."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
from pathlib import Path


def create_secret(path: Path) -> str:
    target = path.resolve()
    if not target.parent.is_dir():
        raise FileNotFoundError(target.parent)
    key = secrets.token_bytes(32)
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(key)
    return hashlib.sha256(key).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    digest = create_secret(args.output)
    print(json.dumps({"path": str(args.output.resolve()),
                      "sha256": digest, "key_bytes": 32}, sort_keys=True))


if __name__ == "__main__":
    main()
