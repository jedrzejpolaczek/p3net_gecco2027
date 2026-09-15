# P3 correctness on concatenated deceptive k-ary traps

m=5 blocks, k=4, alphabet {0,1,2}, n=20, variables interleaved (permutation seed 12345); optimum score 20, score of the all-deceptive local optimum 16.25.
Criteria were fixed before the first run (see scripts/p3_trap_correctness.py).

| Arm | Budget | Pre-registered criterion | Optimum found | Median evals to optimum | Median best score | Wall-clock s |
|---|---|---|---|---|---|---|
| p3_canonical | 50000 | >= 8/10 | 10/10 | 8968 | 20.00 | 571 |
| random_search | 50000 | <= 1/10 | 0/10 | -- | 16.78 | 4 |
| fihc_restarts | 50000 | <= 1/10 | 0/10 | -- | 17.75 | 2 |
| p3net_default | 2000 | diagnostic | 0/10 | -- | 15.72 | 239 |
| p3net_cascade | 2000 | diagnostic | 0/10 | -- | 16.09 | 6490 |
