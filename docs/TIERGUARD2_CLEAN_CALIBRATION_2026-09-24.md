# TierGuard 2 clean-only calibration (development, not confirmation)

The three source-attested FashionMNIST clean development seeds (2001--2003)
ran for 40 rounds with 30 selected clients and six active edges per round.
The source commit was `950d8a7f6f27622ceaabdec1d64cea881c636d4e` and the test set
contained all 10,000 images. Each clipping candidate yielded 3,600 client
and 720 edge audit scores. The provisional threshold was 1.0, so these
clean runs applied no risk downweighting.

The pooled 95th-percentile held-out target-gain threshold was 0.3399 for
clip multiplier 8 and 0.3671 for clip multiplier 16. However, the two
hierarchy levels had visibly different clean score distributions:

| Clip multiplier | Client 95th percentile | Edge 95th percentile |
| ---: | ---: | ---: |
| 8 | 0.3590 | 0.2150 |
| 16 | 0.3827 | 0.2349 |

These are empirical quantiles of overlapping, temporally dependent audit
events, **not** per-event false-positive guarantees. Pooling clients and
edges would privilege the more numerous client scores (5:1) and set a
much higher-than-edge-specific cutoff at the cloud. Before any
confirmatory run, the method therefore uses separate frozen 95th-percentile
thresholds at the client and edge levels. The same clean-only calibration
rule must be applied on MNIST and CIFAR-10 development runs. The legacy
single threshold remains a provisional fallback for smoke/pilot configs;
it is not the intended confirmatory configuration.

Neither the clipping candidate nor the risk weight is selected from these
quantiles alone. Clean utility must be compared with matched FedAvg on
all three development seeds, and attack-side parameter selection must
follow the declared development grid and baseline budget. No positive
superiority conclusion follows from these clean runs.
