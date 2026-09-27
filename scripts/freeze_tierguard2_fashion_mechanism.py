"""Issue a write-once DEVELOPMENT manifest after tests/source commit.

This does not change protocol_draft.yaml, issue a final freeze, or submit jobs.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess

from fashion_mechanism_common import ROOT, canonical_hash, cell_config, cells, digest
from tierguard.tierguard2_protocol import verify_tierguard2_environment

ENV = Path("/home/chandrasen.pandey/tierguard2_env_2026_09_23")
INPUTS = {
    "fashion_t2_attack_development_index_2026_09_27T145912Z.json":
        "dded43b3d024cf0a17f1ca472c2812ad4cd54da86222d0fa6bba41906cdd76f0",
    "fashion_attack_validity_index_2026_09_24.json":
        "432c72da0b14510ee73391dd0cd71b43ce2497c2d146ec8bbe71bc0b9c61083d",
    "calibration_clip8_source_attested.json":
        "8e68fc7cb73ebab9cadcbcb14794e8ae016e75a95dafa259549a3f7e323e2345",
    "datasets_manifest_2026_09_24.json":
        "e9a1fcb8c38de5577ba0c3bb5c84407009b4de68feb2c61ef2fd2ca15a6519bb",
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-commit", required=True)
    args = parser.parse_args()
    if ROOT != ENV / "project_fashion_mechanism_v1":
        raise ValueError("Manifest creation requires the new isolated HPC clone")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    if commit != args.expected_commit or dirty:
        raise ValueError("Source is not clean and pinned")
    errors = verify_tierguard2_environment(ROOT)
    if errors:
        raise ValueError(f"Environment mismatch: {errors}")
    for name, expected in INPUTS.items():
        if digest(ENV / name) != expected:
            raise ValueError(f"Prior input hash mismatch: {name}")
    datasets = json.loads((ENV / "datasets_manifest_2026_09_24.json").read_text())
    fashion_files = {name: value for name, value in datasets["files_sha256"].items()
                     if name.startswith("FashionMNIST/")}
    if not fashion_files or any(digest(ENV / "datasets" / name) != expected
                                for name, expected in fashion_files.items()):
        raise ValueError("FashionMNIST files do not match the pinned dataset manifest")
    prior_path = ENV / "fashion_t2_attack_development_index_2026_09_27T145912Z.json"
    prior = json.loads(prior_path.read_text())
    if not prior["complete"] or prior["errors"] or prior["observed_run_count"] != 9:
        raise ValueError("Previous panel was not valid/complete")
    partitions = {}
    for row in prior["runs"]:
        key = str(row["seed"])
        if key in partitions and partitions[key] != row["partition_sha256"]:
            raise ValueError("Prior paired partitions differ across attacks")
        partitions[key] = row["partition_sha256"]
    source_provenance = json.loads((Path(prior["runs"][0]["run_dir"]) / "provenance.json").read_text())
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    names = [name for name in tracked if name and
             (name.startswith(("src/", "configs/", "scripts/", "tests/")) or
              name in {".gitignore", ".python-version-tierguard2", "pyproject.toml",
                       "requirements-tierguard2-cu128.txt", "requirements-lock-cu128.txt"})]
    manifest = {
        "phase": "fashion_mechanism_v1", "status": "frozen_development_screen_not_confirmation",
        "created_utc": datetime.now(timezone.utc).isoformat(), "source_commit": commit,
        "cells": cells(), "config_hashes": {c["id"]: canonical_hash(cell_config(c)) for c in cells()},
        "source_files": {name: digest(ROOT / name) for name in sorted(names)},
        "environment_lock_sha256": digest(ROOT / "requirements-tierguard2-cu128.txt"),
        "python_version": platform.python_version(),
        "provenance_packages": source_provenance["packages"],
        "partition_hashes": partitions, "prior_panel_index": str(prior_path),
        "dataset_root": str(ENV / "datasets"), "dataset_file_sha256": fashion_files,
        "inputs": [{"path": str(ENV / name), "sha256": expected}
                   for name, expected in INPUTS.items()],
        "maximum_outstanding_account_jobs": 1,
        "stop_after_cells": 96, "automatic_retries": False,
    }
    target = ENV / "fashion_mechanism_v1_manifest.json"
    with target.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"path": str(target), "sha256": digest(target), "source_commit": commit,
                      "cells": len(cells()), "environment_errors": errors}, indent=2))

if __name__ == "__main__":
    main()
