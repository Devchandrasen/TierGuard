# TierGuard 2 prefreeze HPC pilots (not manuscript results)

All runs used one NVIDIA H100, real FashionMNIST, 60 clients, six edges,
five selected clients per edge, two local epochs, Dirichlet alpha 0.3, a
disjoint 200/200/200 reference/search/evaluation root. The initial
ten-round pilots
used a fixed 5,000-image test subset: the `data.test_size=null` override
activated the base configuration's `validation_size=5000` fallback. The
one-round runtime profiler explicitly used 1,000 test images. These sizes
are now recorded correctly; the later scaled-distributed pilot and attested
development rerun request all 10,000 test images explicitly. The PBS
outputs and complete run directories are
on `arc-hpc` under the dedicated `tierguard2_env_2026_09_23` workspace.
These pilots use seeds 1991--1993, none of which is a development or
confirmatory seed. They must not enter manuscript inference.

| Pilot | PBS job | Rounds | Final clean accuracy | Final ASR | Interpretation |
| --- | --- | ---: | ---: | ---: | --- |
| FedAvg, no attack, seed 1992 | 38536 | 10 | 0.7960 | undefined | Clean comparator for utility diagnostic only |
| TierGuard 2, clip multiplier 2, no attack, seed 1992 | 38536 | 10 | 0.6868 | undefined | Unacceptable early utility deficit at this setting |
| TierGuard 2, clip multiplier 8, no attack, seed 1992 | 38537 | 10 | 0.8176 | undefined | Candidate for independent development testing |
| TierGuard 2, clip multiplier 16, no attack, seed 1992 | 38537 | 10 | 0.8004 | undefined | Candidate for independent development testing |
| FedAvg, deterministic unknown patch/model replacement, 20% malicious, seed 1992 | 38536 | 10 | 0.7272 | 0.9839 | One effective attack instance against undefended FedAvg; not a cross-seed result |
| FedAvg, component-distributed backdoor, 20% malicious, seed 1993 | 38550 | 10 | 0.7692 | 0.0230 | Ineffective attack at the tested strength; cannot enter the main matrix unchanged |
| FedAvg, attacker-local optimized patch, 20% malicious, seed 1993 | 38551 | 10 | 0.6680 | 0.9270 | Effective in this one pilot; requires cross-seed validation |
| FedAvg, scaled component-distributed backdoor, 20% malicious, seed 1993 | 38566 | 10 | 0.6542 | 1.0000 | Full 10,000-image test; effective but with considerable clean-utility harm in this one pilot |

At multiplier 8, 96.7% of selected client updates were clipped in round 1
and 20% in round 10. At multiplier 16, those fractions were 90% and 0%.
The target class and 3×3 location for the attack pilot were 9 and (12, 0),
drawn by the method-independent SHA-256 instance key. The defender did not
receive them. The resolved instance is recorded with its run.

One separate TierGuard 2 attack-audit diagnostic (PBS 38538; one round,
multiplier 16, provisional threshold 1.0 so no risk suppression) selected
six malicious and 24 benign clients. Median held-out target gain was 0.189
for malicious versus 0.095 for benign updates; five of six malicious
updates selected the actual target/location probe. Nevertheless, the gain
distributions overlapped: only three of six malicious gains exceeded the
benign 95th percentile. This is a warning against treating the probe score
as a calibrated detector or claiming robustness from the pilot.

A separate one-round profiler (PBS 38534 before and 38535 after vectorization)
identified a 5.1-second per-candidate synchronization bottleneck. The
vectorized selection preserved all 30 client-selected patterns, target
classes and held-out gains exactly in that paired run, reducing one-round
runtime from 287 to 31 seconds. The runtime observation is not a
hardware-normalized comparison of algorithms.
The queue placed jobs on two H100 nodes with different NVIDIA drivers
(gpu01: 570.124.06; gpu02: 580.126.16), and observed wall times varied
materially. Later runs record hostname, device and driver; confirmatory
comparisons must control or stratify node assignment.

The three real dataset snapshots were checked against a 24-file SHA-256
manifest, including expected class counts. This does not freeze the v2
protocol. The next gate is three clean development seeds with the two
clipping candidates, followed by clean-score calibration and attack-strength
checks across all planned datasets. No confirmatory seed has run.

The unscaled distributed-component attack's ASR fell from 0.184 in round 2
to 0.023 in round 10 despite clean model learning. A new, still-distributed
component-wise version applies matched model-replacement scaling to each
malicious update. The seed-1993 pilot reached ASR 1.0000 but reduced clean
accuracy to 0.6542; additional development seeds and the full 40-round
schedule are needed to establish attack validity and utility effects. This
change is prefreeze, not a post-confirmation alteration.

One-round full-data integration/runtime checks for the source-audited
baselines completed: FLAME 30.8 seconds, the bounded FedGame adaptation
4.9 seconds and the HFLMND reconstruction 4.2 seconds. These are different
algorithms with provisional settings and cannot be used as an efficiency or
clean-utility comparison.

The first attempt at three 40-round clean development runs was not used for
calibration: compute nodes lacked `git`, so run-level commit and clean-tree
provenance were unavailable. Six further development jobs were cancelled
once this was discovered, with partial logs retained. A Git 2.43.5 binary
from the HPC login image was placed in the dedicated shared environment and
tested on both GPU nodes (SHA-256
`d220991337f55201c733e9ad80c11bec384680ec7b927a341a8cf03bb62d19a4`).
The rerun requires readable, clean Git provenance
before training starts and uses an explicit 10,000-image test set. The
initial attempt is diagnostic only and must not be mixed with the rerun.
