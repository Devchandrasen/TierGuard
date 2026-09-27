# TierGuard 2 evidence review — 27 September 2026

## Overall assessment: needs further experiments

This is an internal evidence audit, not an independent peer review and not a
submission-ready manuscript. The approved new-study decision rule remains
unchanged. None of the 12 confirmatory seeds has run. The prior frozen study
and its manuscript must not be presented as confirmation of TierGuard 2.

## Source and completeness checks

The completed records comprise 27 clean-development runs, 27 FedAvg
attack-validity runs and two TierGuard 2 FashionMNIST attack-development
runs. All 56 records are retained, including the rejected CIFAR-10 evidence.
The downloaded snapshot passed the packaging integrity checks with zero
errors: 56 run records and 834 index/calibration file-hash comparisons.
The compressed transfer archive matched SHA-256
`37e98b2931dd9a673738e3c8747257f5b5089618af7598536c239aa212c56fa3`.
This validates the copy, not the scientific acceptability of failed panels.

| Panel | Completion and validity | Permitted interpretation |
| --- | --- | --- |
| Clean development: three datasets, three seeds, FedAvg plus two clipping candidates | 27/27; separate dataset indices passed | Clean calibration and descriptive utility only |
| FedAvg attacks: MNIST and FashionMNIST | 18/18; indices passed | Attack strength against undefended FedAvg in development |
| FedAvg attacks: CIFAR-10 | 9/9 finished; panel rejected | Three optimized-trigger runs had non-finite updates; all attacked runs had low clean utility. Do not use for a defence claim. |
| TierGuard 2 attacks: FashionMNIST | 2/9; seven cancelled | Two-seed, one-attack exploratory observation only |
| CIFAR-10 clean learning-rate repair | 0/9; cancelled | No evidence |
| TierGuard 2 attacks: MNIST | 0/9; cancelled | No evidence |
| Matched tuned robust baselines, full edge-attack/ablation/sensitivity panels and confirmation | Not completed | No superiority, mechanism-isolation or cross-dataset robustness claim |

The new CIFAR-10 clean index passed with no errors (SHA-256
`947cfa92f83d2cbc2839cd5e1aa8a55bfbc7449a0afc77029570f5d2dae07863`).
The FashionMNIST attack-development index deliberately failed completeness,
identifying the exact seven missing cells and no other validation error
(SHA-256 `bb288121abbaac5652d360ff91f1d51ba286396e30d888938a7d6643a2554658`).
Those two observed pairs have matching partition hashes, deterministic attack
instances, complete 40-round records, clean-source attestations and zero
recorded numerical-stability failures.

## Verified exploratory outcomes

| FashionMNIST unknown-patch/model-replacement attack | FedAvg ASR | TierGuard 2 ASR | FedAvg clean accuracy | TierGuard 2 clean accuracy |
| --- | ---: | ---: | ---: | ---: |
| Development seed 2001 | 1.000000 | 0.272000 | 0.8014 | 0.8805 |
| Development seed 2002 | 1.000000 | 0.325111 | 0.8412 | 0.8861 |

The descriptive mean ASR reduction is 0.701444 across these two observed
pairs. It is not a three-seed panel mean, a confirmatory test or evidence
against the strongest robust baseline. No p-value, confidence claim or
superiority conclusion is appropriate here. Both outcomes must remain
visible even if future runs are less favorable.

The independent edge risk exceeded the client-derived risk suggestion in
only 2 of 240 edge-round comparisons for each completed run (4/480 combined).
This is a logged diagnostic, not proof that the cloud audit adds protection:
the client-only/edge-only ablations and concealed/distributed attack panel
are still missing. Clipping or client-level downweighting could explain the
observed FedAvg contrast.

CIFAR-10 no-attack FedAvg clean accuracies were 0.4372, 0.5004 and 0.4905.
At clip 8, paired TierGuard 2 minus FedAvg differences were
[-0.0011, -0.0066, +0.0050]; at clip 16 they were
[-0.0088, -0.0030, +0.0056]. These runs used provisional threshold 1.0,
so they do not validate the clean-accuracy cost of the calibrated risk rule.

| CIFAR-10 development clipping multiplier | Client gain 95th percentile | Edge gain 95th percentile |
| ---: | ---: | ---: |
| 8 | 0.583161 | 0.239610 |
| 16 | 0.620781 | 0.279663 |

These are empirical, temporally dependent clean quantiles, not guaranteed
false-positive rates. They must be recomputed if the training protocol changes.

## Required corrections and next decision

1. Keep the new-study manuscript unsubmitted until the preconfirmation gates
   and planned decision rule can actually be evaluated. Do not insert these
   two development results into the old paper as if they were confirmation.
2. Respect the HPC administrator's request: the 25 queued jobs were cancelled,
   the two running jobs finished, the queue is empty, and automated continuation
   remains paused. No further GPU jobs are submitted by this review.
3. If an administrator-approved one-job limit becomes available, first finish
   the third FashionMNIST seed and test strong matched baselines/ablations as
   a development feasibility gate. Do not bypass the scheduler with a large
   hidden batch or launch the whole confirmation matrix immediately.
4. Repair and revalidate the CIFAR-10 attack/training protocol in development,
   then complete equal-budget baseline tuning and the remaining mechanism
   and security checks before freezing the study.
5. If no further compute is available, the author must explicitly choose
   whether to pursue the earlier, narrower revision instead. That is a
   different scientific scope and cannot be silently substituted.

The data-validation and evidence-review checks are the reason failed and
incomplete cells remain explicit, and why no submission-ready claim is made.
