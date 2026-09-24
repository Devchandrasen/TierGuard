# HFLMND comparator: paper-derived reconstruction, not author code

Source: Q. Bi et al., *Knowledge-Based Systems* 336 (2026) 115270,
https://doi.org/10.1016/j.knosys.2026.115270. The supplied 14-page PDF
(`1-s2.0-S0950705126000146-main.pdf`) has SHA-256
`bf00829fd4a280360a8658d40079db6c9dc0b023487c93064cf06c2847576660`.
The PDF is **not** redistributed in this repository.

`src/tierguard/aggregators/hflmnd_hierarchical.py` implements the following
published mechanism at both client-to-edge and edge-to-cloud aggregation:

| Paper element | Implementation |
| --- | --- |
| Eq. (4) | Per-model min-max normalization of the complete plaintext model vector. |
| Fig. 2; Eq. (5) | Dot product, cosine, and Euclidean distance between each subordinate model and its superior's current model. A client or edge *update* is converted back to its local model by adding the common superior model. |
| Eqs. (6)--(10) | Inverted min-max dot/distance, ReLU cosine, cosine-times-distance, and the four-dimensional feature vector in the paper's order. |
| Eqs. (12)--(14) | Euclidean feature distances, hierarchical clustering, and two current-status groups. |
| Eq. (15); Sec. 4.4 | Persistent per-node score, incremented for the suspected group and decremented for the benign group. Admission requires both current benign status and an updated score strictly below zero. |
| Algorithm 1, lines 15 and 22 | Equal arithmetic averaging of accepted client or edge models. With a common starting model, this equals equal averaging of their updates. The paper's rule does not use sample-mass weights. |

The paper does **not** specify its linkage criterion, how the two clusters
are assigned benign/malicious semantics, what to do with tied min-max values,
or what to aggregate if every node is excluded. The reconstruction fixes these
choices before development results are viewed: average linkage; larger cluster
is benign under the paper's less-than-50%-malicious premise, with a tie broken
by lower mean distance to the superior model; tied features are non-separating;
fewer than three nodes are not split into clusters; an all-rejected layer emits
a zero update. The zero-update rule freezes the
superior model rather than silently re-admitting rejected nodes. Each choice
is logged in run metadata. Author code, if supplied later, should supersede
these choices after an explicit review **before** confirmatory freezing.

The matched TierGuard 2 study has 60 clients, six edges, 40 global rounds,
two local epochs, and one edge aggregation per global round. Bi et al. report
100 clients, ten edges, and five edge iterations per global iteration, with
different dataset models and attacks (Sec. 5.1). This comparator therefore
tests the paper's *algorithmic mechanism in our common topology*, not a
reproduction of its published Table 4 or Table 5. The signed receipt/challenge
wrapper is supplied to all compared methods and is not an HFLMND component.
HFLMND itself operates on plaintext model parameters and does not provide a
client-update confidentiality guarantee (Sec. 6).

HFLMND already performs detection at both hierarchy levels. The TierGuard 2
novelty claim must therefore be about a verified complementary functional
counterfactual mechanism and authenticated challenge evidence, not simply
placing a detector at two levels. No such comparative outcome exists yet.
