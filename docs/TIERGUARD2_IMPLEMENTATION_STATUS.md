# TierGuard 2 research branch — implementation status

This branch is a new, unfinished study. It does **not** change the published
`protocol-v1-freeze` Git tag or convert the earlier six-seed results into
evidence for a new method. No confirmatory outcome or superiority claim exists.

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
- The same optional receipt/challenge wrapper is available to existing
  hierarchical FedAvg, FLTrust, coordinate median, RFA, PTA, and two-tier
  FLAME/FedGame defender adaptations and a paper-derived HFLMND reconstruction.
  FLAME follows the published cosine/HDBSCAN majority
  filter, median-norm clipping, equal averaging, and adaptive noise structure;
  its two-tier application and small-edge fallback require explicit reporting
  and source-validation before confirmation. FedGame follows the official
  auxiliary-average model, per-class trigger reconstruction, smallest-mask
  target selection, and genuine-score weighting, but its two-tier use and
  reconstruction budget likewise need development validation.
  Payload byte counts are recorded; these are **not** real network timings.
- The supplied full HFLMND article has now been inspected. Its NSFE feature
  equations, binary hierarchical clustering, historical suspicion correction,
  and equal-average aggregation are implemented at both layers. The paper
  omits the linkage, benign-cluster labelling and all-rejected conventions;
  these are fixed in `docs/HFLMND_PAPER_DERIVATION.md`. This is not a claim of
  matching unpublished author code or its reported outcomes. The one-round
  synthetic HFLMND/challenge smoke test completed without false rejection.
- Attack-side unknown-location patch/model-replacement, four-corner
  distributed-trigger, and attacker-local gradient-optimized patch constructors.
  The optimized patch penalizes similarity to the defender's fixed probe
  templates and is shared by selected malicious clients within a round. Its
  actual values are saved per round. These are implementation paths, not yet
  validated threat-strength experiments.
- A calibration utility requiring three distinct clean development seeds and
  complete per-round audit logs. A primary decision-rule implementation checks
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
comparison or a calibration run. On the separate TierGuard 2 HPC environment,
all 59 applicable tests now pass, including three HFLMND-specific tests, both
locally and in the pinned HPC environment on the committed branch. The omitted
legacy test compares the HPC v2
environment with the old confirmatory-v1 lock and is not a v2 validity check.
PBS GPU preflight job `38455.mgmt01` exited 0 on an NVIDIA H100, with
PyTorch 2.11.0+cu128, torchvision 0.26.0+cu128, and cryptography 48.0.0.
The HPC TierGuard 2 preflight now fails only because the protocol remains
explicitly unfrozen; all nine method names resolve and the environment check
passes. This is the correct state before development calibration and attack
validation, not permission to start confirmatory seeds.

## Still required before confirmation or manuscript rewriting

1. Source-check both hierarchical FLAME and FedGame adaptations. Verify the
   HFLMND reconstruction against author code if it becomes available; otherwise
   disclose the paper's under-specified choices and keep them fixed before
   confirmation. Do not call this reconstruction author-code-identical.
2. Validate the defence-aware optimized-trigger attack and semantic green-car
   implementation on real CIFAR-10; run sign-flip/ALIE, stronger-heterogeneity, and
   the implemented root-sensitivity panels;
   validate each against undefended FedAvg. The current distributed trigger is
   a single four-corner pattern, not the full published DBA attack.
3. Run the actual study on GPU compute nodes, not on the login host. A separate
   Python 3.12.13 `uv` environment is installed on the HPC host from the v2
   lock, including Linux CUDA transitive pins. `uv pip check` passes for all
   65 packages and a dry-run install would make no changes. The minimal PBS
   GPU/dependency preflight passed, but it is not a training run or a timing
   benchmark.
4. Finish a frozen development grid and tune all baselines with the same
   budget. Run three clean development seeds per dataset with provisional
   threshold 1.0, calibrate scores, and freeze configuration, code, partitions,
   software, and attack instances before the first confirmatory seed.
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
