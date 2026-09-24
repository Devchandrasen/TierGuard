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

The MNIST panel also completed 9/9 runs and passed the same validator with
no errors (index SHA-256
`c98d8c943bc0fd89d5b775d2a5c733021fbeeb62b17e8cd1da73e4625ee3fa8c`).

| MNIST attack | Mean final ASR, 3 seeds | Lowest seed ASR | Mean final clean accuracy |
| --- | ---: | ---: | ---: |
| Unknown patch and model replacement | 1.0000 | 1.0000 | 0.9829 |
| Four-component distributed backdoor | 1.0000 | 1.0000 | 0.9785 |
| Attacker-local optimized trigger | 0.99996 | 0.99989 | 0.9745 |

The CIFAR-10 attack-validity runs finished 9/9, but the fail-closed index
**rejected the panel**. All three optimized-trigger runs recorded non-finite
client updates (43--59 failures per run), and their round-two trigger records
contain NaNs. The other two attack conditions did not record non-finite
updates, but all nine attacked CIFAR-10 runs had very low final clean accuracy
(0.1235--0.2441). Their final ASR values therefore cannot establish a useful
backdoor challenge or defence efficacy. The rejected index is retained for
audit at SHA-256
`24dd56535daaac619b452833c333c29c601087ba9d1edd8528021177955bd365`.
The original raw runs are not altered or relabelled as valid. Three-seed
clean FedAvg learning-rate candidates (0.005, 0.01, 0.02) have been queued
separately; the pending original-rate clean controls will also be checked.
Only after a stable clean protocol is selected on development evidence can
the CIFAR-10 attack panel be rerun and validated. This is an exploratory
protocol repair before any confirmatory freeze, not a post hoc selection on
confirmatory results.

TierGuard 2 attack-development runs have been submitted but have not yet
produced a validated full panel. No confirmatory seed or superiority analysis
has run.
