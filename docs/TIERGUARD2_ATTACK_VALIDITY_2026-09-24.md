# TierGuard 2 attack-validity development panel

The FashionMNIST panel completed all nine prespecified 40-round runs:
three attacks × development seeds 2001--2003 against undefended
hierarchical FedAvg. Each run used the full 10,000-image test set,
60 clients, six edges, 30 selected clients per round, two local epochs,
20% malicious clients, a method-independent deterministic attack instance,
and source commit `aba8ac7b135ac342597a76bd25353c906a40eddc`.
The fail-closed index found no duplicate, incomplete, dirty-source,
partition-mismatch, or instance-hash error. The index SHA-256 is
`432c72da0b14510ee73391dd0cd71b43ce2497c2d146ec8bbe71bc0b9c61083d`;
the validator script SHA-256 is
`11ab43e8c32f6c950b90f311595da330394fb41d4ac8ce0c8b0b73a3168d2ae2`.

| Attack | Mean final ASR, 3 seeds | Lowest seed ASR | Mean final clean accuracy |
| --- | ---: | ---: | ---: |
| Unknown patch and model replacement | 0.9987 | 0.9961 | 0.7991 |
| Four-component distributed backdoor | 1.0000 | 1.0000 | 0.8187 |
| Attacker-local optimized trigger | 0.9919 | 0.9801 | 0.8163 |

The matched no-attack FedAvg clean-development mean was 0.8820. Thus these
attack conditions also reduce clean accuracy by roughly 0.06--0.08; they
must not be presented as clean-utility-preserving or stealthy without
qualification. The scaled distributed attack should be described as a
strong distributed model-poisoning/backdoor stress condition, not as a
replication of the published DBA attack or as evidence of stealth.

MNIST and CIFAR-10 attack-validity runs remain queued/running. TierGuard 2
attack-development runs have been submitted but have not yet produced a
validated full panel. No confirmatory seed or superiority analysis has run.
