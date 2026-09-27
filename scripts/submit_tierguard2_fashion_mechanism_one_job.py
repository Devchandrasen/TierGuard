"""At most ONE job per invocation, all-account guard, no retries or chaining.

Run from the new frozen clone's scripts directory. The default is dry-run.
An external hash-frozen manifest pins the source and all 96 configurations.
The completed first panel and its legacy guard/ledger remain unchanged.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import getpass
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fashion_mechanism_common import ROOT, cells, check_manifest, digest
from index_tierguard2_fashion_mechanism import index_runs, require
from submit_tierguard2_one_job import selected_job_ids

ENV = Path("/home/chandrasen.pandey/tierguard2_env_2026_09_23")
MANIFEST = ENV / "fashion_mechanism_v1_manifest.json"
LEDGER = ENV / "fashion_mechanism_v1_submission_ledger.jsonl"

def command(args, cwd=None):
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True, timeout=30)
    if proc.stderr.strip():
        raise ValueError(f"Unexpected command diagnostic: {proc.stderr.strip()}")
    return proc.stdout.strip()

def completed_job(job_id):
    require(bool(re.fullmatch(r"\d+\.mgmt01", job_id)), "invalid job id")
    history = json.loads(command(["/opt/pbs/bin/qstat", "-x", "-f", "-F", "json", job_id]))
    record = history["Jobs"][job_id]
    require(record["job_state"] == "F" and record.get("Exit_status") == 0,
            f"Previous job is not known to have finished successfully: {job_id}")
    return record

def check_ledger(records, index):
    submitted = []
    require(len(records) % 2 == 0, "ambiguous submission intent; never retry automatically")
    for offset in range(0, len(records), 2):
        intent, done = records[offset:offset + 2]
        require(intent.get("mode") == "submission_intent" and done.get("mode") == "submitted",
                "invalid ledger sequence")
        require(all(done.get(k) == v for k, v in intent.items() if k != "mode"),
                "intent/submission mismatch")
        require(intent["cell"] == cells()[len(submitted)], "non-prefix or duplicate ledger cell")
        require(bool(re.fullmatch(r"\d+\.mgmt01", done.get("job_id", ""))), "ambiguous job id")
        submitted.append(done)
    require(index["valid_partial"], f"Invalid or incomplete attempt: {index['errors']}")
    require([row["id"] for row in index["runs"]] == [row["cell"]["id"] for row in submitted],
            "ledger/results mismatch: unrecorded, missing or incomplete run")
    for row, ledger_row in zip(index["runs"], submitted):
        require(row["job_id"] == ledger_row["job_id"], "result belongs to a different scheduler job")
    return submitted

def append_record(record):
    with LEDGER.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()
    require(getpass.getuser() == "chandrasen.pandey", "wrong scheduler account")
    require(ROOT == ENV / "project_fashion_mechanism_v1", "wrong training checkout")
    require(digest(MANIFEST) == args.manifest_sha256, "manifest hash mismatch")
    manifest = json.loads(MANIFEST.read_text())
    import fcntl
    # Same cross-workflow lock as the original guard; it does not defeat a
    # human submitting directly but prevents concurrent guarded submissions.
    with (ENV / "single_job_submission.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        active = selected_job_ids(command(["/opt/pbs/bin/qselect", "-u", "chandrasen.pandey"]))
        require(not active, f"Account already has outstanding job(s): {active}")
        check_manifest(manifest)
        from tierguard.tierguard2_protocol import verify_tierguard2_environment
        require(not verify_tierguard2_environment(ROOT), "TierGuard 2 environment drift")
        for name, expected in manifest["dataset_file_sha256"].items():
            require(digest(Path(manifest["dataset_root"]) / name) == expected, "dataset file drift")
        git = str(ENV / "shared_bin/git")
        require(command([git, "rev-parse", "HEAD"], ROOT) == manifest["source_commit"] and
                not command([git, "status", "--porcelain"], ROOT), "source not clean/pinned")
        for item in manifest["inputs"]:
            require(digest(Path(item["path"])) == item["sha256"], "prior evidence input hash mismatch")
        prior = json.loads(Path(manifest["prior_panel_index"]).read_text())
        require(prior["complete"] and prior["errors"] == [] and prior["observed_run_count"] == 9,
                "previous bounded panel is not complete")
        records = [json.loads(line) for line in LEDGER.read_text().splitlines()] if LEDGER.exists() else []
        require(all(row.get("manifest_sha256") == args.manifest_sha256 and
                    row.get("source_commit") == manifest["source_commit"] for row in records),
                "ledger refers to a different frozen phase")
        index = index_runs(ROOT / "results_fashion_mechanism_v1", manifest)
        stamp = datetime.now(timezone.utc).strftime("%Y_%m_%dT%H%M%S_%fZ")
        index_path = ENV / f"fashion_mechanism_index_{stamp}.json"
        index["manifest_sha256"] = args.manifest_sha256
        with index_path.open("x", encoding="utf-8") as stream:
            json.dump(index, stream, indent=2, sort_keys=True)
            stream.write("\n")
        submitted = check_ledger(records, index)
        if submitted:
            completed_job(submitted[-1]["job_id"])
        else:
            completed_job("39388.mgmt01")
        if len(submitted) == len(cells()):
            print(json.dumps({"mode": "panel_complete_no_submission", "index": str(index_path)}))
            return
        cell = cells()[len(submitted)]
        # Check the all-account queue again immediately before the intent.
        active = selected_job_ids(command(["/opt/pbs/bin/qselect", "-u", "chandrasen.pandey"]))
        require(not active, f"Account became busy: {active}")
        record = {"time_utc": datetime.now(timezone.utc).isoformat(), "cell": cell,
                  "mode": "submission_intent" if args.submit else "dry_run",
                  "manifest_sha256": args.manifest_sha256,
                  "source_commit": manifest["source_commit"],
                  "validation_index": str(index_path), "validation_index_sha256": digest(index_path),
                  "account_jobs_before": active}
        if args.submit:
            append_record(record)
            job_id = command(["/opt/pbs/bin/qsub", "-v",
                              f"TG2_CELL_ID={cell['id']},TG2_MANIFEST_SHA256={args.manifest_sha256}",
                              str(ROOT / "scripts/tierguard2_fashion_mechanism_v1.pbs")])
            require(bool(re.fullmatch(r"\d+\.mgmt01", job_id)),
                    f"Ambiguous submission response {job_id!r}; STOP, do not retry")
            record = {**record, "mode": "submitted", "job_id": job_id}
            append_record(record)
        print(json.dumps(record, indent=2))

if __name__ == "__main__":
    main()
