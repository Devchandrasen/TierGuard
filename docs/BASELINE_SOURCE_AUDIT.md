# Source audit of the proposed two-tier baselines

This note compares our implementations with the authors' published methods.
It defines what the manuscript may call each comparator; it does **not**
validate empirical performance. HFLMND has a separate derivation note.

## FLAME

[Nguyen et al., USENIX Security 2022, Algorithm 1](https://www.usenix.org/system/files/sec22fall_nguyen.pdf)
specifies cosine-distance clustering of local **model vectors**, a median
bound on update norms, equal averaging of admitted clipped models, and
Gaussian noise with standard deviation `lambda × median norm`. The paper
reports an image-classification noise factor of 0.001 and explains that
the noise factor must be tuned for the setting. Our
`HierarchicalFlameAggregator` implements that sequence independently at
each edge and again at the cloud; `noise_multiplier` is this factor.

The published method has one flat server. Our two-tier repetition, use of
scikit-learn HDBSCAN, deterministic replay seed for receipt challenges, and
"retain all" fallback when a small edge yields no stable cluster are
adaptation choices. On five-client edge groups, the clustering fallback may
matter often and must be counted in results. We cannot transfer FLAME's
flat-server results or theoretical interpretation to this adaptation.

## FedGame

The [NeurIPS 2023 paper](https://proceedings.neurips.cc/paper_files/paper/2023/file/a6678e2be4ce7aef9d2192e03cd586b7-Paper-Conference.pdf)
and [authors' code, commit `6be7b9e`](https://github.com/AI-secure/FedGame/tree/6be7b9e3f9e3a1aa1822fa8b319ec85c6ec27d52)
build an auxiliary model from mean updates, reconstruct a trigger/mask for
each target class, select the smallest mask, compute each local model's
genuine score as one minus target-class attack success on the reconstructed
trigger, and normalize those scores for aggregation. Our
`HierarchicalFedGameAggregator` retains this defender-side sequence.

Important differences are fixed explicitly before confirmation: the
authors' MNIST configuration uses a clean set equal to 10% of the training
data and 100 reconstruction epochs; their code optimizes over batches with
`tanh`-mapped trigger/mask variables and early stopping. Our adaptation
uses a bounded root batch, a configurable finite reconstruction step
budget, sigmoid-mapped variables, and reconstruction at each edge and cloud
level. It does **not** reproduce the full strategic attacker--defender game
or the authors' flat-server execution. Therefore the correct label in
tables is **"FedGame-derived, bounded two-tier adaptation"**, never an
author-code-identical FedGame run. The reconstruction budget and root-item
count require prespecified development tuning, and runtime must be reported.

These distinctions are not minor implementation details. A weak bounded
reconstruction could make this comparator look worse than the published
method. Any manuscript must state this limitation alongside the results,
and a superiority claim should not depend solely on outperforming this
adaptation.
