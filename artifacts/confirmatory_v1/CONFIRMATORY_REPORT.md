# TierGuard confirmatory-v1 report

Validation: **PASS** (180/180 runs).

The protocol uses six paired held-out seeds. All methods share the same hierarchy, client sampling, data partitions, local training, root set, rounds, and attack configuration. Exact two-sided paired sign-flip permutation tests are Holm-adjusted within each dataset × attack × metric family. Results are not promoted beyond this simulation scope.

## Means and 95% t intervals

| Dataset | Attack | Method | Clean accuracy | Attack success rate |
|---|---|---|---:|---:|
| digits | adaptive_tierguard_aware | hfl_fedavg | 0.8817 [0.8252, 0.9381] | 0.0842 [-0.0401, 0.2086] |
| digits | adaptive_tierguard_aware | hfl_fltrust | 0.6639 [0.5771, 0.7506] | 0.1029 [-0.0319, 0.2377] |
| digits | adaptive_tierguard_aware | hfl_rfa | 0.8378 [0.7822, 0.8933] | 0.0197 [0.0028, 0.0365] |
| digits | adaptive_tierguard_aware | hfl_trimmed_mean | 0.8344 [0.7785, 0.8904] | 0.0503 [-0.0070, 0.1077] |
| digits | adaptive_tierguard_aware | tierguard | 0.8678 [0.8350, 0.9006] | 0.0132 [0.0003, 0.0261] |
| digits | backdoor_model_replacement | hfl_fedavg | 0.4889 [0.2369, 0.7409] | 0.7870 [0.4561, 1.1179] |
| digits | backdoor_model_replacement | hfl_fltrust | 0.6528 [0.4048, 0.9008] | 0.0387 [-0.0213, 0.0987] |
| digits | backdoor_model_replacement | hfl_rfa | 0.7722 [0.6614, 0.8831] | 0.0332 [-0.0158, 0.0822] |
| digits | backdoor_model_replacement | hfl_trimmed_mean | 0.3267 [0.0463, 0.6070] | 0.8257 [0.5453, 1.1061] |
| digits | backdoor_model_replacement | tierguard | 0.8617 [0.8320, 0.8913] | 0.0363 [-0.0123, 0.0849] |
| fashionmnist | adaptive_tierguard_aware | hfl_fedavg | 0.7747 [0.7429, 0.8064] | 0.8851 [0.7380, 1.0322] |
| fashionmnist | adaptive_tierguard_aware | hfl_fltrust | 0.7655 [0.7397, 0.7913] | 0.8894 [0.7720, 1.0067] |
| fashionmnist | adaptive_tierguard_aware | hfl_rfa | 0.7488 [0.6949, 0.8028] | 0.8033 [0.4681, 1.1385] |
| fashionmnist | adaptive_tierguard_aware | hfl_trimmed_mean | 0.7707 [0.7452, 0.7961] | 0.8000 [0.6764, 0.9236] |
| fashionmnist | adaptive_tierguard_aware | tierguard | 0.7575 [0.7234, 0.7916] | 0.3290 [0.0295, 0.6284] |
| fashionmnist | backdoor_model_replacement | hfl_fedavg | 0.6418 [0.5588, 0.7248] | 0.9916 [0.9838, 0.9995] |
| fashionmnist | backdoor_model_replacement | hfl_fltrust | 0.7432 [0.7248, 0.7615] | 0.0539 [-0.0017, 0.1094] |
| fashionmnist | backdoor_model_replacement | hfl_rfa | 0.7173 [0.6740, 0.7606] | 0.8589 [0.6048, 1.1129] |
| fashionmnist | backdoor_model_replacement | hfl_trimmed_mean | 0.6812 [0.5833, 0.7790] | 0.9844 [0.9651, 1.0038] |
| fashionmnist | backdoor_model_replacement | tierguard | 0.7515 [0.7213, 0.7817] | 0.1113 [0.0137, 0.2088] |
| mnist | adaptive_tierguard_aware | hfl_fedavg | 0.9443 [0.9377, 0.9510] | 0.8882 [0.6735, 1.1028] |
| mnist | adaptive_tierguard_aware | hfl_fltrust | 0.9242 [0.9095, 0.9389] | 0.9956 [0.9885, 1.0026] |
| mnist | adaptive_tierguard_aware | hfl_rfa | 0.9312 [0.9096, 0.9527] | 0.8169 [0.4800, 1.1537] |
| mnist | adaptive_tierguard_aware | hfl_trimmed_mean | 0.9362 [0.9281, 0.9442] | 0.8303 [0.6547, 1.0059] |
| mnist | adaptive_tierguard_aware | tierguard | 0.9338 [0.9232, 0.9445] | 0.2982 [-0.0253, 0.6218] |
| mnist | backdoor_model_replacement | hfl_fedavg | 0.8755 [0.8194, 0.9316] | 0.9865 [0.9568, 1.0162] |
| mnist | backdoor_model_replacement | hfl_fltrust | 0.9225 [0.9114, 0.9336] | 0.3554 [0.0680, 0.6428] |
| mnist | backdoor_model_replacement | hfl_rfa | 0.9227 [0.9015, 0.9438] | 0.9033 [0.6946, 1.1121] |
| mnist | backdoor_model_replacement | hfl_trimmed_mean | 0.9037 [0.8586, 0.9488] | 0.9970 [0.9946, 0.9994] |
| mnist | backdoor_model_replacement | tierguard | 0.9313 [0.9208, 0.9419] | 0.3655 [0.0560, 0.6750] |

## Paired inference

Full pre-specified comparisons are in `paired_comparisons.csv`. A Holm rejection is reported only when the adjusted p-value is below 0.05; no post-hoc best-baseline selection is used.

Holm-adjusted rejections: 0/72.
