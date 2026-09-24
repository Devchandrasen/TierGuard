# TierGuard 2 clean-only calibration (development, not confirmation)

The three source-attested FashionMNIST clean development seeds (2001--2003)
ran for 40 rounds with 30 selected clients and six active edges per round.
The source commit was `950d8a7f6f27622ceaabdec1d64cea881c636d4e` and the test set
contained all 10,000 images. Each clipping candidate yielded 3,600 client
and 720 edge audit scores. The provisional threshold was 1.0, so these
clean runs applied no risk downweighting.

The nine-run completeness index passed with no errors: three clean FedAvg
runs and three runs for each TierGuard 2 clip candidate had identical
partitions within seed, complete round and audit records, clean source
provenance, and undefined backdoor ASR. Its SHA-256 is
`e99acb3dd70e8af9159c6a6f5943551980af80c8ea551cf4ffae889cad4b1e44`.
Paired clean-accuracy differences (TierGuard 2 minus FedAvg) were
`[+0.0040, -0.0027, +0.0007]` for clip 8 and
`[-0.0002, -0.0048, -0.0005]` for clip 16. These three-seed development
comparisons do not justify a statistical claim or finalize the clip choice.

The pooled 95th-percentile held-out target-gain threshold was 0.3399 for
clip multiplier 8 and 0.3671 for clip multiplier 16. However, the two
hierarchy levels had visibly different clean score distributions:

| Clip multiplier | Client 95th percentile | Edge 95th percentile |
| ---: | ---: | ---: |
| 8 | 0.3590 | 0.2150 |
| 16 | 0.3827 | 0.2349 |

The full calibration records, including hashes of all 120 round-audit
files for each candidate, are stored in the separate HPC environment as
`calibration_clip8_source_attested.json` (SHA-256
`8e68fc7cb73ebab9cadcbcb14794e8ae016e75a95dafa259549a3f7e323e2345`)
and `calibration_clip16_source_attested.json` (SHA-256
`1a99eefc264ef5fa37d5107763de7b991491e6e0745e945bc441a0650765ec13`).
The calibration script SHA-256 is
`1dde4c999eea93dae7a5c690c2ac8275d3ee096b01016dcea5c00e54b21b3427`.

These are empirical quantiles of overlapping, temporally dependent audit
events, **not** per-event false-positive guarantees. Pooling clients and
edges would privilege the more numerous client scores (5:1) and set a
much higher-than-edge-specific cutoff at the cloud. Before any
confirmatory run, the method therefore uses separate frozen 95th-percentile
thresholds at the client and edge levels. The same clean-only calibration
has now been applied on MNIST; CIFAR-10 remains outstanding. The legacy
single threshold remains a provisional fallback for smoke/pilot configs;
it is not the intended confirmatory configuration.

Neither the clipping candidate nor the risk weight is selected from these
quantiles alone. Clean utility must be compared with matched FedAvg on
all three development seeds, and attack-side parameter selection must
follow the declared development grid and baseline budget. No positive
superiority conclusion follows from these clean runs.

## MNIST completed clean calibration

The nine 40-round MNIST clean development runs passed the strengthened
fail-closed index with one clean source commit, matched per-seed partitions,
complete round/audit records, finite metrics and no non-finite updates.
The fixed training source commit was
`9f396ccd2a71de79967729eaa71e3d1759420755`.
The index SHA-256 is
`0d49266854445f136672e330eebf2b5783719e2228ccd73360a4282e34737f09`;
the strengthened index script SHA-256 is
`e4683292f9e7aea3d65a95e98e473f56f8b6c9a01110b0567b4f832685ac0724`.
FedAvg clean accuracies were 0.9865, 0.9859 and 0.9857 for development
seeds 2001--2003. The matched TierGuard 2 minus FedAvg differences were
`[+0.0003, +0.0002, 0.0000]` at clip 8 and
`[+0.0002, +0.0001, +0.0004]` at clip 16. These are descriptive
development results, not evidence of superiority.

| MNIST clip multiplier | Client 95th percentile | Edge 95th percentile | Calibration JSON SHA-256 |
| ---: | ---: | ---: | --- |
| 8 | 0.239614 | 0.071889 | `a3ce46e3ec5545c5cc4eb3044c4e14f1a135da5539efe28d295ea6a2c4f378f9` |
| 16 | 0.245875 | 0.088684 | `525254c60584838f8d76b71be2ec8529557d5431485e20b40c00d4868da755ba` |

Each MNIST calibration contains 3,600 client and 720 edge scores from the
three clean runs. The stricter finite-gain calibrator was executed outside
the immutable training clone (script SHA-256
`510cbc4def22a3b51e8f6a68cf6cfd89d9b9d604e9f6ce2466e7bb8bd465b70c`).
The thresholds remain candidates until the attack-development and baseline
budget checks determine the final configuration before confirmation.
