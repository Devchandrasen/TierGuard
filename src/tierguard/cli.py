from __future__ import annotations

import argparse
import sys

from tierguard.config import load_config
from tierguard.fl.hierarchical_runner import run_experiment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tierguard")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run one experiment config")
    run.add_argument("--config", required=True)
    run.add_argument("overrides", nargs="*")
    return parser


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        config = load_config(args.config, args.overrides)
        run_dir = run_experiment(config, command="python -m tierguard.cli " + " ".join(argv))
        print(run_dir)


if __name__ == "__main__":
    main()
