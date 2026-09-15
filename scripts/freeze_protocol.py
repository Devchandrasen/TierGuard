from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tierguard.protocol import verify_frozen_manifest, write_frozen_manifest

REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Write or verify the confirmatory freeze manifest")
    parser.add_argument("--write", action="store_true", help="write a new manifest")
    args = parser.parse_args()
    if args.write:
        path = write_frozen_manifest(REPO_ROOT)
        print(f"wrote {path.relative_to(REPO_ROOT)}")
    ok, errors = verify_frozen_manifest(REPO_ROOT)
    if not ok:
        for error in errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)
    print("frozen protocol verified")


if __name__ == "__main__":
    main()
