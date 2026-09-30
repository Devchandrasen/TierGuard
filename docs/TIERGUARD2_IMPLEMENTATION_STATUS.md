# TierGuard 2 research branch — implementation status

This branch is a new, unfinished study. It does **not** change the published
`protocol-v1-freeze` Git tag or convert the earlier six-seed results into
evidence for a new method. No confirmatory outcome or superiority claim exists.

As of 27 September 2026, the 25 queued development jobs were cancelled at
the administrator's request. After the queue emptied, the user approved
strictly one-at-a-time continuation. All resumed jobs through 39388.mgmt01
completed with exit 0 and passed validation, bringing FashionMNIST attack
development to 9/9. The final index is complete with zero errors. The account
queue was empty and the hourly follow-up was paused at that panel's completion.
Optimized-trigger seeds 2002 and 2003 retain 52.98% and 54.37% ASR, respectively.
The [complete panel review](TIERGUARD2_FASHIONMNIST_PANEL_REVIEW_2026-09-27.md)
reports every seed and distinguishes validated execution from defence efficacy.
These are development results only, not robust-baseline superiority or
confirmation. Review this completed panel before any further campaign.
Following that review, the user approved the
[bounded mechanism screen](TIERGUARD2_FASHION_MECHANISM_PHASE_2026-09-27.md):
three basic robust baselines, three TG2 weighting ablations, full TG2 and
FedAvg, each under clean training and three attacks with three development
seeds. Its 96 cells use a new source snapshot and never permit more than one
outstanding account job. Later source-audited baselines and confirmation
remain outside this screen. The original panel is not overwritten or pooled.
At 07:08 UTC on 30 September, the validated prefix remained
**40/96** with zero guard errors. After full-account empty,
ledger and pinned-hash checks, the guard submitted exactly one
next job: **39749.mgmt01**, `clip_only /
unknown_patch_model_replacement / seed 2002`. PBS showed it R
and the sole account job. The 82-row ledger retains the previous
80 rows unchanged and adds a matching intent/submitted pair.
This is an attempt, not yet a validated result. Evidence is in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-30T070500Z`.
Job 39749 subsequently finished F/exit 0. Frozen guard and
independent raw-record checks validate **41/96** completed
cells, zero errors, 40 rounds/audits, zero stability failures
and unchanged prior 40-run prefix. This clip-only unknown-patch
seed has accuracy 0.8847, macro-F1 0.8843148565654431 and
adverse ASR 0.9995555555555555. It is an ablation development
result, not a result for full TierGuard 2. No second job was
submitted.
At 06:09 UTC on 30 September, the validated prefix remained **39/96**
with zero guard errors. Following refreshed empty-account, external
ledger and pinned-hash checks, the guard submitted exactly one next
job: **39730.mgmt01**, `clip_only / unknown_patch_model_replacement /
seed 2001`. PBS showed it R and the sole account job. The 80-row
ledger retains the previous 78 rows unchanged and adds one matching
intent/submitted pair. This is an attempt, not a validated result.
The prior clean seed and full 39-run index remain validated. See
`Rajanmani/output/TierGuard2_Mechanism_2026-09-30T060322Z`.
Job 39730 subsequently finished F/exit 0. The frozen guard and
independent raw-record checker validate **40/96** completed cells,
zero errors, 40 rounds and audits, zero stability failures, and
the unchanged 39-run prefix. This clip-only unknown-patch seed
records accuracy 0.8822, macro-F1 0.8820349349730623 and
adverse ASR 0.9995555555555555. This single development seed
does not support comparative inference. No second job was submitted.
At 05:03 UTC on 30 September, **39/96** cells completed and passed the
frozen guard, including all three clip-only clean seeds. Seed 2003
(39719) has accuracy 0.8792, macro-F1 0.8784398708213675 and
undefined clean ASR. A first independent checker failed on a rounded
macro-F1 literal; the raw record and index agree at full precision, and
the corrected checker passes all 51 file hashes, 40 rounds and audits.
No training discrepancy was found. In accordance with the stop-on-error
rule, **no next job was submitted** in this heartbeat; the account ended
empty and all 78 ledger rows were unchanged. The next attack cell remains
unattempted pending fresh validation. No comparative claim is made.
At 04:06 UTC on 30 September, **38/96** cells had completed and passed
the frozen guard and independent raw-record checks. The second clip-only
clean seed (39710) has accuracy 0.8840 and macro-F1
0.8828316721127758; clean ASR is undefined. Following full-account
empty and ledger checks, the guard submitted exactly one next job,
**39719.mgmt01** for `clip_only / none / seed 2003`. PBS showed it
running as the sole account job; it is not yet a result. The phase
checkpoint records its 78-row ledger and timestamped evidence. No
comparative or confirmatory claim is made.
At 03:05 UTC on 30 September, **37/96** cells had completed and passed
the frozen guard and independent raw-record checks. The first clip-only
clean seed (39709) has accuracy 0.8847 and macro-F1 0.8843347297719957;
clean ASR is undefined. After full-account empty and ledger checks, the
guard submitted exactly one next job, **39710.mgmt01** for
`clip_only / none / seed 2002`. PBS showed it running as the sole
account job; it is not yet a result. The separate mechanism checkpoint
records its 76-row ledger and timestamped evidence. No comparative or
confirmatory claim is made.
At the 30 September 02:57 UTC checkpoint, the validated prefix remains
**36/96**; the recovered dry-run, prior and submission-time indices are
byte-identical and the independent raw-record checker passes. The account
was empty before the pinned guard submitted exactly one next cell:
**39709.mgmt01**, `clip_only / none / seed 2001`. PBS showed it running as
the sole account job; the 74-row ledger has one new matching intent/submitted
pair. This clean cell is not yet a validated result, and its ASR is undefined.
No other job, tuning or confirmation was started. See the mechanism phase
checkpoint and its separate evidence folder for scheduler and hash details.
At the 09:04 UTC heartbeat checkpoint on 29 September, 36/96 cells had completed
F/exit 0 and passed the frozen guard with no errors: all 12 median cells,
all 12 FLTrust cells, all three RFA clean seeds, all three RFA unknown-patch seeds
and all three RFA distributed-backdoor and optimized-trigger seeds.
All three 12-cell baseline subsets are complete, not the 96-cell screen;
the index lists 60 genuinely unattempted cells before any next submission.
Each completed cell has 40 rounds, complete audits and zero stability failures.
The newest cell (39607, rfa / defence_aware_optimized_trigger / seed 2003)
has clean-test accuracy under attack 87.92% (0.8792), macro-F1
0.8767053758248743 and adverse ASR 71.44% (0.7144444444444444).
Recorded ASR is 0.10288888888888889 at round 5, 0.5587777777777778 at round 10,
0.6491111111111111 at round 35 and 0.7144444444444444 at round 40.
Final/index/CSV metrics and both aliases agree; all eight evaluation points
and 40 finite optimized-trigger artifacts are saved without tuning or rerun.
Optimized-trigger seed 2002 (39595) retains
clean-test accuracy under attack 88.54% (0.8854), macro-F1
0.883715817471517 and adverse ASR 70.54% (0.7054444444444444).
Recorded ASR is 0.024666666666666667 at round 5, 0.101 at round 10,
0.49655555555555553 at round 35 and 0.7054444444444444 at round 40.
Final/index/CSV metrics and both aliases agree; all eight evaluation points
and 40 finite optimized-trigger artifacts are saved. This adverse result is
retained without tuning, exclusion or rerun. Different seeds are not repair evidence.
Optimized-trigger seed 2001 (39583)
has clean-test accuracy under attack 87.68% (0.8768), macro-F1
0.8777828838556347 and adverse ASR 99.48% (0.9947777777777778).
Recorded ASR is 0.4777777777777778 at round 5,
0.9502222222222222 at round 10, 0.9867777777777778 at round 35 and
0.9947777777777778 at round 40. Final/index/CSV metrics and both aliases agree;
all eight evaluation points and 40 finite optimized-trigger artifacts are saved.
This adverse development seed is retained without tuning, exclusion or rerun.
The preceding distributed-backdoor cell (39566, rfa / distributed_backdoor / seed 2003)
has clean-test accuracy under attack 87.56% (0.8756), macro-F1
0.8748556960047212 and adverse ASR 100% (1.0).
Recorded ASR is 0.0035555555555555557 at round 5 and 1.0 at rounds 35/40;
final/index/CSV metrics and both aliases agree. Its preserved exact-frozen-source
boundary review confirms true-target exclusion, all remaining classes,
target label 5 and an empty-loader ASR of zero, not one.
Distributed-backdoor seed 2002 retains accuracy 88.79% (0.8879), macro-F1
0.886147613311708 and adverse ASR 99.18% (0.9917777777777778).
Its recorded ASR is 0.011333333333333334 at round 5, 0.9 at round 35 and
0.9917777777777778 at round 40; final/index/CSV metrics and both aliases agree.
Distributed-backdoor seed 2001 retains accuracy 87.95% (0.8795), macro-F1
0.8799075719382156 and adverse ASR 100% (1.0).
Its earlier boundary review confirms ASR 4% at round 5,
99.9333% at round 35 and 100% at round 40. Frozen-source inspection confirms
true-target exclusion and all other classes; an empty loader returns zero.
The saved test partition has 10,000 unique indices. Predictions and the exact
backdoor numerator/denominator were not independently recomputed.
RFA unknown-patch seed 2003 retains accuracy 88.10% (0.881), macro-F1
0.8802445937287672 and adverse ASR 94.87% (0.9486666666666667).
Unknown-patch seed 2002 retains accuracy 88.88% (0.8888), macro-F1
0.8872450787792507 and adverse ASR 99.92% (0.9992222222222222).
Unknown-patch seed 2001 retains accuracy 87.82% (0.8782), macro-F1
0.8784813701102749 and adverse ASR 99.86% (0.9985555555555555).
All RFA baseline outcomes are retained without tuning, exclusion or rerun;
they are not evidence of TierGuard 2 superiority.
RFA clean seed 2003 retains accuracy 87.98% (0.8798) and macro-F1
0.8784533402701046. Clean seeds 2001/2002 retain
88.50%/88.43% (0.885/0.8843) and macro-F1
0.8842036720600657/0.8823849961603034. Clean-cell ASR is null in final
JSON/index and blank in both CSV ASR columns, not zero. These individual clean
development values support no method comparison and are not compared with
accuracy under attack.
FLTrust optimized-trigger seed 2003 retains clean-test accuracy under attack
79.51%, macro-F1 0.7876075739817777 and residual ASR
6.56% (0.06555555555555556). Seed 2002 retains 80.87%
accuracy, macro-F1 0.7963585252238866 and ASR
2.16% (0.021555555555555557). Seed 2001 retains 81.08%
accuracy, macro-F1 0.805647132854906 and adverse ASR
31.89% (0.3188888888888889), unchanged.
Distributed-backdoor seed 2003 retains 79.33% accuracy, macro-F1
0.7851625604766831 and ASR 0.69% (0.006888888888888889). Seed 2002 retains
80.66% accuracy, macro-F1 0.7924789504946977 and ASR
0.43% (0.004333333333333333). Seed 2001 retains
80.72% accuracy, macro-F1 0.8008264683142536 and ASR 2.50% (0.025).
These are individual development seeds, not a method comparison.
FLTrust unknown-patch seed 2003 retains accuracy 79.43%,
macro-F1 0.7869355118352528 and ASR 4.98% (0.049777777777777775).
Unknown-patch seed 2002 retains accuracy 80.91%, macro-F1 0.7960852645745459
and ASR 26.00% (0.26). Unknown-patch seed 2001 retains accuracy 81.07%,
macro-F1 0.8063727955403557 and adverse ASR 77.97% (0.7796666666666666).
All outcomes are retained without tuning, exclusion or rerun; different
development seeds and attack conditions are not before/after evidence of a repair.
FLTrust clean seeds 2001--2003 retain accuracies 81.21%, 80.31% and 79.66%
and macro-F1 0.8077987660174857, 0.7862631414726295 and
0.7886567798662272, respectively. Clean-cell ASR is undefined, not zero.
The median optimized-trigger seeds retain ASRs of 24.03%, 13.01% and
24.12%; the distributed seeds retain 1.22%, 0.50% and 0.41%, respectively.
Unknown-patch ASRs of 87.88%, 70.78% and 33.40% remain unchanged.
All outcomes are retained without tuning or exclusion. These descriptive
development values do not establish a method comparison.
At the previous checkpoint, **39607.mgmt01** was submitted once at
08:07:51 UTC for rfa / defence_aware_optimized_trigger / seed 2003
and verified as the sole running job; it is now complete and validated.
This checkpoint's original external copy-check script failed to parse because
a diagnostic output key lacked one closing quote. Its original bytes/error
are preserved. Corrected read-only checker verify_copy_v2.py passes all data
assertions; no training source, record or pinned guard failed or was edited.
No --submit invocation was made after that local error in this heartbeat.
The end-of-turn account query is empty and the ledger unchanged.
The next unattempted cell is clip_only / none / seed 2001; a later heartbeat
must check fresh account state, ledger, pins and guard validation first.
This is within the same 96-cell screen, not a new campaign. Completion of
the median/FLTrust/RFA subsets does not end that screen.
At an earlier 16:25 checkpoint, a queue query encountered an SSH
banner-exchange error. No guard
was invoked while status was uncertain; a fresh read-only query succeeded
with exit 0 and proved the account empty before validation/submission.
The failed query and successful checks are both preserved in that earlier
checkpoint. This checkpoint's queue, ledger and hash checks succeeded.
All completed run files were copied and hash-verified locally; the newest
RFA optimized-trigger run contains 91 files, including 40 audit records and
40 finite trigger artifacts. Earlier optimized-
trigger records remain intact. Local verification respects the frozen
five-round evaluation cadence, both attack-ASR aliases and undefined clean ASR;
both guard and local checks passed. Previous evidence and training clones
remain unchanged. The complete first-35 run records, including their file
hashes, exactly match the previous timestamped index.
The earlier 04:03 boundary review resolved local source-path and optional-null
metadata inspection diagnostics through actual file inventory, frozen-source
inspection and direct non-null counts; no training/guard/index check failed.
At the earlier 29 September, 01:31 checkpoint, the full-index command display
exceeded the output limit; bounded JSON projection and independent file checks
passed. That local display diagnostic is preserved; no training/guard failure
or retry occurred. Current projection and file checks pass without discrepancy.
At the earlier 28 September, 22:27 checkpoint, a local JSON-key-order comparison gave a false
ledger mismatch. Sorted-key and independent Python dictionary checks confirm
identical fields and exactly one new submission pair; the diagnostic is saved.
That diagnostic is retained in its original checkpoint. Current fieldwise checks
pass without discrepancy; no scheduler/training attempt failed or was retried.
Current end-state checks confirm 72 ledger rows, all unchanged from the
preceding checkpoint; no new intent/submitted pair was added this heartbeat.
Evidence and the resolved checker diagnostic are preserved in
`Rajanmani/output/TierGuard2_Mechanism_2026-09-29T090417Z`.
The hourly follow-up now targets only this 96-cell
phase; it was resumed after freezing the protocol and checking the account.
The [serial execution policy](TIERGUARD2_SERIAL_EXECUTION.md) governs subsequent
submissions; no batch or array is allowed. Previously completed evidence is audited in
[the September 27 evidence review](TIERGUARD2_EVIDENCE_REVIEW_2026-09-27.md).
That archived snapshot remains unchanged and contains no result from job 39247.

## Implemented and smoke-tested

- Disjoint, class-balanced reference, probe-search, and probe-evaluation roots;
  explicit original client/root/test indices saved per TierGuard 2 run.
- Candidate-update counterfactual search over bounded high, low, checkerboard,
  and four-corner distributed patterns, across three-by-three patch positions
  and all target classes. The winning search probe is evaluated on the held-out
  root against the unchanged model; clean-loss improvement reduces risk. The
  audit API has no attack name, trigger, location, or target-label input.
- Norm clipping and continuous risk weights at both the edge and cloud; no
  trimming/geometric-median switching branch in TierGuard 2. The cloud audits
  each received edge aggregate independently and logs edge-minus-client risk.
- Ed25519-signed direct client receipts covering round, model hash, edge,
  training sample mass, and raw-update hash. After edge reports are committed,
  half of active edges are sampled without replacement for raw-update
  verification and independent aggregate recomputation. Client signatures and
  receipt-list equality are checked for all edges. Under one forged aggregate
  and six active edges, the one-round non-challenge probability is exactly
  3/6 = 0.5; this is not a multi-round security guarantee.
  Missing active-edge reports are recorded and excluded before aggregation,
  with separate expected/received counts. The round and report commitment
  are checked for **every** received edge, including unchallenged edges;
  forged receipts and challenged aggregate inconsistencies are also rejected.
  For matched future edge experiments, a private 32-byte cloud key can define
  a method-independent HMAC ranking by dataset, seed and round, with only its
  hash recorded in provenance. The key is used after report commitment and
  is never supplied to the attack constructor. A write-once key-creation
  utility exists; no final-study key or freeze has been issued yet. Because
  this is one-process simulation, client private-key custody is modelled, not
  independently deployed on client devices. Client training receives a
  reduced configuration without the cloud key path, and the simulated
  compromised-edge transformation has no key/path parameter. This narrows
  the simulation's information interface but is not process isolation or a
  deployment-grade secrecy proof.
- The same optional receipt/challenge wrapper is available to existing
  hierarchical FedAvg, FLTrust, coordinate median, RFA, PTA, and two-tier
  FLAME/FedGame defender adaptations and a paper-derived HFLMND reconstruction.
  PTA retains its predefined bottom-right trigger and target label 0; it is
  not given the new attack instance's hidden target class.
  FLAME follows the published cosine/HDBSCAN majority
  filter, median-norm clipping, equal averaging, and adaptive noise structure;
  its two-tier application and small-edge fallback require explicit reporting.
  The FedGame-derived baseline follows the authors' defender-side sequence,
  but its bounded reconstruction, root size and two-tier use differ materially
  from their flat-server code. The source audit and exact differences are in
  `docs/BASELINE_SOURCE_AUDIT.md`; neither adaptation is author-code-identical.
  Payload byte counts are recorded; these are **not** real network timings.
- The supplied full HFLMND article has now been inspected. Its NSFE feature
  equations, binary hierarchical clustering, historical suspicion correction,
  and equal-average aggregation are implemented at both layers. The paper
  omits the linkage, benign-cluster labelling and all-rejected conventions;
  these are fixed in `docs/HFLMND_PAPER_DERIVATION.md`. This is not a claim of
  matching unpublished author code or its reported outcomes. The one-round
  synthetic HFLMND/challenge smoke test completed without false rejection.
- Attack-side unknown-location patch/model-replacement, four-corner
  component-distributed trigger, and attacker-local gradient-optimized patch
  constructors. Each malicious client is assigned one deterministic corner
  component; the held-out ASR test uses all four components. The complete
  malicious-client/component assignment is written per run.
  The optimized patch penalizes similarity to the defender's fixed probe
  templates and is shared by selected malicious clients within a round. Its
  actual values are saved per round. One-seed FashionMNIST pilots indicate
  effective attacks against FedAvg. The completed validity campaign passed
  on FashionMNIST and MNIST but failed on CIFAR-10; pilots are not inferential
  evidence and no validity campaign is currently running.
- Main-attack target class and patch location can now be drawn from a
  deterministic SHA-256 keyed instance, independent of method, for paired
  dataset/attack/seed comparisons. The location is chosen from the
  prespecified nine-position bounded search family; it is hidden from the
  auditor but this is **not** arbitrary-location generalisation. The resolved
  attack configuration and digest are saved in each run.
- A calibration utility requiring three distinct clean development seeds and
  complete per-round audit logs. It now produces separate client- and
  edge-level thresholds because their clean score distributions differ.
  The FashionMNIST and MNIST nine-run clean development indices passed and are
  recorded in `docs/TIERGUARD2_CLEAN_CALIBRATION_2026-09-24.md`; CIFAR-10
  clean indexing and candidate calibration are now complete at the original
  development training settings, as recorded in the September 27 evidence
  review. A primary decision-rule implementation checks
  all 12-by-9 ASR and 12-by-3 clean cells, the exact paired sign-flip test,
  and the clean-accuracy lower confidence bound.
- Deterministic targeted root-contamination wrapper with the contaminated
  original indices recorded. Its paired test verifies that the client/test
  partitions remain unchanged. Root-label restriction and per-channel
  intensity inversion are also implemented as root-only transformations with
  unchanged clients/test and explicit active/reserved indices. Full sensitivity
  runs have not been executed.
- A small, explicitly out-of-family semantic green-car path using the 30
  CIFAR-10 training indices in the attack authors' Backdoors101 configuration.
  All 30 indices were checked against an existing official CIFAR-10 copy and
  have car label 1. The new 20 attacker-only / 10 held-out split is recorded
  and excluded from normal client/root partitions; ASR uses unmodified held-out
  images, not a synthetic patch. The real-data preflight passed on the HPC copy
  with three disjoint 200-image root splits and no semantic-source leakage.
  No semantic attack experiment has been run yet.

The synthetic one-round test is only an integration check. It is not a model
comparison or a calibration run. The current local applicable test suite
passes; the one omitted legacy test compares the HPC v2 environment
with the old confirmatory-v1 lock and is not a v2 validity check.
PBS GPU preflight job `38455.mgmt01` exited 0 on an NVIDIA H100, with
PyTorch 2.11.0+cu128, torchvision 0.26.0+cu128, and cryptography 48.0.0.
The HPC TierGuard 2 preflight now fails only because the protocol remains
explicitly unfrozen; all nine method names resolve and the environment check
passes. This is the correct state before development calibration and attack
validation, not permission to start confirmatory seeds.
The preflight now also requires, if status is ever changed to `frozen`, a
complete source/configuration hash manifest, a matching clean Git freeze tag,
and a hashed evidence artifact for every listed gate. Changing the status
word alone cannot unlock confirmation. None of these v2 freeze artifacts has
been created yet.

The three benchmark datasets are present in a separate HPC data directory and
a preparation manifest records 24 file hashes, expected
train/test sizes and per-class counts. A read-only recheck of all 24 files,
sizes and class counts passed. This is preparation, not a v2 freeze.
An H100 one-round full-FashionMNIST clean pilot at the planned 60-client,
six-edge topology exposed a 5.1-second per-candidate GPU synchronization
bottleneck in pattern/target selection. A vectorized equivalent reduced the
one-round TierGuard 2 runtime from 287 to 31 seconds (separate jobs) and
preserved all 30 selected client pattern/target choices and held-out gains
exactly in that paired pilot. The one-round clean accuracies are not a
meaningful effectiveness comparison. Nine 40-round, source-attested
FashionMNIST clean development runs are complete, matched and indexed with
no errors. A separate 27-run, three-dataset, three-attack, three-seed
FedAvg attack-validity campaign, 18 MNIST/CIFAR-10 clean-calibration
runs and nine calibrated FashionMNIST TierGuard 2 attack-development
runs have been submitted on the HPC from fixed, separate source clones.
The attack matrix has a fail-closed run/provenance index. No confirmatory
seed has run.
The FashionMNIST and MNIST FedAvg attack-validity submatrices are now
complete (9/9 each) and documented in
`docs/TIERGUARD2_ATTACK_VALIDITY_2026-09-24.md`. They establish attack
strength in development, not defence efficacy. CIFAR-10 finished 9/9 but
failed the validity gate: three optimized-trigger runs produced non-finite
updates, and all attacked runs had poor clean utility. Its original raw runs
remain available as invalid development evidence. The separate three-rate,
three-seed clean CIFAR-10 repair grid and all nine MNIST TierGuard 2
attack-development jobs were cancelled before running. Initially, only two of
nine FashionMNIST TierGuard 2 attack-development jobs completed and the other
seven were cancelled. Those seven cells subsequently completed under the
user-approved single-job workflow; the full nine-run panel passed validation
on 27 September and automated submissions stopped. The
attacker-side optimizer now fails closed on non-finite objectives, gradients
and triggers, with a regression test; this source change does not
retroactively validate old runs.

## Still required before confirmation or manuscript rewriting

1. Validate the source-audited FLAME and bounded FedGame adaptations in actual
   development runs, including FLAME's small-edge fallback frequency and
   FedGame's root/reconstruction budget. Verify HFLMND against author code if
   it becomes available; otherwise disclose the paper's under-specified
   choices and keep them fixed before confirmation. Do not call any of these
   two-tier adaptations author-code-identical. The new five-clients-per-edge
   topology also invalidates the old four-client argument for excluding
   Krum with a one-Byzantine tolerance setting. A hierarchical Krum adapter
   with explicit `f=1` and a fail-closed `n>2f+2` check is now available as
   an exploratory secondary comparator; it still needs development runs
   before any claim or confirmatory inclusion.
2. Validate the defence-aware optimized-trigger attack and semantic green-car
   implementation on real CIFAR-10; run sign-flip/ALIE, stronger-heterogeneity, and
   the implemented root-sensitivity panels;
   validate each against undefended FedAvg. The current distributed attack
   uses four coordinated corner components; it is not a complete reproduction
   of the published DBA attack family.
3. Run the actual study on GPU compute nodes, not on the login host. A separate
   Python 3.12.13 `uv` environment is installed on the HPC host from the v2
   lock, including Linux CUDA transitive pins. `uv pip check` passes for all
   65 packages and a dry-run install would make no changes. The minimal PBS
   GPU/dependency preflight passed, but it is not a training run or a timing
   benchmark.
4. Finish a frozen development grid and tune all baselines with the same
   budget. Three-seed clean calibration is complete on all datasets at the
   original development settings, but CIFAR-10 protocol repair would require
   recalibration. Freeze configuration,
   code, partitions, software, and attack instances before the first
   confirmatory seed.
5. Execute and validate all planned 12-seed main, clean, edge, ablation, and
   sensitivity panels. Select the strongest baseline from development ASR
   before opening confirmation. Report every adverse outcome.
6. Only then write the clean manuscript, changes-only highlighted manuscript,
   supplementary results, and plain reviewer response. A DOI deposit remains
   a separate editorial requirement; none is claimed here.

The study matrix and preconfirmation gates are recorded in
`configs/tierguard2/protocol_draft.yaml` and explicitly marked **prefreeze**.

## Novelty boundary to test, not assume

| Work | Published inspection mechanism | Architectural distinction to test |
| --- | --- | --- |
| [FedGame](https://papers.nips.cc/paper_files/paper/2023/file/a6678e2be4ce7aef9d2192e03cd586b7-Paper-Conference.pdf) | Auxiliary global model, reverse-engineered trigger/target, client genuine scores | Its published server is flat; a faithful two-tier adaptation is still needed. |
| [FilterFL](https://ink.library.smu.edu.sg/sis_research/10634/) | Data-free trigger-image generation from old/new global-model knowledge differences | It is not a root-based client-and-edge counterfactual audit; the original study must still be discussed, not ignored. |
| [HFLMND](https://doi.org/10.1016/j.knosys.2026.115270) | Client/edge similarity features, multi-feature clustering, historical suspicion correction | It already handles two layers; two-level placement alone cannot establish novelty. Its equations and procedure are implemented as a disclosed reconstruction with unspecified choices fixed independently of confirmatory outcomes. |
| TierGuard 2 candidate | Disjoint-root change in target-class behaviour relative to the unchanged model, with independently audited edge aggregates and signed random challenges | Novelty would require a validated complementary failure mode and improved held-out outcomes; neither is established yet. |

## Commands used for local checks

```powershell
$env:PYTHONPATH = 'src'
python -m pytest tests/test_tierguard2.py tests/test_tierguard2_decision.py -q
python -m tierguard.cli run --config configs/tierguard2/smoke.yaml
```

The HPC dataset and GPU preflight entry points are
`scripts/verify_semantic_stress_data.py` and
`scripts/tierguard2_gpu_preflight.pbs`. Neither runs a confirmatory seed.

The prior study's lock and freeze manifest remain in the repository for its
tagged release. Because this branch adds new source, the old source manifest
cannot be used as a TierGuard 2 freeze; a distinct v2 manifest is needed.
