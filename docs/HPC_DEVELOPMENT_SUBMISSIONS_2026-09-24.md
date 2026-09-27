# TierGuard 2 HPC development submissions

These are **development** jobs, never the 12 prespecified confirmatory seeds.
The isolated HPC environment is
`/home/chandrasen.pandey/tierguard2_env_2026_09_23` on `arc-hpc`.
Datasets are pinned by its `datasets_manifest_2026_09_24.json` (24 file
SHA-256 values). Each run records the resolved configuration, clean Git
commit, partition indices, per-round metrics and node provenance. The two
H100 nodes have different drivers and runtime characteristics, so concurrent
wall times are not an algorithmic efficiency comparison.

## Current execution state (checked 27 September 2026)

All 25 queued jobs (38624--38630 and 38663--38680) were cancelled following
the administrator's request. Jobs 38619 and 38623, which were already running,
finished with exit code 0, 40 rounds and zero recorded numerical-stability
failures. The account queue is empty and automatic continuation is paused.
No resubmission is authorized by this ledger. Obtain an agreed resource limit
before resuming; do not replace the cancelled jobs with a hidden array or
an unbounded chained job.

| Campaign | Source clone and commit | PBS job IDs | Purpose |
| --- | --- | --- | --- |
| FashionMNIST clean, 3 seeds × (FedAvg + 2 clipping candidates) | `project_dev_attested`, `950d8a7f6f27622ceaabdec1d64cea881c636d4e` | 38557--38565 | Completed; nine-run index passed. Calibration JSON and index SHA-256 values are in `docs/TIERGUARD2_CLEAN_CALIBRATION_2026-09-24.md`. |
| FedAvg attack validity, 3 datasets × 3 attacks × 3 seeds | `project_attack_dev`, `aba8ac7b135ac342597a76bd25353c906a40eddc` | FashionMNIST 38567--38575; MNIST 38579--38587; CIFAR-10 38588--38596 | FashionMNIST and MNIST 9/9 each validated. CIFAR-10 9/9 finished but the index rejected three non-finite optimized-trigger runs; all nine CIFAR runs have low clean accuracy. The raw evidence is retained, not treated as valid. |
| MNIST and CIFAR-10 clean, 2 datasets × 3 seeds × (FedAvg + 2 clipping candidates) | `project_clean_dev_more`, `9f396ccd2a71de79967729eaa71e3d1759420755` | MNIST 38602--38610; CIFAR-10 38611--38619 | All 18 completed and passed separate nine-run indices. Both levels calibrated on each dataset; thresholds remain development candidates. |
| TierGuard 2 FashionMNIST attack development, three attacks × three seeds at clip 8 | `project_t2_attack_dev`, `897b419efa8c47774efd8ed14c41e020ad4df31e` | 38622--38630 | Only 38622 and 38623 completed. The other seven were cancelled. The index correctly reports 2/9 and incomplete; no full-panel claim is supported. |
| CIFAR-10 clean learning-rate repair grid, 3 rates × 3 seeds | `project_cifar_lr_dev`, `aba8ac7b135ac342597a76bd25353c906a40eddc` | 38663--38671 | All nine cancelled before running; no repair-grid result exists. |
| TierGuard 2 MNIST attack development, three attacks × three seeds at clip 8 | `project_t2_mnist_dev`, `1b1dacb67d383e5642b61b3bb50099f2a2812414` | 38672--38680 | All nine cancelled before running; no TierGuard 2 MNIST attack-development result exists. |

The snapshots are separate: later repository commits must not be pulled into
any clone while its jobs run, or a run could mix source versions. The
FashionMNIST calibration script was copied to the dedicated environment
outside its training checkout and hash-checked before execution. A development
snapshot of all 56 completed records was validated on 27 September. The final
confirmatory evidence archive still requires the unfinished experiments.
The CIFAR-10 clean-rate index was likewise copied outside the training clone;
its SHA-256 is
`5fc74c6b2c13df71d744f1516405904b1980151e51754fb95d032f3b2fe5d5a2`.
The nine-run TierGuard 2 attack-development index was also copied outside
the active clones (SHA-256
`7c19cb2a58055394f05b9cd821483927282a164e9228e7d1221981a4de0cabce`).
It checks exact paired partitions and attack instances against the validated
FedAvg index, clean-calibrated thresholds, 40-round audit completeness,
source attestation and numerical stability before reporting descriptive
ASR differences or client/edge risk separation. It is not a confirmatory
analysis.
