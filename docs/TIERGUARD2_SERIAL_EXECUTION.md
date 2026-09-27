# TierGuard 2 serial HPC execution

The user approved "yes one at time" on 27 September 2026 after the
administrator-requested cancellation of the queued campaign. This is a user
authorization; no additional administrator approval is represented here.

## Resource limit

At most **one outstanding job** may be submitted by this workflow. Count all
account jobs, including queued, running, held and exiting jobs. Never use
arrays, multiple qsub calls, background chaining or automatic retries. SSH,
scheduler, provenance or validation uncertainty means **no new submission**.
Existing completed evidence and the frozen training checkouts must be preserved.

The first resumed job is **39247.mgmt01**, submitted at
2026-09-27T02:59:34 UTC: FashionMNIST, TierGuard 2 clip 8,
unknown_patch_model_replacement, development seed 2003. It requests one GPU,
four CPUs, 24 GB RAM and a four-hour walltime limit. Training source remains
`897b419efa8c47774efd8ed14c41e020ad4df31e` in `project_t2_attack_dev`.

## Guarded submission

`scripts/submit_tierguard2_one_job.py` is deployed outside the training clone as
`/home/chandrasen.pandey/tierguard2_env_2026_09_23/submit_tierguard2_one_job_v2.py`.
Its SHA-256 is
`e27004394fc2b6e7d9008d644ef9dcf5ac538042782703c857484a96a1233a15`.
Version 1 submitted job 39247; version 2 corrects this PBS installation's
mixed text/JSON qstat output by checking all live account jobs with qselect.
The version-2 dry-run refused another submission while 39247 was running.

The guard defaults to dry-run and allows only the three FashionMNIST attack
conditions and seeds 2001, 2002, 2003. It verifies an empty account queue,
the clean source commit and exact PBS script hash. Any previous run attempt
or ledger submission intent blocks the same cell, even if incomplete.
An exclusive file lock serializes callers. The ledger is written before qsub,
so an ambiguous response requires inspection, never an automatic retry.
This protects this workflow; it cannot prevent a human or unrelated tool
from submitting directly to the scheduler.

## Bounded continuation

1. Inspect the scheduler and submission ledger. If any account job remains
   outstanding, submit nothing.
2. For the last completed job, verify scheduler exit status zero, 40 rounds,
   finite metrics, zero numerical-stability failures and complete audit files.
   Run the existing attack-development index against the fixed FedAvg index
   and clean calibration. Require exact source, partitions and attack pairing.
   Before 9/9 completion, only the expected missing-not-yet-run-cells error
   may remain; any other error stops further submissions.
3. Submit at most one next unattempted cell through version 2 of the guard.
   Order: finish unknown-patch seed 2003; distributed backdoor seeds
   2001--2003; defence-aware optimized trigger seeds 2001--2003.
4. Use new timestamped evidence/index filenames. Do not modify the earlier
   56-run archive or hide adverse outcomes.
5. Stop automatic submissions after this nine-cell FashionMNIST candidate
   panel. Review all results before advancing other campaigns, tuning,
   baseline selection or confirmation. This is development, not a
   confirmatory experiment or a superiority finding.

Hourly follow-up may carry out these steps, remaining quiet on unchanged
state and notifying only for meaningful completion, failure or a decision.
