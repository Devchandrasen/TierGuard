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
