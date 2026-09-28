# Bounded FashionMNIST mechanism screen (development only)

## Authorization and question

After reviewing the completed nine-run panel and its residual optimized-trigger
ASRs of 52.98% and 54.37%, the user approved proceeding with matched robust
baselines, ablations and failure analysis on 27 September 2026 ("ok karo").
This phase asks whether the counterfactual risk weights add benefit beyond
clipping, and how the candidate compares with three established robust
aggregators at the same topology. It is not a superiority trial or a repair
of the observed outcomes. Earlier raw records and source clones are unchanged.

## Matrix and resource limit

Eight variants, four conditions, three paired development seeds: **96 runs**.
Only ONE outstanding job (queued, running, held or exiting) is allowed across
the entire account. No arrays, batch submissions, background submission chains
or automatic retries. A completed run must validate before the next submission.

| Variant | Edge aggregation | Cloud aggregation |
| --- | --- | --- |
| median | Coordinate lower median | Coordinate lower median |
| fltrust | FLTrust using trusted reference update | Same FLTrust rule on edge aggregates |
| rfa | Sample-mass-weighted geometric median | Same rule with represented edge sample mass |
| clip_only | Norm clipping, sample-weighted average | Same; no risk weighting |
| client_only | Clipping and client risk weights | Clipping and sample-weighted average |
| cloud_only | Clipping and sample-weighted average | Clipping and edge risk weights |
| full | Clipping and client risk weights | Clipping and edge risk weights |
| fedavg | Sample-weighted average | Sample-weighted average |

Condition order within each variant: clean training (none), unknown patch with
model replacement, distributed backdoor, defence-aware optimized trigger.
Seeds within each condition: 2001, 2002, 2003. Variant order is the table order.
The first cell is **median / none / 2001**. All are 40-round runs; no best-round
selection. Clean runs have no malicious clients and undefined ASR.

The new full and FedAvg runs are explicit same-source development replications,
not replacements for earlier evidence and not new independent confirmatory
seeds. Old outcomes remain separately reported, not pooled as extra seeds.
The completed screen must be reviewed before any further campaign.

## Fixed configuration and fairness

`configs/tierguard2/fashion_mechanism_v1.yaml` fixes FashionMNIST, 60 clients,
six edges, five clients per edge/round, two local epochs, batch size 64,
Dirichlet alpha 0.3, SGD learning rate 0.05, momentum 0.9, weight decay
0.0001, server learning rate 1, and 10,000 test examples. All methods reserve
the same three disjoint, class-balanced 200-example roots and use identical
client/root/test partitions. Attacked cells use 20% malicious clients and
30% batch poisoning. The instance namespace, target/location draw and
malicious-client identities are paired by attack and seed. The adaptive
attack is re-optimized against each method's current model: equal attacker
procedure/access, not artificially identical pixel values on different models.

TierGuard 2 keeps the completed candidate's clip multiplier 8, gamma 8,
weight floor 0.05, clean-improvement credit 0.25, two probes per class,
3-by-3 patch family and clean-derived client/edge thresholds
0.35900445729494096 / 0.21499230563640584. No parameter is changed in response
to the adverse seeds. Both levels still compute and save audit scores in
every TG2 ablation, but the disabled level receives zero applied risk.
This isolates risk-weighting effects while retaining clipping, receipts,
diagnostics and recomputation. It is **not an audit-computation speed ablation**.

Median ignores sample masses and uses Torch's lower-median convention,
including the six-edge cloud. FLTrust clips negative cosine trust to zero,
normalizes candidate norms to the reference norm and weights by trust; it
falls back to FedAvg only for an absent/near-zero reference. RFA uses ten
smoothed Weiszfeld iterations with the existing 1e-6 distance floor and
sample-mass weights. These are disclosed two-tier adaptations, not claims
of reproducing the original flat-server experiments. Numerical aggregator
definitions are covered by unit tests and the pinned source.

This initial screen uses **one fixed configuration per variant**, with no
within-screen tuning and no selection of the final strongest baseline.
It does not satisfy the full study's equal-budget hyperparameter-search gate.
FLAME, FedGame-derived, HFLMND and PTA comparisons remain required in later
development, including their source/adaptation and runtime checks.

All variants share the plaintext signed-receipt and half-edge challenge
interface. This phase has trusted edges and no compromised-edge injection.
Challenges use the existing post-commit system-random sampler; the fraction
and information interface are matched, but exact challenged edge IDs are not
paired. The method-independent secret schedule remains a separate requirement
for future compromised-edge comparisons. No client confidentiality, real
network timing, or deployment-grade key-custody guarantee is claimed.

## Freeze and validation

A NEW HPC clone, `project_fashion_mechanism_v1`, is pinned to a tested source
commit. No earlier training clone is pulled or edited. The write-once external
`fashion_mechanism_v1_manifest.json` records every resolved cell hash, source
file hash, package lock, Python version, prior calibration/index hashes and
three paired partition hashes. This is a development freeze only; the main
`protocol_draft.yaml` remains prefreeze and confirmatory seeds stay disabled.

The new guard shares the original exclusive submission lock but keeps a
separate `fashion_mechanism_v1_submission_ledger.jsonl`. It checks the entire
account twice, verifies the preceding scheduler job ended F/exit 0, refuses
any prior attempt or ambiguous intent, and validates the complete prefix of
finished cells before submitting at most ONE next cell. PBS rerunning is
disabled. An error stops continuation; it is never silently skipped.

The index verifies exact configuration/source/environment/partitions,
rounds 1--40, finite populated metrics, zero stability failures, 40 complete
receipt/audit records, the intended applied-risk switches, paired malicious
clients and finite optimized-trigger artifacts. Every run file receives a
SHA-256 in the timestamped index. Missing cells are allowed only when genuinely
unattempted; duplicates, incomplete or unrecorded attempts block submission.
No inference is calculated from partial panels.

## Analysis and stopping rules

Report every final seed value, mean, sample SD, paired differences and adverse
outcome. Separate clean-training accuracy from accuracy under attack. Compare
full versus clipping-only, client-only and cloud-only to locate a mechanism
benefit or redundancy, and compare all four with median/FLTrust/RFA/FedAvg.
Three reused development seeds do not justify confirmatory significance.

For the high-ASR optimized-trigger seeds, inspect client and edge held-out
target gains, applied risks, clipping fractions and target/pattern choices
through time. Treat associations as diagnostic; only matched ablations can
support an attribution to risk weighting. Do not label a score difference as
proved cloud-audit benefit.

Pause on execution/validation failure, missing scheduler history, ambiguous
submission, or a completed 96-cell panel. Inform the user of meaningful
completion, adverse findings or decisions; remain quiet on unchanged running
state. Do not start a new campaign, change hyperparameters, or run confirmation
automatically. A failed scientific performance gate is reported, not optimized
away. DOI work remains outside scope.

## Local implementation verification

The applicable local suite passed **117 tests**, including all eight variants'
synthetic integration/receipt checks, both weighting switches, malformed
configuration/partition/audit detection, incomplete and duplicate attempts,
and ambiguous/mismatched submission ledgers. One legacy v1 environment-lock
test was deselected because this is a v2 development environment; the complete
v2 package/Python lock is independently checked on the HPC before freezing
and again before submission and training. Synthetic tests are implementation
checks, not FashionMNIST effectiveness results.

## Frozen deployment and first job

The new HPC clone is detached at
`731fda036f6cd7b2af3eb62413b3e6b33f557311`. The v2 Python/package check
returned no errors. FashionMNIST dataset hashes were verified before issuing
the write-once manifest; the full lock and dataset hashes are checked again
before submission and before training.

| Artifact | SHA-256 |
| --- | --- |
| `fashion_mechanism_v1_manifest.json` | `b7f73df20b534317e33cf01bdec4eb3790c563251c2e8b3f20d25e3c81ebccd5` |
| `scripts/submit_tierguard2_fashion_mechanism_one_job.py` | `134afa8f7b6a13836ad390a34ac177a20b4d632d6ca3802d0212367f0b4802f0` |
| `scripts/tierguard2_fashion_mechanism_v1.pbs` | `56a4611b71b61ba3fb687a9bdb5b73d6e62cdb940ccc109f261f4c1b87dfd5a9` |

After an empty-account dry-run, the guard submitted **39399.mgmt01** at
2026-09-27T15:56:21 UTC for **median / none / seed 2001**. It was verified
running and the only selected account job. No second job was submitted in
this startup turn. The existing hourly heartbeat was updated to this exact
bounded phase and resumed; it cannot authorize another campaign.

The startup manifest, empty validated index, ledger and submission record
are copied to `Rajanmani/output/TierGuard2_Fashion_Mechanism_Phase_2026-09-27`.
The first cell is not a completed result at startup. Later documentation
commits must not be pulled into the frozen HPC clone.

## Checkpoint: 27 September 2026, 16:58 UTC

The first cell (median / none / 2001, job 39399) completed with exit 0.
The partial-panel index validates 1/96 cells, has no errors and reports
only unattempted cells as missing. It verifies all 40 rounds, complete
audits, zero stability failures, exact frozen source/configuration/environment
and paired partitions. All 51 raw files were copied locally and independently
hash-checked, with CSV/final metric agreement.

Final clean accuracy is 0.8556 and macro-F1 is 0.8565363973966267. ASR is
null because no backdoor is installed. No comparison or inference is made
from this single clean development seed.

The dry-run index at 17:00:00 UTC and submission-time index at 17:02:15 UTC
share SHA-256
`f1dd8018b0b8dc5574cfb59d32cddf5c6c90d0138ccc8e4ca3f460e69c017916`.
After verifying an empty account and the approved manifest/guard hashes,
the guard submitted **39403.mgmt01** once at 17:02:16 UTC for median /
none / seed 2002. It was verified R and the sole account job.

The checkpoint evidence is saved under
`Rajanmani/output/TierGuard2_Mechanism_2026-09-27T165844Z`.
No source changes, retries, additional submissions, tuning or confirmatory
runs were made. The frozen 96-cell order is unchanged.

## Checkpoint: 27 September 2026, 17:59 UTC

The second cell (median / none / 2002, job 39403) completed F/exit 0.
The partial index contains 2/96 cells with no errors: 40 rounds per cell,
complete audits, zero stability failures, frozen source/configuration/
environment and exact paired partitions. All 51 newly completed run files
were copied and independently hash-checked. Accuracy is 0.8615 and macro-F1
is 0.860873189628035; clean ASR is undefined. This partial clean panel
supports no method comparison or confirmatory inference.

The new dry-run/submission indices share SHA-256
`2d43a448e5fd1c624855447089c2977784a1bcc1e4704385e9b049806a501c6a`.
Following hash verification and an empty-account check, the frozen guard
submitted **39404.mgmt01** once at 18:02:41 UTC for median / none / seed
2003. It was verified R and the only account job. Evidence is preserved in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-27T175915Z`.
No training retry, tuning, confirmation, clone edit or other campaign occurred.

## Checkpoint: 27 September 2026, 19:00 UTC

The third clean cell (median / none / 2003, job 39404) completed F/exit 0.
The partial index validates 3/96 cells with no errors. Each has 40 rounds,
complete audits and zero stability failures, with frozen inputs and exact
paired partitions. The local checks verify all 153 files across the three
completed clean cells. Seed 2003 accuracy is 0.8380 and macro-F1 is
0.8354947465848456; clean ASR remains undefined.

Both new indices have SHA-256
`58d9bfedbd451e0e9a20afd9700a71ecc8c234e793080eb84bb1c67d6e302997`.
After successful validation, approved hash checks and an empty account,
the guard submitted **39405.mgmt01** once at 19:03:35 UTC for median /
unknown_patch_model_replacement / seed 2001. It was verified R and the
only account job. Evidence is saved under
`Rajanmani/output/TierGuard2_Mechanism_2026-09-27T190016Z`.
The median clean subset is complete; method comparisons await the full
bounded screen. No tuning, confirmation, retries or clone edits occurred.

## Checkpoint: 27 September 2026, 20:00 UTC

The first median unknown-patch/model-replacement cell (seed 2001, job 39405)
completed F/exit 0. The frozen guard validates 4/96 cells without errors.
Its accuracy is 0.8614, macro-F1 0.8619156723420935 and ASR
0.8787777777777778. The high ASR is retained as an adverse outcome, not used
for tuning or exclusion. Forty rounds, complete audits, zero stability
failures, frozen inputs and exact paired partitions pass validation.
All 51 newly copied files are hash-verified. A supplemental local checker
was corrected to respect the already-frozen five-round evaluation schedule;
the original checker and diagnostic remain preserved. The frozen guard,
training source and evidence were not changed.

Both new indices have SHA-256
`8d956f59c90f7582ac1f10f5156f12bf6559de1c93de5e56f1d9bc6327644bb4`.
After validation and an empty-account check, the guard submitted
**39406.mgmt01** once at 20:04:42 UTC for median /
unknown_patch_model_replacement / seed 2002, verified R and the sole account
job. Evidence is in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-27T200017Z`.
No method superiority, tuning, confirmation or next campaign is inferred.

## Checkpoint: 27 September 2026, 21:01 UTC

Median unknown-patch/model-replacement seed 2002 (39406) completed F/exit 0.
The frozen guard validates 5/96 cells without errors. The new cell's accuracy
is 0.8630, macro-F1 0.8650849318225526 and ASR 0.7077777777777777.
This adverse ASR is retained without tuning or exclusion. All 40 rounds,
complete audits, zero stability failures, frozen inputs and paired partitions
pass validation. The local copy passes all 51 hashes and metric checks,
including the frozen five-round evaluation cadence.

Both new indices have SHA-256
`847ec07dc7139904580ce57b27ef24377fe364760d58acceb7a1b3b760d89079`.
After validation and an empty-account check, the guard submitted
**39407.mgmt01** once at 21:05:07 UTC for median /
unknown_patch_model_replacement / seed 2003, verified R and the sole account
job. Evidence is in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-27T210148Z`.
No comparative inference, tuning, confirmation, retry or clone edit occurred.

## Checkpoint: 27 September 2026, 22:02 UTC

Median unknown-patch/model-replacement seed 2003 (39407) completed F/exit 0.
The frozen guard validates 6/96 cells with no errors. Accuracy is 0.8520,
macro-F1 0.8487135668567335 and ASR 0.3340. The three-seed unknown-patch
subset is complete; every result, including the earlier high ASRs, is retained.
All 40 rounds, complete audits, zero stability failures, frozen inputs and
paired partitions pass validation. The local copy passes all 51 file hashes,
metric agreement and the frozen five-round evaluation-cadence checks.

Both new indices have SHA-256
`459d4c2df1c49e0f3e9cdea280736475d710f232bd3e58e09facc6db28f97418`.
After validation and an empty-account check, the guard submitted
**39408.mgmt01** once at 22:06:24 UTC for median / distributed_backdoor /
seed 2001, verified R and the only account job. Evidence is in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-27T220249Z`.
This follows the fixed order within the existing screen, not a new campaign.
No comparative inference, tuning, confirmation, retry or clone edit was made.

## Checkpoint: 27 September 2026, 23:04 UTC

Median distributed-backdoor seed 2001 (39408) completed F/exit 0,
walltime 00:13:07. The frozen guard validates 7/96 cells with no errors.
The new cell's accuracy is 0.8530, macro-F1 0.8535090057786812 and ASR
0.012222222222222223. These are one seed's descriptive development values;
no method comparison is available yet. Prior adverse unknown-patch results
remain unchanged. All 40 rounds, complete audits, zero stability failures,
frozen inputs and paired partitions pass validation. The local copy passes
all 51 file hashes, metric agreement and the frozen evaluation-cadence checks.

Both new indices have SHA-256
`00bb0be148158cc1ec13eed6fdc0b2e74f22233c3357f3c815d5eeacc35419f4`.
After validation and an empty-account check, the guard submitted
**39409.mgmt01** once at 23:08:37 UTC for median / distributed_backdoor /
seed 2002, verified R and the only account job. Evidence is in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-27T230420Z`.
No comparative inference, tuning, confirmation, retry or clone edit was made.

## Checkpoint: 28 September 2026, 00:06 UTC

Median distributed-backdoor seed 2002 (39409) completed F/exit 0,
walltime 00:13:14. The frozen guard validates 8/96 cells with no errors.
The new cell's accuracy is 0.8631, macro-F1 0.8611206785526117 and ASR
0.005. These are descriptive development values; no method comparison is
available yet. All prior outcomes, including adverse unknown-patch ASRs,
remain unchanged. All 40 rounds, complete audits, zero stability failures,
frozen inputs and paired partitions pass validation. The local copy passes
all 51 file hashes, metric agreement and the frozen evaluation-cadence checks.

Both new indices have SHA-256
`fe491e4aa1d129d802e67e173beae025cc290b65aa9947221a72bdafd3314d29`.
After validation and an empty-account check, the guard submitted
**39410.mgmt01** once at 00:10:00 UTC for median / distributed_backdoor /
seed 2003, verified R and the only account job. Evidence is in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T000621Z`.
No comparative inference, tuning, confirmation, retry or clone edit was made.

## Checkpoint: 28 September 2026, 01:07 UTC

Median distributed-backdoor seed 2003 (39410) completed F/exit 0,
walltime 00:11:57. The frozen guard validates 9/96 mechanism-screen cells
with no errors. The new cell's accuracy is 0.8550, macro-F1
0.852810812595094 and ASR 0.004111111111111111. The three-seed median
distributed-backdoor subset is complete, but no method comparison is made
from this partial screen. All prior outcomes, including adverse unknown-patch
ASRs, remain unchanged. All 40 rounds, complete audits, zero stability
failures, frozen inputs and paired partitions pass validation. The local copy
passes all 51 file hashes, metric agreement and evaluation-cadence checks.

Both new indices have SHA-256
`8832df1199dc093525ae17f435a557933d55bcdeea8a98b41d72bd240e8700d4`.
After validation and an empty-account check, the guard submitted
**39411.mgmt01** once at 01:11:36 UTC for median /
defence_aware_optimized_trigger / seed 2001, verified R and the only account
job. Evidence is in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T010751Z`.
No comparative inference, tuning, confirmation, retry or clone edit was made.

## Checkpoint: 28 September 2026, 02:41 UTC heartbeat

Median optimized-trigger seed 2001 (39411) completed F/exit 0,
walltime 00:13:51. The frozen guard validates 10/96 cells with no errors.
The new cell's accuracy is 0.8502, macro-F1 0.8492562304825864 and residual
ASR 0.24033333333333334. The adverse baseline outcome is retained unchanged;
one development seed does not establish comparative efficacy. All prior
outcomes remain preserved. All 40 rounds, complete audits, finite optimized
artifacts, zero stability failures, frozen inputs and paired partitions pass
validation. The local copy passes all 91 hashes, metric agreement and
frozen evaluation-cadence checks.

Both new indices have SHA-256
`ff60b3d309b0db57490e10c7d7c7717f57bc162705a86ee7b75411fc44b89eff`.
After the intervening status query, refreshed empty-account, ledger and
approved hash checks and successful validation, the guard submitted
**39413.mgmt01** once at 03:28:32 UTC for median /
defence_aware_optimized_trigger / seed 2002, verified R and the only account
job. Evidence is in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T024137Z`.
No comparative inference, tuning, confirmation, retry or clone edit was made.

## Checkpoint: 28 September 2026, 03:41 UTC heartbeat

Median optimized-trigger seed 2002 (39413) completed F/exit 0,
walltime 00:13:00. The frozen guard validates 11/96 cells with no errors.
Accuracy is 0.8654, macro-F1 0.8650128130882108 and residual ASR
0.13011111111111112. This result and seed 2001's 24.03% ASR are retained
without tuning or exclusion. The partial development panel supports no
comparative inference. All 40 rounds, complete audits, finite optimized
artifacts, zero stability failures, frozen inputs and paired partitions pass
validation. The local copy passes all 91 hashes, metric agreement and
frozen evaluation-cadence checks.

Both new indices have SHA-256
`d6c30ecadbd0053a7ddfb83aa3d7ab71205d16f034156e0826583a8d76b6b7a5`.
After successful validation and an empty-account check, the guard submitted
**39416.mgmt01** once at 03:45:07 UTC for median /
defence_aware_optimized_trigger / seed 2003, verified R and the only account
job. Evidence is in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T034156Z`.
No comparative inference, tuning, confirmation, retry or clone edit was made.

## Checkpoint: 28 September 2026, 04:42 UTC heartbeat

Median optimized-trigger seed 2003 (39416) completed F/exit 0,
walltime 00:12:08. The frozen guard validates 12/96 cells with no errors.
The entire median subset is complete; the index lists 84 unattempted cells
before the next submission in the same authorized screen. The latest cell's
accuracy is 0.8520, macro-F1
0.8497660839220946 and residual ASR 0.24122222222222223. All outcomes,
including prior adverse ASRs, are retained without tuning, exclusion or
replacement. These descriptive development values do not establish a
method comparison. All 40 rounds, complete audits, finite optimized artifacts,
zero stability failures, frozen inputs and paired partitions pass validation.
The new local copy passes all 91 hashes, metric agreement and evaluation cadence.

Both new indices have SHA-256
`e2eba78b54be19a9dd1e1e08e89451dd8d7e3b19344c3130b32cf66e4f4a6b06`.
After successful validation, approved hash checks and refreshed empty-account
and unchanged-ledger checks, the guard submitted **39420.mgmt01** once at
04:49:56 UTC for fltrust / none / seed 2001, verified R and the sole account
job. Evidence is in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T044257Z`.
This is the next frozen cell in the existing screen, not another campaign.
No comparative inference, tuning, confirmation, retry or clone edit was made.

## Checkpoint: 28 September 2026, 05:42 UTC heartbeat

FLTrust clean seed 2001 (39420) completed F/exit 0, walltime 00:07:37.
The frozen guard validates 13/96 cells without errors; the new cell follows
the completed 12-cell median subset. The index lists 83 genuinely unattempted
cells before the next submission. Accuracy is 0.8121 and macro-F1 is
0.8077987660174857. Clean ASR is null in final JSON/index and blank throughout
the CSV, not zero. This one clean development seed supports no comparative
inference. Prior outcomes are retained without tuning or exclusion.

All 40 rounds, complete audits, zero stability failures, frozen inputs and
paired partitions pass validation. The local copy passes all 51 hashes,
exact file membership, metric agreement and frozen evaluation cadence.
Both new indices have SHA-256
`d1026d0f7e037e9fe35a92f5e08dc3fb371dbb7c435bb6b18c612ceaefff5623`.

After validation and refreshed empty-account, unchanged-ledger and approved
hash checks, the guard submitted **39430.mgmt01** once at 05:48:21 UTC for
fltrust / none / seed 2002, verified R and the sole account job. Evidence is in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T054258Z`.
No retry, replacement, tuning, confirmation, clone edit or other submission
was made. This remains the same bounded screen, not another campaign.

## Checkpoint: 28 September 2026, 06:44 UTC heartbeat

FLTrust clean seed 2002 (39430) completed F/exit 0, walltime 00:07:44.
The frozen guard validates 14/96 cells without errors: all median cells
and the first two FLTrust clean seeds. The index lists 82 genuinely unattempted
cells before the next submission. Accuracy is 0.8031 and macro-F1 is
0.7862631414726295. Clean ASR is null in final JSON/index and blank throughout
the CSV. Seed 2001 retains accuracy 0.8121 and macro-F1 0.8077987660174857.
These descriptive development values support no method comparison; no tuning,
exclusion or replacement is made.

All 40 rounds, complete audits, zero stability failures, frozen inputs and
paired partitions pass validation. The local copy passes all 51 hashes,
exact file membership, metric agreement and frozen evaluation cadence.
Both new indices have SHA-256
`723f9e6ee1cdfe69b7c7936263f1a712b9a99dea0a5a70fd5d39faafffcf7747`.

After validation and refreshed empty-account, unchanged-ledger and approved
hash checks, the guard submitted **39441.mgmt01** once at 06:48:21 UTC for
fltrust / none / seed 2003, verified R and the sole account job. Evidence is in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T064400Z`.
No retry, replacement, tuning, confirmation, clone edit or other submission
was made. This remains the same bounded screen, not another campaign.

## Checkpoint: 28 September 2026, 07:44 UTC heartbeat

FLTrust clean seed 2003 (39441) completed F/exit 0, walltime 00:07:53.
The frozen guard validates 15/96 cells without errors: all median cells
and all three FLTrust clean seeds. The index lists 81 genuinely unattempted
cells before the next submission. Accuracy is 0.7966 and macro-F1 is
0.7886567798662272. Clean ASR is null in final JSON/index and blank throughout
the CSV. Seeds 2001 and 2002 retain accuracy 0.8121 and 0.8031 and macro-F1
0.8077987660174857 and 0.7862631414726295, respectively. These descriptive
development values support no method comparison; no tuning, exclusion or
replacement is made.

All 40 rounds, complete audits, zero stability failures, frozen inputs and
paired partitions pass validation. The local copy passes all 51 hashes,
exact file membership, metric agreement and frozen evaluation cadence.
Both new indices have SHA-256
`2fb912775e7d815017745028e731706f255aaa65700087a053af711fa2826d65`.

After validation and refreshed empty-account, unchanged-ledger and approved
hash checks, the guard submitted **39478.mgmt01** once at 07:50:39 UTC for
fltrust / unknown_patch_model_replacement / seed 2001, verified R and the
sole account job. Evidence is in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T074431Z`.
The clean subset's completion does not end the authorized 96-cell phase.
No retry, replacement, tuning, confirmation, clone edit or other submission
was made. This remains the same bounded screen, not another campaign.

## Checkpoint: 28 September 2026, 08:45 UTC heartbeat

FLTrust unknown-patch/model-replacement seed 2001 (39478) completed F/exit 0,
walltime 00:09:27. The frozen guard validates 16/96 cells with no errors:
all median cells, all three FLTrust clean seeds and its first attack seed.
The index lists 80 genuinely unattempted cells before the next submission.
The newest cell has clean-test accuracy under attack 0.8107, macro-F1
0.8063727955403557 and ASR 0.7796666666666666. Its high 77.97% ASR is
retained without tuning, exclusion or replacement. One development seed
does not establish a method comparison; prior outcomes remain unchanged.
Clean-cell ASR remains undefined.

All 40 rounds, complete audits, zero stability failures, frozen inputs and
paired partitions/attack instances pass validation. The local copy passes
all 51 hashes, exact file membership, metric and ASR-alias agreement and
frozen evaluation cadence. Both new indices have SHA-256
`633f421faf76df06288cf6c707fac29ce44fa48e3c8649130ca17274ba0cddf3`.

After validation and refreshed empty-account, unchanged-ledger and approved
hash checks, the guard submitted **39497.mgmt01** once at 08:49:48 UTC for
fltrust / unknown_patch_model_replacement / seed 2002, verified R and the
sole account job. Evidence is in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T084532Z`.
No retry, replacement, tuning, confirmation, clone edit or other submission
was made. This remains the same bounded screen, not another campaign.

## Checkpoint: 28 September 2026, 13:23 UTC heartbeat

FLTrust unknown-patch/model-replacement seed 2002 (39497) completed F/exit 0,
walltime 00:03:01. The frozen guard validates 17/96 cells with no errors:
all median cells, all three FLTrust clean seeds and unknown-patch seeds 2001/2002.
The index lists 79 genuinely unattempted cells before the next submission.
The newest cell has clean-test accuracy under attack 0.8091, macro-F1
0.7960852645745459 and residual ASR 0.26. Seed 2001's adverse ASR
0.7796666666666666 remains intact. Both results are retained without tuning,
exclusion or replacement. They are different development seeds, not
before/after evidence of a repair; no comparative inference is made.
Clean-cell ASR remains undefined.

All 40 rounds, complete audits, zero stability failures, frozen inputs and
paired partitions/attack instances pass validation. The local copy passes
all 51 hashes, exact file membership, metric and ASR-alias agreement and
frozen evaluation cadence. Both new indices have SHA-256
`b9761349cda1737e4c8bad477797939dd894dccb7920e7bad75c8a6328b5d218`.
The shorter scheduler walltime is provenance, not a normalized speed comparison.

After validation and refreshed empty-account, unchanged-ledger and approved
hash checks, the guard submitted **39522.mgmt01** once at 13:28:14 UTC for
fltrust / unknown_patch_model_replacement / seed 2003, verified R and the
sole account job. Evidence is in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T132302Z`.
No retry, replacement, tuning, confirmation, clone edit or other submission
was made. This remains the same bounded screen, not another campaign.

## Checkpoint: 28 September 2026, 14:23 UTC heartbeat

FLTrust unknown-patch/model-replacement seed 2003 (39522) completed F/exit 0,
walltime 00:14:49. The frozen guard validates 18/96 cells with no errors:
all median cells, all three FLTrust clean seeds and all three unknown-patch seeds.
The index lists 78 genuinely unattempted cells before the next submission.
The newest cell has clean-test accuracy under attack 0.7943, macro-F1
0.7869355118352528 and residual ASR 0.049777777777777775.
Seed 2001's adverse ASR 0.7796666666666666 and seed 2002's ASR 0.26 remain
intact. All three results are retained without tuning, exclusion or rerun.
These are different development seeds, not before/after evidence of a repair;
no comparative inference is made. Clean-cell ASR remains undefined.

All 40 rounds, complete audits, zero stability failures, frozen inputs and
paired partitions/attack instances pass validation. The local copy passes
all 51 hashes, exact file membership, metric and ASR-alias agreement and
frozen evaluation cadence. Both new indices have SHA-256
`4ba8dc20f94fde59ae2b34e473241e65e20179f8917fe10942e39450a9cf3bb3`.
Recorded-metric agreement does not independently recompute predictions.

After validation and refreshed empty-account, unchanged-ledger and approved
hash checks, the guard submitted **39536.mgmt01** once at 14:30:13 UTC for
fltrust / distributed_backdoor / seed 2001, verified R, non-rerunnable and
the sole account job. The unchanged ledger prefix gained exactly one
intent/submitted pair, reaching 38 rows. Evidence is in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T142334Z`.
Completion of the FLTrust unknown-patch subset does not end the 96-cell phase.
No retry, replacement, tuning, confirmation, clone edit or other submission
was made. This remains the same bounded screen, not another campaign.

## Checkpoint: 28 September 2026, 15:24 UTC heartbeat

FLTrust distributed-backdoor seed 2001 (39536) completed F/exit 0,
walltime 00:14:17. The frozen guard validates 19/96 cells with no errors:
all median cells, all FLTrust clean/unknown-patch seeds and its first
distributed-backdoor seed. The index lists 77 genuinely unattempted cells
before the next submission. The newest cell has clean-test accuracy under
attack 0.8072, macro-F1 0.8008264683142536 and residual ASR 0.025.
This is one development seed, not a comparative efficacy result. All prior
outcomes, including adverse unknown-patch seeds, are retained without tuning,
exclusion or rerun. Clean-cell ASR remains undefined.

All 40 rounds, complete audits, zero stability failures, frozen inputs and
paired partitions/attack instances pass validation. The local copy passes
all 51 hashes, exact file membership, metric and ASR-alias agreement and
frozen evaluation cadence. Its first-18 complete run records, including
hashes, exactly match the previous timestamped index.
Both new indices have SHA-256
`203041e54e4bd386442893a5802ff65b79f6360c1cd9e4e2081d976f408e6a14`.
Recorded-metric agreement does not independently recompute predictions.

After validation and refreshed empty-account, unchanged-ledger and approved
hash checks, the guard submitted **39538.mgmt01** once at 15:30:25 UTC for
fltrust / distributed_backdoor / seed 2002, verified R, non-rerunnable and
the sole account job. The previous ledger prefix gained exactly one
intent/submitted pair, reaching 40 rows. Evidence is in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-28T152404Z`.
No retry, replacement, tuning, confirmation, clone edit or other submission
was made. This remains the same bounded screen, not another campaign.
