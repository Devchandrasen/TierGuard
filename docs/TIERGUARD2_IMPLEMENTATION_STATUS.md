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
  FLAME/FedGame defender adaptations. FLAME follows the published cosine/HDBSCAN majority
  filter, median-norm clipping, equal averaging, and adaptive noise structure;
  its two-tier application and small-edge fallback require explicit reporting
  and source-validation before confirmation. FedGame follows the official
  auxiliary-average model, per-class trigger reconstruction, smallest-mask
  target selection, and genuine-score weighting, but its two-tier use and
  reconstruction budget likewise need development validation.
  Payload byte counts are recorded; these are **not** real network timings.
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
  partitions remain unchanged; full sensitivity runs have not been executed.

The synthetic one-round test is only an integration check. It is not a model
comparison or a calibration run. The ordinary test suite is code-clean except
for the pre-existing exact-environment test in the shared Python installation:
the installed packages do not match the old confirmatory-v1 lock.

## Still required before confirmation or manuscript rewriting

1. Source-check both hierarchical FLAME and FedGame adaptations. Obtain the full
   HFLMND method or official code; the publisher abstract alone is inadequate
   for a faithful baseline. Do not call a feature-clustering surrogate HFLMND.
2. Validate the defence-aware optimized-trigger attack, implement the semantic
   green-car stress test, sign-flip/ALIE and heterogeneity panels; run the
   implemented root-contamination sensitivity;
   validate each against undefended FedAvg. The current distributed trigger is
   a single four-corner pattern, not the full published DBA attack.
3. Establish the exact TierGuard 2 HPC environment. The login shell defaults
   to Python 3.9, but `uv` already has Python 3.12.13 installed; the v2 target
   is pinned separately in `.python-version-tierguard2`. PBS `gpu` queue is
   available. The environment has not been installed or validated on a GPU node.
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
| [HFLMND](https://www.sciencedirect.com/science/article/abs/pii/S0950705126000146) | Client/edge similarity features, multi-feature clustering, historical suspicion correction | It already handles two layers; two-level placement alone cannot establish novelty. Full implementation details are not yet available. |
| TierGuard 2 candidate | Disjoint-root change in target-class behaviour relative to the unchanged model, with independently audited edge aggregates and signed random challenges | Novelty would require a validated complementary failure mode and improved held-out outcomes; neither is established yet. |

## Commands used for local checks

```powershell
$env:PYTHONPATH = 'src'
python -m pytest tests/test_tierguard2.py tests/test_tierguard2_decision.py -q
python -m tierguard.cli run --config configs/tierguard2/smoke.yaml
```

The prior study's lock and freeze manifest remain in the repository for its
tagged release. Because this branch adds new source, the old source manifest
cannot be used as a TierGuard 2 freeze; a distinct v2 manifest is needed.
