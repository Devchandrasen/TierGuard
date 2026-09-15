# TierGuard

TierGuard is a research implementation of trusted-edge robust aggregation for
hierarchical federated learning (HFL). It contains the frozen confirmatory-v1
protocol, matched two-level baselines, per-run provenance capture, and paired
statistical analysis used for the public software artifact.

## Scope and claim boundary

TierGuard inspects individual client updates in plaintext at trusted edge
aggregators. It is **not** a secure-aggregation or client-update-confidentiality
protocol. The files under `tierguard.security` are standalone communication and
secret-sharing simulators; the confirmatory protocol disables them. The released
results cover simulation experiments on MNIST, FashionMNIST, and scikit-learn
Digits under a predefined bottom-right-square trigger and target label 0. They do
not establish unknown-trigger detection, malicious-edge security, privacy,
collusion tolerance, or deployment-scale performance.

## Matched hierarchical comparison

Every method uses the same two-level client → edge → cloud route, seed, data
partition, selected clients, local training, root set, number of rounds, and
attack configuration:

- `hfl_fedavg`: weighted FedAvg at edges and cloud;
- `hfl_fltrust`: FLTrust at edges and cloud using the same clean root update;
- `hfl_trimmed_mean`: coordinate-wise trimmed mean at edges and cloud;
- `hfl_rfa`: weighted geometric median at edges and cloud;
- `tierguard`: TierGuard-PTA at edges and cloud, including the predefined-trigger audit.

The audit has its own data-loader generator. Client and reference-loader
generators are method-independent, so the audit cannot change another method's
batch order under a paired seed.

## Pinned environment

The reference run used Python 3.12.10 and the exact CUDA 12.8 package set in
`requirements-lock-cu128.txt`, while computation was forced to CPU for the
confirmatory campaign.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-lock-cu128.txt
python -m pip install -e . --no-deps
python -m pytest -q
python scripts\freeze_protocol.py
```

Linux uses the same commands with `source .venv/bin/activate` and forward
slashes.

## Frozen confirmatory run

The protocol was committed and tagged before any confirmatory result was run.
`configs/confirmatory_v1/FROZEN_SHA256SUMS` binds the implementation, tests,
matrix, dataset configs, runner, analysis, Python version, and dependency lock.
The six held-out paired seeds are 101, 202, 303, 404, 505, and 606.

```powershell
python scripts\freeze_protocol.py
python scripts\run_confirmatory.py --device cpu --workers 4 --torch-threads 1
python scripts\analyze_confirmatory.py
```

The run command refuses to start if a frozen file differs from the committed
manifest. Each run saves the resolved config, per-round metrics, final metrics,
command, and environment/git provenance. `scripts/analyze_confirmatory.py`
requires all 180 cells, one clean source commit, six paired seeds, zero duplicate
cells, and zero non-finite-update failures before it emits tables.

## Statistical analysis

For each method and condition, the artifact reports the mean, sample standard
deviation, and 95% t interval. TierGuard is compared with every pre-specified
baseline using a two-sided exact paired sign-flip permutation test and paired
Cohen's dz. P-values are Holm-adjusted within each dataset × attack × metric
family. There is no post-hoc best-baseline selection.

## Repository layout

- `configs/confirmatory_v1/`: frozen matrix, dataset configs, and checksums
- `src/tierguard/`: implementation
- `scripts/run_confirmatory.py`: resumable campaign runner
- `scripts/analyze_confirmatory.py`: validation and paired inference
- `artifacts/confirmatory_v1/`: validated aggregate results and report
- `tests/`: unit and protocol-invariant tests

Raw per-round outputs are distributed as a release asset because they are larger
than the review-friendly aggregate files kept in Git.

## Citation

Use the repository's “Cite this repository” control or the DOI listed on the
latest release. See `CITATION.cff` for author metadata.

## License

MIT. See `LICENSE`.
