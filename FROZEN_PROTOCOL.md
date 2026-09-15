# Confirmatory-v1 frozen protocol

## Freeze boundary

The protocol is independently frozen before confirmatory execution. A dedicated
Git commit and annotated tag identify the pre-result state. The SHA-256 manifest
at `configs/confirmatory_v1/FROZEN_SHA256SUMS` covers source, tests, all
confirmatory configs, the runner, analysis code, version pins, and package
metadata. The campaign runner exits before training if the manifest does not
match.

No seed in the frozen set (101, 202, 303, 404, 505, 606) was part of the retained
three-seed evidence (1, 2, 3). Hyperparameters are fixed across these held-out
seeds. Any later code or configuration change requires a new protocol version and
fresh results; it cannot be mixed into confirmatory-v1.

## Design

- Datasets: MNIST, FashionMNIST, scikit-learn Digits
- Methods: HFL-FedAvg, HFL-FLTrust, HFL-TrimmedMean, HFL-RFA, TierGuard-PTA
- Attacks: backdoor model replacement and adaptive TierGuard-aware backdoor
- Malicious fraction: 0.2
- Data partition: Dirichlet, alpha 0.5
- Clients/edges/selected per round: 20/5/10
- Seeds: six paired held-out seeds
- Runs: 3 × 5 × 2 × 6 = 180
- Device: CPU

MNIST and Digits use 20 rounds; FashionMNIST uses 30. Dataset-specific sample,
root-set, and batch sizes are fixed in their YAML files.

## Pairing invariant

Within a dataset/attack/seed cell, all five methods receive the same dataset
subsample, client partition, malicious-client set, selected clients, model
initialisation, local-loader order, and reference-loader order. The
predefined-trigger audit uses a separate deterministic loader generator to avoid
changing later client or root batches for TierGuard only.

## Inference

The pre-specified outcomes are clean accuracy, macro F1, and attack success rate.
For each baseline, the paired seed differences are analysed using a two-sided
exact sign-flip permutation test, paired Cohen's dz, and a 95% t interval for the
mean paired difference. Holm correction is applied across the four baseline
comparisons within each dataset × attack × metric family. Six seeds permit a
minimum attainable two-sided exact p-value of 0.03125 before multiplicity
correction.
