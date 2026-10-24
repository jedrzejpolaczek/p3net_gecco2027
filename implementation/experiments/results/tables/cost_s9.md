# v004 cost (s9_timing: budget 350, one run per arm and space, sequential)

| Arm | Wall s (median) | Optimiser s (median) | Peak RSS MB (max) | Bridge RSS MB (max) | Slowest space | Note |
|---|---|---|---|---|---|---|
| oss_vizier | 9268 | 9250 | 30600 | n/r | jahs_bench_201_fashion (12037 s) | quality grid only at budgets 50/100 (~30 GB per run at 350; does not fit beside other workers) |
| botorch_qnehvi | 5410 | 5401 | 16343 | n/r | jahs_bench_201_fashion (7612 s) | quality grid only at budgets 50/100 (8419 s per run at 350; serialised GPU slot) |
| botorch_qparego | 3442 | 3425 | 12045 | n/r | jahs_bench_201 (5676 s) | quality grid only at budgets 50/100 (3192 s per run at 350; serialised GPU slot) |
| canonical_p3_scalar_fihc | 1205 | 1187 | 1560 | n/r | jahs_bench_201 (1232 s) |  |
| bartnik_p3 | 1143 | 1122 | 1559 | n/r | jahs_bench_201 (1311 s) |  |
| przewozniczek_p3elympus | 1097 | 1080 | 1560 | n/r | jahs_bench_201 (1266 s) |  |
| p3net_bartnik_fihc | 613 | 609 | 1562 | n/r | jahs_bench_201 (856 s) |  |
| p3net_elympus | 469 | 465 | 1560 | n/r | jahs_bench_201 (540 s) |  |
| asha_mo | 421 | 58 | 1553 | n/r | jahs_bench_201_colorectal (472 s) |  |
| p3net_bartnik | 355 | 347 | 1560 | n/r | jahs_bench_201 (392 s) |  |
| smac3_parego | 247 | 235 | 1728 | n/r | nas_hpo_bench_ii (248 s) |  |
| bohb_mo | 231 | 66 | 1553 | n/r | jahs_bench_201_fashion (241 s) |  |
| hyperband_mo | 164 | 0 | 1552 | n/r | jahs_bench_201_fashion (174 s) |  |
| p3net_cascade | 154 | 150 | 1801 | n/r | jahs_bench_201_fashion (186 s) |  |
| p3net | 139 | 80 | 1732 | n/r | jahs_bench_201_fashion (150 s) |  |
| bananas_mo | 118 | 103 | 1553 | n/r | jahs_bench_201 (127 s) |  |
| p3_absolute_cascade | 99 | 94 | 1557 | n/r | jahs_bench_201_colorectal (128 s) |  |
| p3_alone | 82 | 75 | 1553 | n/r | jahs_bench_201_fashion (132 s) |  |
| p3_alone_pop20 | 24 | 18 | 1553 | n/r | jahs_bench_201 (36 s) |  |
| tpe | 21 | 11 | 1555 | n/r | jahs_bench_201_fashion (24 s) |  |
| moead | 16 | 6 | 1557 | n/r | jahs_bench_201_fashion (72 s) |  |
| mo_bohb | 16 | 6 | 1552 | n/r | jahs_bench_201_colorectal (17 s) |  |
| p3_alone_pop40 | 13 | 3 | 1552 | n/r | jahs_bench_201_colorectal (13 s) |  |
| p3_absolute | 10 | 1 | 1554 | n/r | jahs_bench_201 (11 s) |  |
| sh_emoa | 10 | 1 | 1551 | n/r | jahs_bench_201 (10 s) |  |
| nsga3 | 10 | 1 | 1554 | n/r | jahs_bench_201 (10 s) |  |
| nsganetv2 | 9 | 0 | 1552 | n/r | jahs_bench_201_fashion (9 s) |  |
| mo_ls | 9 | 0 | 1551 | n/r | jahs_bench_201_fashion (9 s) |  |
| random_search | 9 | 0 | 1551 | n/r | jahs_bench_201_fashion (10 s) |  |
| reinforce_mo | 9 | 0 | 1552 | n/r | jahs_bench_201_fashion (9 s) |  |
| regularized_evolution_mo | 9 | 0 | 1552 | n/r | jahs_bench_201_colorectal (9 s) |  |
| nsga_net | 9 | 0 | 1551 | n/r | jahs_bench_201_colorectal (9 s) |  |

Arms with a note have measured costs here but **no quality results at budgets 200 and 350** (the Holm family of those cells is smaller by these arms).
