# TierGuard 2 HPC development submissions

These are **development** jobs, never the 12 prespecified confirmatory seeds.
The isolated HPC environment is
`/home/chandrasen.pandey/tierguard2_env_2026_09_23` on `arc-hpc`.
Datasets are pinned by its `datasets_manifest_2026_09_24.json` (24 file
SHA-256 values). Each run records the resolved configuration, clean Git
commit, partition indices, per-round metrics and node provenance. The two
H100 nodes have different drivers and runtime characteristics, so concurrent
wall times are not an algorithmic efficiency comparison.

## Current execution state (checked 28 September 2026)

**New authorized phase:** after the completed nine-run panel was reviewed,
the user approved the [bounded matched-baseline/ablation screen](TIERGUARD2_FASHION_MECHANISM_PHASE_2026-09-27.md).
At the 07:44 UTC heartbeat checkpoint, the 12 median cells and all three FLTrust
clean seeds had completed with exit 0. The frozen guard validates 15/96 cells
with no errors: 40 rounds, 40 complete audits and zero stability failures
per run. The latest cell (**39441.mgmt01**, fltrust / none / seed 2003)
has 79.66% clean accuracy and macro-F1 0.7886567798662272. Seeds 2001 and
2002 retain 81.21% and 80.31% accuracy and macro-F1 0.8077987660174857
and 0.7862631414726295, respectively; clean ASR is undefined.
All median outcomes remain unchanged, including optimized-trigger
ASRs of 24.03%, 13.01% and 24.12%, distributed-backdoor ASRs of 1.22%,
0.50% and 0.41%, and unknown-patch ASRs of 87.88%, 70.78% and 33.40%.
These development values do not establish comparative efficacy. No tuning
or exclusion was made. All completed run files were copied and hash-verified;
the newest clean run contains 51 files. After validation and refreshed
empty-account, unchanged-ledger and approved hash checks, **39478.mgmt01**
(fltrust / unknown_patch_model_replacement / seed 2001) was submitted once
at 07:50:39 UTC and
verified as the sole running account job. The 96-cell
development matrix is frozen in a new isolated clone; it is NOT a submitted
batch. Hourly continuation permits at most one next job after validation.
The following paragraphs record the preceding panel's completion history.

All 25 queued jobs (38624--38630 and 38663--38680) were cancelled following
the administrator's request. Jobs 38619 and 38623, which were already running,
finished with exit code 0, 40 rounds and zero recorded numerical-stability
failures. The account queue was then verified empty and automatic continuation
was paused. On 27 September the user approved continuation with **one job at a
time**, counting every submitted job on the account, not just running jobs.
Job **39247.mgmt01** was submitted at 02:59:34 UTC for the missing FashionMNIST
unknown-patch seed 2003 and completed with exit 0 and validated records.
Jobs 39266.mgmt01, 39286.mgmt01 and 39366.mgmt01 (all three distributed-backdoor
seeds), plus 39367.mgmt01, 39385.mgmt01 and 39388.mgmt01 (optimized-trigger
seeds 2001--2003), also completed and passed validation. The final 14:59 UTC
checkpoint index contains 9/9 completed runs and zero errors. The last job
exited 0 with walltime 00:11:49. The account queue is empty, the hourly
follow-up is paused and no subsequent job was submitted. Optimized-trigger
seeds 2002 and 2003 retain adverse ASRs of 52.98% and 54.37%, respectively.
See the [complete panel review](TIERGUARD2_FASHIONMNIST_PANEL_REVIEW_2026-09-27.md)
before any further campaign. These are development results, not confirmation.
No batch, array or chained submission replaces the cancelled queue. The
[serial execution policy](TIERGUARD2_SERIAL_EXECUTION.md) limits the next
automatic steps to the now-completed FashionMNIST development panel. Its
completion stops submissions; no next campaign is launched automatically.

| Campaign | Source clone and commit | PBS job IDs | Purpose |
| --- | --- | --- | --- |
| FashionMNIST clean, 3 seeds × (FedAvg + 2 clipping candidates) | `project_dev_attested`, `950d8a7f6f27622ceaabdec1d64cea881c636d4e` | 38557--38565 | Completed; nine-run index passed. Calibration JSON and index SHA-256 values are in `docs/TIERGUARD2_CLEAN_CALIBRATION_2026-09-24.md`. |
| FedAvg attack validity, 3 datasets × 3 attacks × 3 seeds | `project_attack_dev`, `aba8ac7b135ac342597a76bd25353c906a40eddc` | FashionMNIST 38567--38575; MNIST 38579--38587; CIFAR-10 38588--38596 | FashionMNIST and MNIST 9/9 each validated. CIFAR-10 9/9 finished but the index rejected three non-finite optimized-trigger runs; all nine CIFAR runs have low clean accuracy. The raw evidence is retained, not treated as valid. |
| MNIST and CIFAR-10 clean, 2 datasets × 3 seeds × (FedAvg + 2 clipping candidates) | `project_clean_dev_more`, `9f396ccd2a71de79967729eaa71e3d1759420755` | MNIST 38602--38610; CIFAR-10 38611--38619 | All 18 completed and passed separate nine-run indices. Both levels calibrated on each dataset; thresholds remain development candidates. |
| TierGuard 2 FashionMNIST attack development, three attacks × three seeds at clip 8 | `project_t2_attack_dev`, `897b419efa8c47774efd8ed14c41e020ad4df31e` | 38622--38630; serial resume 39247, 39266, 39286, 39366, 39367, 39385, 39388 | All nine cells completed and validated; final index has zero errors. Seven original queued jobs were cancelled and their cells later ran serially. Automatic submissions stopped. The original 56-run archive excludes the new serial results; the separate completed-panel package includes all nine and their paired baseline/calibration context. |
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
