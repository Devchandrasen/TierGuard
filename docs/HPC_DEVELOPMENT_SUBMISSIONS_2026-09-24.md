# TierGuard 2 HPC development submissions

These are **development** jobs, never the 12 prespecified confirmatory seeds.
The isolated HPC environment is
`/home/chandrasen.pandey/tierguard2_env_2026_09_23` on `arc-hpc`.
Datasets are pinned by its `datasets_manifest_2026_09_24.json` (24 file
SHA-256 values). Each run records the resolved configuration, clean Git
commit, partition indices, per-round metrics and node provenance. The two
H100 nodes have different drivers and runtime characteristics, so concurrent
wall times are not an algorithmic efficiency comparison.

| Campaign | Source clone and commit | PBS job IDs | Purpose |
| --- | --- | --- | --- |
| FashionMNIST clean, 3 seeds × (FedAvg + 2 clipping candidates) | `project_dev_attested`, `950d8a7f6f27622ceaabdec1d64cea881c636d4e` | 38557--38565 | Completed; nine-run index passed. Calibration JSON and index SHA-256 values are in `docs/TIERGUARD2_CLEAN_CALIBRATION_2026-09-24.md`. |
| FedAvg attack validity, 3 datasets × 3 attacks × 3 seeds | `project_attack_dev`, `aba8ac7b135ac342597a76bd25353c906a40eddc` | FashionMNIST 38567--38575; MNIST 38579--38587; CIFAR-10 38588--38596 | FashionMNIST and MNIST 9/9 each validated. CIFAR-10 9/9 finished but the index rejected three non-finite optimized-trigger runs; all nine CIFAR runs have low clean accuracy. The raw evidence is retained, not treated as valid. |
| MNIST and CIFAR-10 clean, 2 datasets × 3 seeds × (FedAvg + 2 clipping candidates) | `project_clean_dev_more`, `9f396ccd2a71de79967729eaa71e3d1759420755` | MNIST 38602--38610; CIFAR-10 38611--38619 | MNIST 9/9 completed, indexed and independently calibrated at both levels; see `docs/TIERGUARD2_CLEAN_CALIBRATION_2026-09-24.md`. CIFAR-10 remains queued/running. |
| TierGuard 2 FashionMNIST attack development, three attacks × three seeds at clip 8 | `project_t2_attack_dev`, `897b419efa8c47774efd8ed14c41e020ad4df31e` | 38622--38630 | Submitted; candidate uses the independent clean-only thresholds 0.3590044573 (client) and 0.2149923056 (edge). It is not a selected final configuration. |
| CIFAR-10 clean learning-rate repair grid, 3 rates × 3 seeds | `project_cifar_lr_dev`, `aba8ac7b135ac342597a76bd25353c906a40eddc` | 38663--38671 | Submitted after the invalid CIFAR attack-validity panel. FedAvg only, no attack, rates 0.005/0.01/0.02. Exploratory development; compare with the pending 0.05 clean controls before selecting a stable common protocol. |
| TierGuard 2 MNIST attack development, three attacks × three seeds at clip 8 | `project_t2_mnist_dev`, `1b1dacb67d383e5642b61b3bb50099f2a2812414` | 38672--38680 | Submitted with the separate clean-only MNIST client/edge thresholds 0.2396139853 and 0.0718886655. This is one development candidate, not the final setting. |

The snapshots are separate: later repository commits must not be pulled into
any clone while its jobs run, or a run could mix source versions. The
FashionMNIST calibration script was copied to the dedicated environment
outside its training checkout and hash-checked before execution. A versioned
archive of raw run records is still required before manuscript preparation.
The CIFAR-10 clean-rate index was likewise copied outside the training clone;
its SHA-256 is
`5fc74c6b2c13df71d744f1516405904b1980151e51754fb95d032f3b2fe5d5a2`.
