# TierGuard 2: completed FashionMNIST development panel
Date: 27 September 2026. Status: **9/9 complete; automatic submissions stopped.**

## Assessment
The clip-8 candidate reduced final-round attack success relative to paired undefended hierarchical FedAvg in all nine development runs. It did not eliminate the attacks. The optimized-trigger condition retained **52.98% and 54.37% ASR in seeds 2002 and 2003**, respectively. Its mean ASR was 38.90%, with a large between-seed sample standard deviation of 25.60 percentage points.

This is descriptive development evidence on one dataset, not proof of superiority over robust baselines, cross-dataset robustness, novelty, or submission readiness. The 12-seed confirmatory decision rule has not been tested. No adverse run was excluded or repeated.

## Complete outcomes
ASR is attack success rate; lower is better. Accuracy is clean-test accuracy of the model trained **under the stated attack**, not accuracy from an attack-free training comparison. Values are percentages, except the last column, which is a percentage-point difference. Each mean has three development seeds; ± is the **sample standard deviation**, not a confidence interval. Every result is from round 40, not a selected best round.

| Attack | TierGuard 2 ASR, mean ± SD (%) | FedAvg ASR, mean (%) | TierGuard 2 accuracy, mean ± SD (%) | Paired ASR difference, TG2 − FedAvg (pp) |
| --- | ---: | ---: | ---: | ---: |
| Unknown patch + model replacement | 23.84 ± 10.75 | 99.87 | 88.18 ± 0.38 | -76.03 |
| Distributed backdoor | 6.69 ± 3.44 | 100.00 | 88.05 ± 0.24 | -93.31 |
| Defence-aware optimized trigger | 38.90 ± 25.60 | 99.19 | 87.86 ± 0.19 | -60.29 |

All seed-level outcomes, including the weak cases:

| Attack | Seed | TG2 ASR (%) | FedAvg ASR (%) | TG2 accuracy (%) | FedAvg accuracy (%) | Edge risk > client suggestion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Unknown patch + model replacement | 2001 | 27.20 | 100.00 | 88.05 | 80.14 | 2/240 |
| Unknown patch + model replacement | 2002 | 32.51 | 100.00 | 88.61 | 84.12 | 2/240 |
| Unknown patch + model replacement | 2003 | 11.81 | 99.61 | 87.89 | 75.48 | 8/240 |
| Distributed backdoor | 2001 | 10.67 | 100.00 | 87.98 | 82.23 | 3/240 |
| Distributed backdoor | 2002 | 4.69 | 100.00 | 88.32 | 83.84 | 6/240 |
| Distributed backdoor | 2003 | 4.72 | 100.00 | 87.86 | 79.53 | 11/240 |
| Defence-aware optimized trigger | 2001 | 9.36 | 99.89 | 87.83 | 81.23 | 3/240 |
| Defence-aware optimized trigger | 2002 | 52.98 | 98.01 | 88.06 | 84.31 | 8/240 |
| Defence-aware optimized trigger | 2003 | 54.37 | 99.68 | 87.69 | 79.36 | 16/240 |

Machine-readable full-precision values and record hashes are in `seed_results.csv`. The final index supplies the paired source paths. Means use the three seeds equally; no pooled test-example or round-level inference is performed. Python and independent JavaScript calculations agree to 1e-14.

## Protocol and validation
The saved configurations use FashionMNIST, 60 clients, six edges, five selected clients per edge per round, 40 rounds, two local epochs, Dirichlet alpha 0.3, and 20% malicious clients. Three disjoint 200-example roots support reference updates, probe search, and held-out probe scoring. The clean-test set contains 10,000 examples. Client SGD uses learning rate 0.05, momentum 0.9, weight decay 0.0001, and batch size 64.

The TierGuard 2 clip multiplier is 8.0. The client and edge gain thresholds are 0.35900445729494096 and 0.21499230563640584, respectively, as fixed by the supplied clean-development calibration. The audit receives no attack configuration. The patch-location family in this implementation is bounded to nine positions; “unknown” does not mean unrestricted spatial or semantic attacks. Neither differential privacy nor secure aggregation is enabled. The signed-receipt/challenge interface is simulation evidence, not a deployed network or cryptographic confidentiality claim.

Validation used the existing index outside the unchanged training checkout, followed by an independent local package check:

| Check | Outcome |
| --- | --- |
| Exact three attacks × three development seeds | 9/9; no duplicate or missing cell |
| Final scheduler job 39388.mgmt01 | Finished, exit 0; walltime 00:11:49 |
| Entire account outstanding jobs | Empty at the completion check and at 15:08 UTC |
| Original remote panel index | Complete, zero errors |
| Run lengths and populated numeric metrics | 40 rounds each; finite; zero stability failures |
| Local package | 9 TG2 attack + 9 paired FedAvg attack + 9 clean/calibration-context runs |
| Local round and TG2 attack-audit checks | 1,080 round records; 360 audit files |
| Paired partitions and attack-instance digests | Exact matches for all nine TG2/FedAvg pairs |
| Index/calibration-referenced file hash checks | 192 passed |
| TG2 source | Clean commit `897b419efa8c47774efd8ed14c41e020ad4df31e` |
| Scheduler follow-up | Existing hourly automation paused; no subsequent job submitted |

ASR fields are intentionally empty in attack-free calibration runs because no backdoor is installed. Scheduled metrics before the first evaluation are also blank. These defined absences are not silently converted to zeros; all populated numeric fields were checked for finiteness.

Source capsules are included for TierGuard 2, paired FedAvg, and clean calibration. Their full resolved configurations, provenance, original partitions, per-round metrics, audit and attack artifacts are preserved. The original 56-run archive, earlier timestamped indices, frozen training clones and prior study remain unchanged. The dataset manifest is included; raw benchmark images and the HPC environment itself are not bundled.

## What these results do and do not establish
1. Attack validity: paired FedAvg mean ASR is 99.87%, 100.00%, and 99.19% across the three attacks. These attacks are effective against that undefended comparator at the evaluated settings.
2. Residual vulnerability: unknown-patch ASR ranges from 11.81% to 32.51%. Optimized-trigger ASR ranges from 9.36% to 54.37%. These outcomes do not support a blanket defence claim.
3. Cross-layer scores: edge risk exceeded its client-derived suggestion in 12/720, 20/720, and 27/720 comparisons, respectively (59/2,160 overall). These correlated diagnostic observations show score differences, **not** that the cloud audit causally improves ASR. Matched ablations are required.
4. Clean utility: accuracy under attack remains approximately 88%. The included clean calibration collected scores with threshold 1.0, disabling risk downweighting. It does not establish clean-training non-inferiority for the final calibrated defence.
5. Statistical scope: these are three reused development seeds, not 12 independent confirmatory seeds. Neither nine attack–seed cells nor thousands of round/audit records constitute nine or thousands of independent confirmatory seeds. No significance, multiplicity-adjusted superiority, or clean non-inferiority claim is made.
6. Missing comparisons: matched robust baselines, cloud/client ablations, compromised-edge attacks, and cross-dataset validity remain unfinished. In particular, the earlier CIFAR-10 validity failure is not repaired by this FashionMNIST panel.

## Next decision, before any further campaign
The defensible next stage is a bounded development comparison of matched robust baselines and client-only/cloud-only/full-audit ablations, with the same partitions, attack instances, authentication interface and equal tuning budget. This should establish whether the counterfactual audit adds value beyond clipping and simpler robust aggregation, especially on the two high-ASR optimized-trigger seeds.

Any method change must use a new isolated source snapshot and explicitly remain development, retaining these adverse outcomes. CIFAR-10 protocol repair and attack validity must precede its defence comparisons. Confirmation should remain locked until baseline development, calibration, failure tests and a complete independent protocol freeze pass.

**No next campaign has been submitted or authorized by completion of this panel.** The existing automatic submission workflow is paused for review.

## Evidence identity
The accompanying local archive is
`Rajanmani/output/TierGuard2_FashionMNIST_Development_2026-09-27.zip`
(7,959,654 bytes; 1,634 payload files plus the manifest). Every ZIP member
passed CRC checking, and every payload's SHA-256 matched the manifest after
compression. The raw-record and CSV paths above refer to that evidence package.

Archive SHA-256:
`df80958e99a3749a42dc03cb7a93acb92ade717ccbd633e4dce41e6efed177b5`.

Final index: `fashion_t2_attack_development_index_2026_09_27T145912Z.json`

SHA-256: `dded43b3d024cf0a17f1ca472c2812ad4cd54da86222d0fa6bba41906cdd76f0`

FedAvg index SHA-256: `432c72da0b14510ee73391dd0cd71b43ce2497c2d146ec8bbe71bc0b9c61083d`

Calibration SHA-256: `8e68fc7cb73ebab9cadcbcb14794e8ae016e75a95dafa259549a3f7e323e2345`

Confidence assessment: **share with caveats**. High confidence in the verified run completeness and descriptive arithmetic; insufficient evidence for robust-baseline superiority or a general mechanism claim. The data-validation skill guided the completeness checks, independent arithmetic cross-check and separation of execution validity from scientific performance.
