"""Submit exactly one approved FashionMNIST development cell to PBS.

Run on arc-hpc, outside the immutable training checkout. The default is a
dry-run. --submit requires an empty account queue, a matching clean source,
an unchanged PBS script, and no prior attempt for the selected cell. A local
flock prevents concurrent callers of this entry point from double-submitting.
There are no arrays, loops over submissions, retries or background chaining.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import getpass
import hashlib
import json
from pathlib import Path
import re
import subprocess


ENV_ROOT = Path("/home/chandrasen.pandey/tierguard2_env_2026_09_23")
CLONE = ENV_ROOT / "project_t2_attack_dev"
EXPECTED_COMMIT = "897b419efa8c47774efd8ed14c41e020ad4df31e"
PBS_SCRIPT = CLONE / "scripts/tierguard2_fashion_attack_development_clip8.pbs"
PBS_SHA256 = "f819e3da2dd40e6c82ef172a9167d7cb830868b8c2984dbe9002d78f0c42900c"
ATTACKS = (
    "unknown_patch_model_replacement",
    "distributed_backdoor",
    "defence_aware_optimized_trigger",
)
SEEDS = (2001, 2002, 2003)


def selected_job_ids(output: str) -> list[str]:
    """qselect returns all live account jobs, not only those in Q or R.

    Use qselect rather than qstat -u combined with JSON: on this PBS version,
    that combination emits a text table followed by an empty JSON object.
    Unknown output (including unfamiliar array syntax) fails closed.
    """
    job_ids = output.split()
    if any(not re.fullmatch(r"\d+\.mgmt01", job_id) for job_id in job_ids):
        raise ValueError("Unrecognized qselect response; refusing to submit")
    return sorted(set(job_ids))


def check_no_prior_attempt(results_root: Path, attack: str, seed: int) -> None:
    cell = results_root / attack / "alpha_0.3/mal_0.2" / f"seed_{seed}"
    if cell.exists() and any(cell.iterdir()):
        raise ValueError(f"Prior attempt exists; review it instead of rerunning: {cell}")


def command_output(command: list[str], *, cwd: Path | None = None) -> str:
    return subprocess.run(command, cwd=cwd, check=True, capture_output=True,
                          text=True, timeout=30).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attack", required=True, choices=ATTACKS)
    parser.add_argument("--seed", required=True, type=int, choices=SEEDS)
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()
    username = getpass.getuser()
    if username != "chandrasen.pandey":
        raise ValueError("This bounded launcher is only configured for arc-hpc")
    import fcntl  # Linux-only scheduler host; keep pure helpers testable on Windows.

    with (ENV_ROOT / "single_job_submission.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        active = selected_job_ids(command_output([
            "/opt/pbs/bin/qselect", "-u", username,
        ]))
        if active:
            raise ValueError(f"Account already has submitted jobs; no submission: {active}")
        git = str(ENV_ROOT / "shared_bin/git")
        commit = command_output([git, "rev-parse", "HEAD"], cwd=CLONE)
        if commit != EXPECTED_COMMIT or command_output([git, "status", "--porcelain"], cwd=CLONE):
            raise ValueError("Training checkout is not the expected clean source")
        if hashlib.sha256(PBS_SCRIPT.read_bytes()).hexdigest() != PBS_SHA256:
            raise ValueError("PBS script changed; refusing submission")
        check_no_prior_attempt(CLONE / "results/fashionmnist/tierguard2", args.attack, args.seed)
        log_path = ENV_ROOT / "single_job_submission_ledger.jsonl"
        previous = [json.loads(line) for line in log_path.read_text().splitlines()] if log_path.exists() else []
        if any(row.get("attack") == args.attack and row.get("seed") == args.seed for row in previous):
            raise ValueError("A submission intent already exists for this cell; inspect scheduler history")
        record = {
            "time_utc": datetime.now(timezone.utc).isoformat(),
            "attack": args.attack, "seed": args.seed, "source_commit": commit,
            "pbs_script_sha256": PBS_SHA256, "account_jobs_before": active,
            "mode": "dry_run" if not args.submit else "submission_intent",
        }
        if args.submit:
            # Persist intent before qsub. A lost/ambiguous qsub response must
            # require inspection, never an automatic retry or duplicate cell.
            with log_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, sort_keys=True) + "\n")
            job_id = command_output([
                "/opt/pbs/bin/qsub", "-v",
                f"TG2_ATTACK={args.attack},TG2_SEED={args.seed}", str(PBS_SCRIPT),
            ])
            if not re.fullmatch(r"\d+\.mgmt01", job_id):
                raise ValueError(f"Ambiguous qsub response: {job_id!r}; inspect before retrying")
            record.update({"mode": "submitted", "job_id": job_id})
            with log_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, sort_keys=True) + "\n")
        print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
