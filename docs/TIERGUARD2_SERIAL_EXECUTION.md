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

## Checkpoint: 27 September 2026, 04:07 UTC

Job 39247 finished with exit 0, 40 rounds, complete audits and zero stability
failures. The paired index now contains 3/9 records; its only error is the six
expected unattempted distributed/optimized-trigger cells. The new timestamped
index is `fashion_t2_attack_development_index_2026_09_27T040743Z.json`, SHA-256
`76d3bdc92534afb3c504979b64d7597e4eca8c4e2af6fcf5732a81d7f1ebda44`.
The source, partitions and attack instances match; copied seed-2003 records
were hash-checked and all populated per-round numeric fields are finite.

After the queue was verified empty, the guard submitted **39266.mgmt01** at
04:10:32 UTC, distributed backdoor seed 2001. It was verified state R and
the sole account job. No other submission was made. Evidence and validation
are saved separately in the Rajanmani output folder
`TierGuard2_Serial_2026-09-27T040743Z`; the previous 56-run archive is unchanged.

## Checkpoint: 27 September 2026, 05:07 UTC

Job 39266 completed with exit 0, 40 rounds, complete audits and zero stability
failures. The paired index now contains 4/9 records; only the five expected
unattempted cells are missing. The new index is
`fashion_t2_attack_development_index_2026_09_27T050744Z.json`, SHA-256
`8f67d3d7ce92c51f3ee5ed6f6ff2f8ad672f95d164eaa9998ddcc212afe8dd01`.
Source, partitions, attacks, copied-record hashes and finite populated
per-round fields pass verification.

After the queue was verified empty, the guard submitted **39286.mgmt01** at
05:10:14 UTC, distributed backdoor seed 2002. It was verified state R and
the sole account job. No other submission was made. The new evidence folder
is `TierGuard2_Serial_2026-09-27T050744Z` under Rajanmani/output. Earlier
evidence and the training checkout remain unchanged.

## Checkpoint: 27 September 2026, 11:33 UTC

The user reconnected after repeated SSH timeouts. Scheduler history confirms
39286 completed with exit 0 and walltime 00:09:49. Its 40 rounds, complete
audits, zero stability failures, source/partition/attack pairing and finite
populated metrics pass verification. Copied evidence hashes also match.
The index now contains 5/9 records, with only four expected unattempted cells:
`fashion_t2_attack_development_index_2026_09_27T113300Z.json`, SHA-256
`50d5116eb1ac01bff0b78fba1caf0778de0140009d0b3ce33424b302ec4c315c`.

After checking the account was empty, the guard submitted **39366.mgmt01**
at 11:35:08 UTC for distributed backdoor seed 2003. It was verified state R
and the sole live account job; no other submission was made. New evidence is
in `TierGuard2_Serial_2026-09-27T113300Z` under Rajanmani/output. Prior
archives and training checkouts remain unchanged.

## Checkpoint: 27 September 2026, 11:56 UTC

39366 completed with exit 0, 40 rounds, complete audits and zero stability
failures. Source, partitions, attack instances, finite populated metrics and
copied-record hashes pass verification. The paired index contains 6/9 records;
only the three unattempted optimized-trigger seeds are missing. Index:
`fashion_t2_attack_development_index_2026_09_27T115639Z.json`, SHA-256
`2a682d872a34ece38bc7a69eefb737fa9041f8d79b8374a204ce4cd9ee297251`.

After verifying the empty account queue, the guard submitted **39367.mgmt01**
at 11:58:56 UTC for defence-aware optimized-trigger seed 2001. It was verified
state R and the sole account job. No other submission was made. New evidence
is in `TierGuard2_Serial_2026-09-27T115639Z` under Rajanmani/output. Earlier
evidence and training checkouts remain unchanged.
