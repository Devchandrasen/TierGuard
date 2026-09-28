# TierGuard 2 serial HPC execution

**Original bounded panel complete (27 September 2026): 9/9 validated.**
It stopped as required. The user subsequently approved the separately bounded
[mechanism screen](TIERGUARD2_FASHION_MECHANISM_PHASE_2026-09-27.md).
The one-outstanding-account-job limit remains in force. See the final checkpoint below and the
[complete panel review](TIERGUARD2_FASHIONMNIST_PANEL_REVIEW_2026-09-27.md).

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

## Checkpoint: 27 September 2026, 12:56 UTC

39367 completed with exit 0 and walltime 00:11:16. Its 40 rounds, complete
audits, zero stability failures, source/partition/attack pairing and finite
populated metrics pass verification. Local copies match the recorded hashes.
The paired index contains 7/9 records; only optimized-trigger seeds 2002 and
2003 are missing. Index:
`fashion_t2_attack_development_index_2026_09_27T125640Z.json`, SHA-256
`264b9ecd0c47b0be7b8f2b0f917a978789d5c1cf49b9149c5ad2e60be8c5b8ab`.

After validation and an empty-account check, the guard submitted
**39385.mgmt01** at 12:59:48 UTC for optimized-trigger seed 2002. It was
verified state R and the sole account job. No other submission was made.
New evidence is in `TierGuard2_Serial_2026-09-27T125640Z` under
Rajanmani/output; prior evidence and training checkouts remain unchanged.

## Checkpoint: 27 September 2026, 13:57 UTC

39385 completed with exit 0 and walltime 00:11:32. Forty rounds, complete
audits, zero stability failures, matched source/partitions/attacks, finite
populated metrics and copied-record hashes pass validation. The index has
8/9 records; only optimized-trigger seed 2003 is missing. Index:
`fashion_t2_attack_development_index_2026_09_27T135711Z.json`, SHA-256
`ad5ec2e18a9168b9c1332f7f8a243b4e7d1c945221852918c46ab87030b81e11`.

Adverse performance is retained: optimized-trigger seed 2002 has ASR
0.5297777778, versus 0.0935555556 in seed 2001. No rerun, exclusion or
parameter change is made. Data validity does not establish defence efficacy.

After validation and an empty-account check, the guard submitted
**39388.mgmt01** at 14:00:50 UTC for the final optimized-trigger seed 2003.
It was verified state R and the sole account job. No other submission was
made. New evidence is in `TierGuard2_Serial_2026-09-27T135711Z` under
Rajanmani/output. Validate this last run and review all nine cells before
any further campaign; do not submit confirmation. Earlier evidence and
training checkouts remain unchanged.

## Final checkpoint: 27 September 2026, 14:59 UTC

39388 completed with exit 0 and walltime 00:11:49. Forty rounds, complete
audits, zero stability failures, exact source/partition/attack pairing and
finite populated metrics pass validation. The final index contains 9/9
records, is complete and has no errors:
`fashion_t2_attack_development_index_2026_09_27T145912Z.json`, SHA-256
`dded43b3d024cf0a17f1ca472c2812ad4cd54da86222d0fa6bba41906cdd76f0`.

The account-wide qselect was empty at completion and again at 15:08 UTC.
No next job was submitted. The existing hourly automation was paused on
panel completion. Do not proceed to another campaign or confirmation without
reviewing the full outcomes and a separately bounded next-stage decision.

The completed panel retains adverse optimized-trigger ASRs of 52.98% and
54.37% in seeds 2002 and 2003. The three-seed mean is 38.90%, despite lower
ASR than the undefended FedAvg comparator. This does not establish superiority
over robust methods or causal benefit of the cloud audit. The full review
reports all nine values and the missing comparisons.

New evidence is in `TierGuard2_FashionMNIST_Development_2026-09-27` under
Rajanmani/output. The portable package contains all nine TG2 attack runs,
nine paired FedAvg attack runs and nine clean/calibration-context runs;
the independent local check covers 1,080 round records, 360 TG2 attack
audits and 192 index/calibration-referenced file hashes. Source capsules
and a per-file SHA-256 manifest accompany the evidence. Earlier archives,
the original frozen study, HARP-DP and all training clones are unchanged.

## User-authorized next phase: 27 September 2026

After the nine-run panel and adverse outcomes were reported, the user approved
the proposed matched robust-baseline and risk-weighting ablation phase with
"ok karo". The separate mechanism-screen policy fixes 96 development cells,
three reused development seeds, no confirmation, one outstanding account job,
and mandatory successful completion/validation between submissions. This is
not permission to restore the cancelled batch queue.

The original v2 guard and ledger remain unchanged and cannot launch the new
phase. A new source-pinned guard and write-once manifest govern only
`project_fashion_mechanism_v1`. The original frozen study and all previous
training clones remain unchanged. Stop after the 96-cell screen for review;
any execution/provenance/validation uncertainty stops submission earlier.

The first new-phase job is **39399.mgmt01**, submitted at 15:56:21 UTC
for median / none / seed 2001 and verified as the sole running account job.
Source commit, manifest hash and guard hash are recorded in the new phase
document. The existing hourly heartbeat was updated and resumed for only
that 96-cell phase. Do not call the old nine-cell guard for further work.

## Mechanism checkpoint: 27 September 2026, 16:58 UTC

39399 completed with exit 0 and walltime 00:09:44. The new guard validated
1/96 cells with no errors: all 40 rounds, complete audits, zero stability
failures, finite populated metrics, frozen source/configuration/environment,
exact paired partitions and a consistent ledger. The local copy independently
passed all 51 file hashes and CSV/final metric checks. Median / none / seed
2001 has clean accuracy 0.8556 and macro-F1 0.8565363973966267; clean ASR is
undefined. This is one development seed, not a method comparison.

The dry-run and submission-time indices are
`fashion_mechanism_index_2026_09_27T170000_721239Z.json` and
`fashion_mechanism_index_2026_09_27T170215_999575Z.json`, both SHA-256
`f1dd8018b0b8dc5574cfb59d32cddf5c6c90d0138ccc8e4ca3f460e69c017916`.
Only genuinely unattempted cells are missing from this partial index.

With the account empty and both manifest/guard hashes verified, the guard
submitted **39403.mgmt01** at 17:02:16 UTC for median / none / seed 2002.
It was verified R and the sole account job. No second submission, retry,
tuning or confirmation was made. The new evidence, ledger and scheduler
snapshots are in `Rajanmani/output/TierGuard2_Mechanism_2026-09-27T165844Z`.
All frozen training clones and previous evidence remain unchanged.

## Mechanism checkpoint: 27 September 2026, 17:59 UTC

39403 completed F/exit 0, walltime 00:09:49. The guarded index now validates
2/96 cells with no errors and only 94 genuinely unattempted cells missing.
All 40 rounds, complete audits, finite populated metrics, zero stability
failures, frozen source/configuration/environment and exact paired partitions
pass validation. The new local copy passes all 51 file hashes and CSV/final
metric checks. Median / none / seed 2002 has accuracy 0.8615 and macro-F1
0.860873189628035. Clean ASR remains undefined; no inference is made.

The timestamped indices are
`fashion_mechanism_index_2026_09_27T180029_921958Z.json` (dry-run) and
`fashion_mechanism_index_2026_09_27T180241_023946Z.json` (submission),
both SHA-256
`2d43a448e5fd1c624855447089c2977784a1bcc1e4704385e9b049806a501c6a`.
After approved manifest/guard hash checks and an empty account check,
the guard submitted **39404.mgmt01** once at 18:02:41 UTC for median /
none / seed 2003. It was verified R and the sole account job.

Evidence is preserved under
`Rajanmani/output/TierGuard2_Mechanism_2026-09-27T175915Z`, including
ledger copies, scheduler snapshots, indices and all newly completed files.
No training retry, tuning, confirmation or second submission occurred.
Every frozen training clone and prior evidence remains unchanged.

## Mechanism checkpoint: 27 September 2026, 19:00 UTC

39404 completed F/exit 0, walltime 00:09:45. The new guarded index validates
3/96 cells with no errors and only 93 genuinely unattempted cells missing.
Median / none / seed 2003 has accuracy 0.8380 and macro-F1
0.8354947465848456; clean ASR is undefined. All 40 rounds, complete audits,
zero stability failures, finite populated metrics, frozen source/configuration/
environment/data and exact paired partitions pass validation. Local checks
cover all 153 raw-file hashes across the three completed clean runs, as well
as CSV/final/index agreement and round/audit completeness.

Indices `fashion_mechanism_index_2026_09_27T190144_320082Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_27T190335_492676Z.json` (submission)
share SHA-256
`58d9bfedbd451e0e9a20afd9700a71ecc8c234e793080eb84bb1c67d6e302997`.
Following approved hash checks and an empty account, the guard submitted
**39405.mgmt01** once at 19:03:35 UTC for median /
unknown_patch_model_replacement / seed 2001. It was verified R and the
sole account job.

Evidence is preserved in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-27T190016Z`.
The median clean subset is complete, but no comparative inference is made
from this partial screen. No retry, tuning, confirmation, clone edit or
additional submission occurred.

## Mechanism checkpoint: 27 September 2026, 20:00 UTC

39405 completed F/exit 0, walltime 00:09:32. The frozen guard validates
4/96 cells with no errors and only 92 genuinely unattempted cells missing.
Median / unknown_patch_model_replacement / seed 2001 has clean accuracy
0.8614, macro-F1 0.8619156723420935 and adverse ASR 0.8787777777777778.
The result is retained unchanged. All 40 rounds, complete audits, zero
stability failures, frozen inputs and paired partitions pass validation.
All 51 newly copied files match their indexed SHA-256 values.

The extra local checker initially assumed every round had evaluated metrics.
The frozen configuration and source specify evaluation every five rounds;
the frozen validator already permits the expected pre-evaluation blanks.
A separate local checker version verifies blanks exactly in rounds 1--4,
carry-forward entries and finite populated metrics. It passes; both local
checker versions and the initial diagnostic are preserved. No training
attempt failed or was retried, and the frozen guard was not changed.

Indices `fashion_mechanism_index_2026_09_27T200144_792835Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_27T200442_062136Z.json` (submission)
share SHA-256
`8d956f59c90f7582ac1f10f5156f12bf6559de1c93de5e56f1d9bc6327644bb4`.
After approved hash checks, successful validation and an empty account,
the guard submitted **39406.mgmt01** once at 20:04:42 UTC for median /
unknown_patch_model_replacement / seed 2002. It was verified R and the sole
account job. Evidence is in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-27T200017Z`.
No tuning, confirmation, clone edit or further submission occurred.

## Mechanism checkpoint: 27 September 2026, 21:01 UTC

39406 completed F/exit 0, walltime 00:09:34. The frozen guard validates
5/96 cells with no errors and only 91 genuinely unattempted cells missing.
Median / unknown_patch_model_replacement / seed 2002 has clean accuracy
0.8630, macro-F1 0.8650849318225526 and adverse ASR 0.7077777777777777.
The result is retained unchanged. Forty rounds, complete audits, zero
stability failures, frozen inputs and exact paired partitions pass validation.
All 51 newly copied files pass SHA-256 checks; local metrics agree with the
index and final record and follow the frozen five-round evaluation cadence.

Indices `fashion_mechanism_index_2026_09_27T210311_275079Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_27T210507_077728Z.json` (submission)
share SHA-256
`847ec07dc7139904580ce57b27ef24377fe364760d58acceb7a1b3b760d89079`.
After approved hash checks, successful validation and an empty account,
the guard submitted **39407.mgmt01** once at 21:05:07 UTC for median /
unknown_patch_model_replacement / seed 2003. It was verified R and the
sole account job. Evidence is preserved in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-27T210148Z`.
No retry, replacement, tuning, confirmation, clone edit or other submission
occurred. Both completed attack seeds' adverse outcomes remain in the record.

## Mechanism checkpoint: 27 September 2026, 22:02 UTC

39407 completed F/exit 0, walltime 00:09:44. The frozen guard validates
6/96 cells with no errors and only 90 genuinely unattempted cells missing.
Median / unknown_patch_model_replacement / seed 2003 has accuracy 0.8520,
macro-F1 0.8487135668567335 and ASR 0.3340. All three unknown-patch
seeds are complete; the earlier adverse ASRs remain unchanged. Forty rounds,
complete audits, zero stability failures, frozen inputs and exact paired
partitions pass validation. All 51 newly copied files pass SHA-256 checks;
local metrics match the final/index record and frozen evaluation cadence.

Indices `fashion_mechanism_index_2026_09_27T220417_761990Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_27T220623_984832Z.json` (submission)
share SHA-256
`459d4c2df1c49e0f3e9cdea280736475d710f232bd3e58e09facc6db28f97418`.
After approved hash checks, successful validation and an empty account,
the guard submitted **39408.mgmt01** once at 22:06:24 UTC for median /
distributed_backdoor / seed 2001, the next cell in this same bounded screen.
It was verified R and the sole account job. Evidence is preserved under
`Rajanmani/output/TierGuard2_Mechanism_2026-09-27T220249Z`.
No comparative inference, retry, tuning, confirmation, clone edit or other
submission occurred.

## Mechanism checkpoint: 27 September 2026, 23:04 UTC

39408 completed F/exit 0, walltime 00:13:07. The frozen guard validates
7/96 cells with no errors and only 89 genuinely unattempted cells missing.
Median / distributed_backdoor / seed 2001 has accuracy 0.8530,
macro-F1 0.8535090057786812 and ASR 0.012222222222222223. This is one
development seed of a baseline, not a method comparison. Prior adverse
unknown-patch results remain unchanged. All 40 rounds, complete audits,
zero stability failures, frozen inputs and exact paired partitions pass
validation. All 51 copied files pass SHA-256 checks; local metrics agree
with the final/index record and frozen five-round evaluation cadence.

Indices `fashion_mechanism_index_2026_09_27T230535_278503Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_27T230837_242959Z.json` (submission)
share SHA-256
`00bb0be148158cc1ec13eed6fdc0b2e74f22233c3357f3c815d5eeacc35419f4`.
After approved hash checks, successful validation and an empty account,
the guard submitted **39409.mgmt01** once at 23:08:37 UTC for median /
distributed_backdoor / seed 2002. It was verified R and the sole account
job. Evidence, ledgers and scheduler snapshots are preserved under
`Rajanmani/output/TierGuard2_Mechanism_2026-09-27T230420Z`.
No comparative inference, retry, tuning, confirmation, clone edit or other
submission occurred.

## Mechanism checkpoint: 28 September 2026, 00:06 UTC

39409 completed F/exit 0, walltime 00:13:14. The frozen guard validates
8/96 cells with no errors and only 88 genuinely unattempted cells missing.
Median / distributed_backdoor / seed 2002 has accuracy 0.8631,
macro-F1 0.8611206785526117 and ASR 0.005. These are descriptive development
values, not a method comparison. Prior outcomes, including adverse
unknown-patch ASRs, remain unchanged. All 40 rounds, complete audits,
zero stability failures, frozen inputs and exact paired partitions pass
validation. All 51 copied files pass SHA-256 checks; local metrics agree
with the final/index record and frozen five-round evaluation cadence.

Indices `fashion_mechanism_index_2026_09_28T000804_045809Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_28T000959_845582Z.json` (submission)
share SHA-256
`fe491e4aa1d129d802e67e173beae025cc290b65aa9947221a72bdafd3314d29`.
After approved hash checks, successful validation and an empty account,
the guard submitted **39410.mgmt01** once at 00:10:00 UTC for median /
distributed_backdoor / seed 2003. It was verified R and the sole account
job. Evidence, ledgers and scheduler snapshots are preserved under
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T000621Z`.
No comparative inference, retry, tuning, confirmation, clone edit or other
submission occurred.

## Mechanism checkpoint: 28 September 2026, 01:07 UTC

39410 completed F/exit 0, walltime 00:11:57. The frozen guard validates
9/96 cells with no errors and only 87 genuinely unattempted cells missing.
Median / distributed_backdoor / seed 2003 has accuracy 0.8550,
macro-F1 0.852810812595094 and ASR 0.004111111111111111. All three median
distributed-backdoor seeds are now complete. These descriptive development
values are not a method comparison; prior adverse unknown-patch outcomes
remain unchanged. All 40 rounds, complete audits, zero stability failures,
frozen inputs and exact paired partitions pass validation. All 51 copied
files pass SHA-256 checks; local metrics agree with the final/index record
and frozen five-round evaluation cadence.

Indices `fashion_mechanism_index_2026_09_28T010933_244111Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_28T011136_411537Z.json` (submission)
share SHA-256
`8832df1199dc093525ae17f435a557933d55bcdeea8a98b41d72bd240e8700d4`.
After approved hash checks, successful validation and an empty account,
the guard submitted **39411.mgmt01** once at 01:11:36 UTC for median /
defence_aware_optimized_trigger / seed 2001. It was verified R and the
sole account job. Evidence, ledgers and scheduler snapshots are preserved in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T010751Z`.
No comparative inference, retry, tuning, confirmation, clone edit or other
submission occurred. This continues the existing 96-cell screen, not the
earlier nine-cell candidate panel or another campaign.

## Mechanism checkpoint: 28 September 2026, 02:41 UTC heartbeat

39411 completed F/exit 0, walltime 00:13:51. The frozen guard validates
10/96 cells with no errors and only 86 genuinely unattempted cells missing.
Median / defence_aware_optimized_trigger / seed 2001 has accuracy 0.8502,
macro-F1 0.8492562304825864 and residual ASR 0.24033333333333334. This
adverse baseline outcome is retained without tuning, exclusion or replacement.
It is one development seed, not a method comparison. All 40 rounds,
complete audits, finite optimized-trigger artifacts, zero stability failures,
frozen inputs and exact paired partitions pass validation. All 91 copied
files pass SHA-256 checks; local metrics agree with the final/index record
and frozen five-round evaluation cadence.

Indices `fashion_mechanism_index_2026_09_28T024317_906547Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_28T032832_531465Z.json` (submission)
share SHA-256
`ff60b3d309b0db57490e10c7d7c7717f57bc162705a86ee7b75411fc44b89eff`.
Following the user's intervening status query, the account queue, full ledger
and approved manifest/guard hashes were checked again before continuation.
After successful validation and an empty account, the guard submitted
**39413.mgmt01** once at 03:28:32 UTC for median /
defence_aware_optimized_trigger / seed 2002. It was verified R and the sole
account job. Evidence, refreshed checks, ledgers and scheduler snapshots are
preserved in `Rajanmani/output/TierGuard2_Mechanism_2026-09-28T024137Z`.
No comparative inference, retry, tuning, confirmation, clone edit or other
submission occurred for this heartbeat. The existing 96-cell order is unchanged.

## Mechanism checkpoint: 28 September 2026, 03:41 UTC heartbeat

39413 completed F/exit 0, walltime 00:13:00. The frozen guard validates
11/96 cells with no errors and only 85 genuinely unattempted cells missing.
Median / defence_aware_optimized_trigger / seed 2002 has accuracy 0.8654,
macro-F1 0.8650128130882108 and residual ASR 0.13011111111111112.
The residual ASR is retained unchanged alongside seed 2001's 24.03% ASR;
no tuning, exclusion or replacement is made. These descriptive development
values are not a method comparison. All 40 rounds, complete audits, finite
optimized-trigger artifacts, zero stability failures, frozen inputs and exact
paired partitions pass validation. All 91 copied files pass SHA-256 checks;
local metrics agree with the final/index record and evaluation cadence.

Indices `fashion_mechanism_index_2026_09_28T034357_732294Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_28T034506_956193Z.json` (submission)
share SHA-256
`d6c30ecadbd0053a7ddfb83aa3d7ab71205d16f034156e0826583a8d76b6b7a5`.
After approved hash checks, successful validation and an empty account,
the guard submitted **39416.mgmt01** once at 03:45:07 UTC for median /
defence_aware_optimized_trigger / seed 2003. It was verified R and the sole
account job. Evidence, ledgers and scheduler snapshots are preserved under
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T034156Z`.
No comparative inference, retry, tuning, confirmation, clone edit or other
submission occurred for this heartbeat. The existing 96-cell order is unchanged.

## Mechanism checkpoint: 28 September 2026, 04:42 UTC heartbeat

39416 completed F/exit 0, walltime 00:12:08. The frozen guard validates
12/96 cells with no errors and only 84 genuinely unattempted cells missing.
The median subset is complete: three clean seeds and three seeds per attack.
The newest optimized-trigger cell (seed 2003) has accuracy 0.8520,
macro-F1 0.8497660839220946 and residual ASR 0.24122222222222223.
Every outcome, including the earlier adverse unknown-patch and residual
optimized-trigger ASRs, is retained without tuning, exclusion or replacement.
The partial development screen supports no matched method comparison.
All 40 rounds, complete audits, finite optimized artifacts, zero stability
failures, frozen inputs and exact paired partitions pass validation. The
local copy passes all 91 hashes, metric agreement and evaluation-cadence checks.

Indices `fashion_mechanism_index_2026_09_28T044743_701882Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_28T044955_923496Z.json` (submission)
share SHA-256
`e2eba78b54be19a9dd1e1e08e89451dd8d7e3b19344c3130b32cf66e4f4a6b06`.
After approved hash checks, successful validation and refreshed empty-account
and unchanged-ledger checks, the guard submitted **39420.mgmt01** once at
04:49:56 UTC for fltrust / none / seed 2001. It was verified R and the sole
account job. The ledger contains one matching intent/submitted pair for it.

Evidence, both indices, ledgers and scheduler snapshots are preserved under
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T044257Z`.
This continues the same frozen 96-cell screen, not a new campaign. Stop only
after the full screen, or earlier on execution/provenance/validation uncertainty.
No comparative inference, retry, tuning, confirmation, clone edit or other
submission occurred for this heartbeat. All previous evidence is unchanged.

## Mechanism checkpoint: 28 September 2026, 05:42 UTC heartbeat

39420 completed F/exit 0, walltime 00:07:37. The frozen guard validates
13/96 cells with no errors: all 12 median cells and fltrust / none / seed
2001. Only 83 genuinely unattempted cells are missing before submission.
The new clean cell has accuracy 0.8121 and macro-F1 0.8077987660174857.
Clean ASR is undefined: null in the index/final JSON and blank throughout
the CSV. These descriptive development values support no comparative inference.
All prior outcomes, including adverse ASRs, remain unchanged; no tuning,
exclusion or replacement is made.

All 40 rounds, 40 complete audits, zero stability failures, frozen inputs,
exact paired partitions and the full ledger/run prefix pass validation.
The local copy independently passes all 51 file hashes, exact file membership,
CSV/final/index agreement and the frozen five-round evaluation cadence.

Indices `fashion_mechanism_index_2026_09_28T054537_391288Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_28T054821_487952Z.json` (submission)
share SHA-256
`d1026d0f7e037e9fe35a92f5e08dc3fb371dbb7c435bb6b18c612ceaefff5623`.
After successful validation and refreshed empty-account, unchanged-ledger
and approved manifest/guard-hash checks, the guard submitted **39430.mgmt01**
once at 05:48:21 UTC for fltrust / none / seed 2002. It was verified R and
the sole account job; the ledger gained one matching intent/submitted pair.

Evidence, both copied indices, ledgers, hashes and scheduler snapshots are in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T054258Z`.
No retry, replacement, array, tuning, confirmation, clone edit, second
submission or another campaign occurred. The same frozen 96-cell order
remains in force; previous evidence is preserved.

## Mechanism checkpoint: 28 September 2026, 06:44 UTC heartbeat

39430 completed F/exit 0, walltime 00:07:44. The frozen guard validates
14/96 cells with no errors: all 12 median cells and FLTrust clean seeds
2001 and 2002. Only 82 genuinely unattempted cells are missing before submission.
The newest cell has accuracy 0.8031 and macro-F1 0.7862631414726295.
Clean ASR is null in final JSON/index and blank throughout the CSV, not zero.
Seed 2001's accuracy 0.8121 and macro-F1 0.8077987660174857 remain unchanged.
These descriptive development values support no comparative inference;
all prior outcomes are retained without tuning, exclusion or replacement.

All 40 rounds, complete audits, zero stability failures, frozen inputs,
exact paired partitions and the full ledger/run prefix pass validation.
The local copy passes all 51 hashes, exact file membership, metric agreement
and the frozen five-round evaluation cadence.

Indices `fashion_mechanism_index_2026_09_28T064552_937722Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_28T064821_653625Z.json` (submission)
share SHA-256
`723f9e6ee1cdfe69b7c7936263f1a712b9a99dea0a5a70fd5d39faafffcf7747`.
After validation and refreshed empty-account, unchanged-ledger and approved
manifest/guard-hash checks, the guard submitted **39441.mgmt01** once at
06:48:21 UTC for fltrust / none / seed 2003. It was verified R and the sole
account job. The ledger gained one matching intent/submitted pair.

Both copied indices, complete new run evidence, ledgers, hash checks and
scheduler snapshots are preserved under
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T064400Z`.
No retry, replacement, array, tuning, confirmation, clone edit, second
submission or another campaign occurred. Previous evidence is unchanged;
the same frozen 96-cell order remains in force.

## Mechanism checkpoint: 28 September 2026, 07:44 UTC heartbeat

39441 completed F/exit 0, walltime 00:07:53. The frozen guard validates
15/96 cells with no errors: all 12 median cells and all three FLTrust clean
seeds. Only 81 genuinely unattempted cells are missing before submission.
The newest cell (fltrust / none / seed 2003) has accuracy 0.7966 and
macro-F1 0.7886567798662272. Clean ASR is null in final JSON/index and
blank throughout the CSV. Seeds 2001 and 2002 retain accuracy 0.8121 and
0.8031 and macro-F1 0.8077987660174857 and 0.7862631414726295.
These descriptive development values support no comparative inference;
all prior outcomes are retained without tuning, exclusion or replacement.

All 40 rounds, complete audits, zero stability failures, frozen inputs,
exact paired partitions and the full ledger/run prefix pass validation.
The local copy passes all 51 hashes, exact file membership, metric agreement
and the frozen five-round evaluation cadence.

Indices `fashion_mechanism_index_2026_09_28T074842_969334Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_28T075039_020813Z.json` (submission)
share SHA-256
`2fb912775e7d815017745028e731706f255aaa65700087a053af711fa2826d65`.
After validation and refreshed empty-account, unchanged-ledger and approved
manifest/guard-hash checks, the guard submitted **39478.mgmt01** once at
07:50:39 UTC for fltrust / unknown_patch_model_replacement / seed 2001.
It was verified R and the sole account job. The ledger gained one matching
intent/submitted pair, reaching 32 rows.

Both copied indices, complete new run evidence, ledgers, hash checks and
scheduler snapshots are preserved under
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T074431Z`.
The validation skill guided completeness, null handling, independent metric
agreement and the development-only confidence assessment in VALIDATION.md.
No retry, replacement, array, tuning, confirmation, clone edit, second
submission or another campaign occurred. Previous evidence is unchanged;
the same frozen 96-cell order remains in force.

## Mechanism checkpoint: 28 September 2026, 08:45 UTC heartbeat

39478 completed F/exit 0, walltime 00:09:27. The frozen guard validates
16/96 cells with no errors: all median cells, all FLTrust clean seeds and
fltrust / unknown_patch_model_replacement / seed 2001.
Only 80 genuinely unattempted cells are missing before submission.
The newest cell has clean-test accuracy under attack 0.8107, macro-F1
0.8063727955403557 and adverse ASR 0.7796666666666666.
The 77.97% residual ASR is retained without tuning, exclusion or replacement.
These descriptive development values support no comparative inference.
Previous clean and attacked outcomes remain unchanged; clean-cell ASR is undefined.

All 40 rounds, complete audits, zero stability failures, frozen inputs,
exact paired partitions/attack instances and the full ledger/run prefix pass
validation. The local copy passes all 51 hashes, exact file membership,
final/index/CSV agreement, ASR-alias consistency and the five-round evaluation
cadence. Expected pre-evaluation blanks are not treated as missing runs.

Indices `fashion_mechanism_index_2026_09_28T084732_897872Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_28T084948_778875Z.json` (submission)
share SHA-256
`633f421faf76df06288cf6c707fac29ce44fa48e3c8649130ca17274ba0cddf3`.
After validation and refreshed empty-account, unchanged-ledger and approved
manifest/guard-hash checks, the guard submitted **39497.mgmt01** once at
08:49:48 UTC for fltrust / unknown_patch_model_replacement / seed 2002.
It was verified R and the sole account job. The ledger gained exactly one
matching intent/submitted pair, reaching 34 rows.

Both copied indices, complete new run evidence, validation report, ledgers,
hash checks and scheduler snapshots are preserved under
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T084532Z`.
No retry, replacement, array, tuning, confirmation, clone edit, second
submission or another campaign occurred. This remains the same frozen
96-cell screen; earlier evidence is unchanged.

## Mechanism checkpoint: 28 September 2026, 13:23 UTC heartbeat

39497 completed F/exit 0, walltime 00:03:01. The frozen guard validates
17/96 cells with no errors: all median cells, all FLTrust clean seeds and
unknown-patch/model-replacement seeds 2001 and 2002.
Only 79 genuinely unattempted cells are missing before submission.
The newest cell (seed 2002) has clean-test accuracy under attack 0.8091,
macro-F1 0.7960852645745459 and residual ASR 0.26. Seed 2001 retains accuracy
0.8107, macro-F1 0.8063727955403557 and adverse ASR 0.7796666666666666.
Both results are retained without tuning, exclusion or replacement. These
are different development seeds, not before/after evidence of a repair,
and support no comparative inference. Clean-cell ASR remains undefined.

All 40 rounds, complete audits, zero stability failures, frozen inputs,
exact paired partitions/attack instances and the full ledger/run prefix pass
validation. The local copy passes all 51 hashes, exact file membership,
final/index/CSV agreement, ASR-alias consistency and frozen evaluation cadence.
Walltime is preserved as provenance, not a hardware-normalized speed comparison.

Indices `fashion_mechanism_index_2026_09_28T132458_409899Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_28T132813_070491Z.json` (submission)
share SHA-256
`b9761349cda1737e4c8bad477797939dd894dccb7920e7bad75c8a6328b5d218`.
After validation and refreshed empty-account, unchanged-ledger and approved
manifest/guard-hash checks, the guard submitted **39522.mgmt01** once at
13:28:14 UTC for fltrust / unknown_patch_model_replacement / seed 2003.
It was verified R and the sole account job. The ledger gained exactly one
matching intent/submitted pair, reaching 36 rows.

Both copied indices, complete new run evidence, validation report, ledgers,
hash checks and scheduler snapshots are preserved under
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T132302Z`.
No retry, replacement, array, tuning, confirmation, clone edit, second
submission or another campaign occurred. This remains the same frozen
96-cell screen; earlier evidence is unchanged.

## Mechanism checkpoint: 28 September 2026, 14:23 UTC heartbeat

39522 completed F/exit 0, walltime 00:14:49. The frozen guard validates
18/96 cells with no errors: all median cells, all FLTrust clean seeds and
all three unknown-patch/model-replacement seeds.
Only 78 genuinely unattempted cells are missing before submission.
The newest cell (seed 2003) has clean-test accuracy under attack 0.7943,
macro-F1 0.7869355118352528 and residual ASR 0.049777777777777775.
Seed 2001's adverse ASR 0.7796666666666666 and seed 2002's ASR 0.26 remain
unchanged. All three results are retained without tuning, exclusion or rerun.
They are different development seeds, not before/after evidence of a repair;
no comparative inference is made. Clean-cell ASR remains undefined.

All 40 rounds, complete audits, zero stability failures, frozen inputs,
exact paired partitions/attack instances and the full ledger/run prefix pass
validation. The local copy passes all 51 hashes, exact file membership,
final/index/CSV agreement, ASR-alias consistency and frozen evaluation cadence.
Recorded-metric agreement does not independently recompute predictions.

Indices `fashion_mechanism_index_2026_09_28T142524_575705Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_28T143011_483468Z.json` (submission)
share SHA-256
`4ba8dc20f94fde59ae2b34e473241e65e20179f8917fe10942e39450a9cf3bb3`.
After validation and refreshed empty-account, unchanged-ledger and approved
manifest/guard-hash checks, the guard submitted **39536.mgmt01** once at
14:30:13 UTC for fltrust / distributed_backdoor / seed 2001.
It was verified R, non-rerunnable and the sole account job. The ledger gained
exactly one matching intent/submitted pair, reaching 38 rows.

Both copied indices, complete new run evidence, validation report, ledgers,
hash checks and scheduler snapshots are preserved under
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T142334Z`.
Completion of the FLTrust unknown-patch subset does not end the 96-cell phase.
No retry, replacement, array, tuning, confirmation, clone edit, second
submission or another campaign occurred. Earlier evidence is unchanged.

## Mechanism checkpoint: 28 September 2026, 15:24 UTC heartbeat

39536 completed F/exit 0, walltime 00:14:17. The frozen guard validates
19/96 cells with no errors: all 12 median cells, all FLTrust clean and
unknown-patch/model-replacement seeds, and distributed-backdoor seed 2001.
Only 77 genuinely unattempted cells are missing before submission.
The newest cell has clean-test accuracy under attack 0.8072, macro-F1
0.8008264683142536 and residual ASR 0.025. This is one development seed,
not a method comparison or a before/after repair. All previous outcomes,
including the adverse unknown-patch seeds, remain unchanged.
Clean-cell ASR remains undefined.

All 40 rounds, complete audits, zero stability failures, frozen inputs,
exact paired partitions/attack instances and the full ledger/run prefix pass
validation. The local copy passes all 51 hashes, exact file membership,
final/index/CSV agreement, ASR-alias consistency and frozen evaluation cadence.
The first-18 complete run records, including hashes, exactly match the prior
timestamped index. Recorded-metric agreement does not recompute predictions.
The validation skill guided completeness, null handling, spot-checks and the
development-only confidence assessment in the new VALIDATION.md.

Indices `fashion_mechanism_index_2026_09_28T152627_648936Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_28T153025_337660Z.json` (submission)
share SHA-256
`203041e54e4bd386442893a5802ff65b79f6360c1cd9e4e2081d976f408e6a14`.
After validation and refreshed empty-account, unchanged-ledger and approved
manifest/guard-hash checks, the guard submitted **39538.mgmt01** once at
15:30:25 UTC for fltrust / distributed_backdoor / seed 2002.
It was verified R, non-rerunnable and the sole account job. The ledger gained
exactly one matching intent/submitted pair, reaching 40 rows.

Both copied indices, complete new run evidence, validation report, ledgers,
hash checks and scheduler snapshots are preserved under
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T152404Z`.
No retry, replacement, array, tuning, confirmation, clone edit, second
submission or another campaign occurred. The same frozen 96-cell order
remains in force; previous evidence is unchanged.

## Mechanism checkpoint: 28 September 2026, 16:25 UTC heartbeat

39538 completed F/exit 0, walltime 00:04:40. The frozen guard validates
20/96 cells with no errors: all 12 median cells, all FLTrust clean and
unknown-patch/model-replacement seeds, and distributed-backdoor seeds
2001 and 2002. Only 76 genuinely unattempted cells are missing before
submission. The newest cell has clean-test accuracy under attack 0.8066,
macro-F1 0.7924789504946977 and residual ASR 0.004333333333333333.
Seed 2001 retains accuracy 0.8072, macro-F1 0.8008264683142536 and ASR
0.025. All outcomes, including adverse unknown-patch seeds, remain intact.
No partial-panel comparative inference is made; clean-cell ASR is undefined.

The initial account-wide queue query failed during SSH banner exchange.
No guard was invoked while scheduler state was uncertain. A fresh read-only
qselect query succeeded with exit 0 and was empty; this was not a training
or submission retry. The initial failure is retained with the successful
query and the separately refreshed pre-submission checks.

All 40 rounds, complete audits, zero stability failures, frozen inputs,
exact paired partitions/attack instances and the full ledger/run prefix pass
validation. The local copy passes all 51 hashes, exact file membership,
final/index/CSV agreement, ASR-alias consistency and frozen evaluation cadence.
The first-19 complete run records, including hashes, exactly match the prior
timestamped index. Recorded-metric agreement does not recompute predictions.
The validation skill guided completeness, null handling, spot-checks and
the development-only confidence assessment in the new VALIDATION.md.

Indices `fashion_mechanism_index_2026_09_28T162830_913902Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_28T163436_239440Z.json` (submission)
share SHA-256
`d4bd086b6346efa48f95555cc8dc6171ca617792db127f42eb63a23700c96b28`.
After validation and refreshed empty-account, unchanged-ledger and approved
manifest/guard-hash checks, the guard submitted **39540.mgmt01** once at
16:34:36 UTC for fltrust / distributed_backdoor / seed 2003.
It was verified R, non-rerunnable and the sole account job. The ledger gained
exactly one matching intent/submitted pair, reaching 42 rows; the previous
40 rows are unchanged.

Both copied indices, complete new run evidence, validation report, ledgers,
hash checks and scheduler snapshots are preserved under
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T162535Z`.
No retry, replacement, array, tuning, confirmation, clone edit, second
submission or another campaign occurred. The same frozen 96-cell order
remains in force; previous evidence is unchanged.

## Mechanism checkpoint: 28 September 2026, 17:25 UTC heartbeat

39540 completed F/exit 0, walltime 00:15:24. The frozen guard validates
21/96 cells with no errors: all 12 median cells, all FLTrust clean and
unknown-patch/model-replacement seeds, and all three distributed-backdoor
seeds. Only 75 genuinely unattempted cells are missing before submission.
The newest cell has clean-test accuracy under attack 0.7933, macro-F1
0.7851625604766831 and residual ASR 0.006888888888888889.
Seeds 2001 and 2002 retain accuracies 0.8072 and 0.8066, macro-F1
0.8008264683142536 and 0.7924789504946977, and ASRs 0.025 and
0.004333333333333333, respectively. All outcomes remain intact without
tuning, exclusion or rerun. No partial-panel comparison is made, and
clean-cell ASR remains undefined. Completion of this FLTrust subset
does not end the authorized 96-cell screen.

All 40 rounds, complete audits, zero stability failures, frozen inputs,
exact paired partitions/attack instances and the full ledger/run prefix pass
validation. The local copy passes all 51 hashes, exact file membership,
final/index/CSV agreement, ASR-alias consistency and frozen evaluation cadence.
The first-20 complete run records, including hashes, exactly match the prior
timestamped index. Recorded-metric agreement does not recompute predictions.
The validation skill guided completeness, null handling, spot-checks and
the development-only confidence assessment in the new VALIDATION.md.

Indices `fashion_mechanism_index_2026_09_28T172805_624197Z.json` (dry-run)
and `fashion_mechanism_index_2026_09_28T173136_756173Z.json` (submission)
share SHA-256
`c4ee957bd3b087a123acf390c7a6146091d49e42234cb8ab1336b7ac7a401ada`.
After validation and refreshed empty-account, unchanged-ledger and approved
manifest/guard-hash checks, the guard submitted **39546.mgmt01** once at
17:31:36 UTC for fltrust / defence_aware_optimized_trigger / seed 2001.
It was verified R, non-rerunnable and the sole account job. The ledger gained
exactly one matching intent/submitted pair, reaching 44 rows; the previous
42 rows are unchanged.

Both copied indices, complete new run evidence, validation report, ledgers,
hash checks and scheduler snapshots are preserved under
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T172536Z`.
No retry, replacement, array, tuning, confirmation, clone edit, second
submission or another campaign occurred. The same frozen 96-cell order
remains in force; previous evidence is unchanged.
