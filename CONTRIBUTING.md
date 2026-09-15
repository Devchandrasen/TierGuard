# Contributing

Open an issue before changing the frozen confirmatory-v1 protocol. Bug fixes may
be merged normally, but any change to a file listed in
`configs/confirmatory_v1/FROZEN_SHA256SUMS` requires a new protocol identifier,
new manifest, and fresh confirmatory outputs. Do not combine results from
different protocol hashes.

Run before submitting a change:

```text
python -m ruff check src tests scripts/freeze_protocol.py scripts/run_confirmatory.py scripts/analyze_confirmatory.py
python -m pytest -q
python scripts/freeze_protocol.py
```
