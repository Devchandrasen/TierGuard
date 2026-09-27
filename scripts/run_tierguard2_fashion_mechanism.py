"""Run one frozen development cell on a GPU compute node, never on login."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from fashion_mechanism_common import (ROOT, cell_config, cells, check_manifest,
                                      cell_results, digest)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--cell-id", required=True)
    args = parser.parse_args()
    if digest(args.manifest) != args.manifest_sha256:
        raise ValueError("Manifest changed after guarded submission")
    manifest = json.loads(args.manifest.read_text())
    check_manifest(manifest)
    if not os.environ.get("PBS_JOBID"):
        raise RuntimeError("Full training requires a PBS compute-node job")
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required; refusing CPU fallback")
    from tierguard.tierguard2_protocol import verify_tierguard2_environment
    errors = verify_tierguard2_environment(ROOT)
    if errors:
        raise ValueError(f"Environment drift: {errors}")
    for name, expected in manifest["dataset_file_sha256"].items():
        if digest(Path(manifest["dataset_root"]) / name) != expected:
            raise ValueError(f"Dataset drift: {name}")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
    if commit != manifest["source_commit"] or dirty:
        raise ValueError("Training source is not the clean pinned commit")
    matches = [cell for cell in cells() if cell["id"] == args.cell_id]
    if len(matches) != 1:
        raise ValueError("Cell is not in the frozen development matrix")
    cell = matches[0]
    results = ROOT / "results_fashion_mechanism_v1"
    prior = cell_results(results, cell)
    if prior.exists() and any(prior.iterdir()):
        raise ValueError("Cell was attempted before; no automatic reruns")
    from tierguard.fl.hierarchical_runner import run_experiment
    run_dir = run_experiment(cell_config(cell), results_root=results / cell["variant"],
                             command=f"fashion_mechanism_v1 {cell['id']} manifest_sha256={digest(args.manifest)}")
    print(json.dumps({"cell_id": cell["id"], "run_dir": str(run_dir)}, sort_keys=True))

if __name__ == "__main__":
    main()
