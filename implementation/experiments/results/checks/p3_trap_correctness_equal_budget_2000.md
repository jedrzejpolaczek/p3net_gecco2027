# P3 correctness on concatenated deceptive k-ary traps

m=5 blocks, k=4, alphabet {0,1,2}, n=20, variables interleaved (permutation seed 12345); optimum score 20, score of the all-deceptive local optimum 16.25.
SUPPLEMENTARY equal-budget run (budget 2000, matching the P3Net diagnostic arms). The pre-registered criteria apply only to the 50000-evaluation run in p3_trap_correctness.md; the criterion column here is not applicable.

| Arm | Budget | Pre-registered criterion | Optimum found | Median evals to optimum | Median best score | Wall-clock s |
|---|---|---|---|---|---|---|
| p3_canonical | 2000 | >= 8/10 | 0/10 | -- | 17.75 | 83 |
| random_search | 2000 | <= 1/10 | 0/10 | -- | 16.38 | 0 |
| fihc_restarts | 2000 | <= 1/10 | 0/10 | -- | 17.56 | 0 |
