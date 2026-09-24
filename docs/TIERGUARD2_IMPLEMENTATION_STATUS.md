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
  effective attacks against FedAvg, but the full cross-dataset validity
  campaign is still running; pilots are not inferential evidence.
- Main-attack target class and patch location can now be drawn from a
  deterministic SHA-256 keyed instance, independent of method, for paired
  dataset/attack/seed comparisons. The location is chosen from the
  prespecified nine-position bounded search family; it is hidden from the
  auditor but this is **not** arbitrary-location generalisation. The resolved
  attack configuration and digest are saved in each run.
- A calibration utility requiring three distinct clean development seeds and
  complete per-round audit logs. It now produces separate client- and
  edge-level thresholds because their clean score distributions differ.
  The FashionMNIST nine-run clean development index passed and is recorded in
  `docs/TIERGUARD2_CLEAN_CALIBRATION_2026-09-24.md`; MNIST and CIFAR-10
  calibration remain outstanding. A primary decision-rule implementation checks
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
The FashionMNIST FedAvg attack-validity submatrix is now complete (9/9)
and is documented in `docs/TIERGUARD2_ATTACK_VALIDITY_2026-09-24.md`.
It establishes attack strength in development, not defence efficacy.

## Still required before confirmation or manuscript rewriting

1. Validate the source-audited FLAME and bounded FedGame adaptations in actual
   development runs, including FLAME's small-edge fallback frequency and
   FedGame's root/reconstruction budget. Verify HFLMND against author code if
   it becomes available; otherwise disclose the paper's under-specified
   choices and keep them fixed before confirmation. Do not call any of these
   two-tier adaptations author-code-identical. The new five-clients-per-edge
   topology also invalidates the old four-client argument for excluding
   Krum with a one-Byzantine tolerance setting; reconsider it as a
   prespecified secondary comparator or document a new applicability reason
   before freezing the manuscript.
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
   budget. The three FashionMNIST clean development seeds are complete;
   MNIST and CIFAR-10 clean calibration remains. Freeze configuration,
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
