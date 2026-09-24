# TierGuard 2 prefreeze HPC pilots (not manuscript results)

All runs used one NVIDIA H100, real FashionMNIST, 60 clients, six edges,
five selected clients per edge, two local epochs, Dirichlet alpha 0.3, a
disjoint 200/200/200 reference/search/evaluation root, and the full 10,000
image test set unless noted. The PBS outputs and complete run directories are
on `arc-hpc` under the dedicated `tierguard2_env_2026_09_23` workspace.
These pilots use seed 1991 or 1992, neither of which is a development or
confirmatory seed. They must not enter manuscript inference.

| Pilot | PBS job | Rounds | Final clean accuracy | Final ASR | Interpretation |
| --- | --- | ---: | ---: | ---: | --- |
| FedAvg, no attack, seed 1992 | 38536 | 10 | 0.7960 | undefined | Clean comparator for utility diagnostic only |
| TierGuard 2, clip multiplier 2, no attack, seed 1992 | 38536 | 10 | 0.6868 | undefined | Unacceptable early utility deficit at this setting |
| TierGuard 2, clip multiplier 8, no attack, seed 1992 | 38537 | 10 | 0.8176 | undefined | Candidate for independent development testing |
| TierGuard 2, clip multiplier 16, no attack, seed 1992 | 38537 | 10 | 0.8004 | undefined | Candidate for independent development testing |
| FedAvg, deterministic unknown patch/model replacement, 20% malicious, seed 1992 | 38536 | 10 | 0.7272 | 0.9839 | One effective attack instance against undefended FedAvg; not a cross-seed result |

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

The three real dataset snapshots were checked against a 24-file SHA-256
manifest, including expected class counts. This does not freeze the v2
protocol. The next gate is three clean development seeds with the two
clipping candidates, followed by clean-score calibration and attack-strength
checks across all planned datasets. No confirmatory seed has run.
