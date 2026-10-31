| method | wall b=100 median [s] | wall b=350 median / max [s] | k | peak RSS max [MB] | bridge RSS max [MB] | level 4 | grid worker-hours |
|---|---|---|---|---|---|---|---|
| v005_asha | 9 | 198 / 2235 | 2.41 | 12478 | 0 | OK | 67 |
| v005_hyperband | 0 | 4 / 272 | 1.60 | 15396 | 0 | OK | 13 |
| v005_mo_bohb | 1 | 32 / 71 | 2.41 | 12478 | 0 | OK | 4 |
| v005_mo_dsa | 300 | 869 / 1137 | 0.17 | 12478 | 0 | OK | 144 |
| v005_mo_ls | 0 | 0 / 15 | 2.41 | 12478 | 0 | OK | 0 |
| v005_mo_psa | 14 | 55 / 63 | 1.05 | 12478 | 0 | OK | 57 |
| v005_mobananas | 1 | 14 / 32 | 2.13 | 12478 | 0 | OK | 2 |
| v005_moead | 0 | 0 / 16 | 2.02 | 12478 | 0 | OK | 0 |
| v005_mosh_bananas | 1 | 3 / 61 | 1.38 | 12478 | 0 | OK | 2 |
| v005_motpe | 1 | 8 / 34 | 1.57 | 12478 | 0 | OK | 2 |
| v005_nsga3 | 0 | 0 / 16 | 1.39 | 12478 | 0 | OK | 1 |
| v005_nsga_net | 0 | 0 / 15 | 1.31 | 12478 | 0 | OK | 0 |
| v005_nsganetv2 | 637 | 2681 / 3028 | 1.16 | 12478 | 0 | OK | 332 |
| v005_p3_canonical | 0 | 0 / 16 | 1.81 | 12478 | 0 | OK | 1 |
| v005_p3_elympus | 0 | 0 / 11 | 1.42 | 12478 | 0 | OK | 0 |
| v005_p3net | 2 | 15 / 97 | 1.73 | 12478 | 0 | FAIL | 5 |
| v005_p3net_gate | 1 | 11 / 23 | 2.23 | 12478 | 0 | OK | 1 |
| v005_p3net_nolink | 1 | 3 / 14 | 1.36 | 12478 | 0 | FAIL | 0 |
| v005_qnehvi | 137 | 6130 / 7188 | 3.03 | 15396 | 0 | OK | 514 |
| v005_qparego | 54 | 2452 / 3545 | 2.80 | 12478 | 0 | OK | 201 |
| v005_random_search | 0 | 0 / 16 | 2.62 | 12478 | 0 | OK | 0 |
| v005_regevo | 0 | 0 / 16 | 1.50 | 12478 | 0 | OK | 0 |
| v005_reinforce | 4 | 4 / 12 | 0.08 | 12478 | 0 | OK | 2 |
| v005_shemoa | 0 | 0 / 14 | 1.36 | 12478 | 0 | OK | 0 |
| v005_shemoa_mf | 0 | 1 / 71 | 1.25 | 12478 | 0 | OK | 3 |
| v005_smac3_parego | 36 | 223 / 249 | 1.41 | 12478 | 0 | OK | 25 |
| v005_vizier | 1153 | 7769 / 9511 | 1.52 | 30478 | 0 | OK | 531 |

Grid `v005.yaml`: **1910 worker-hours**, i.e. 13.3 days at 6 workers (one machine).

Not projected (missing measurements): [('v005_mo_dsa', 'nas_bench_201_v005'), ('v005_mo_ls', 'nas_bench_201_v005'), ('v005_mo_psa', 'nas_bench_201_v005'), ('v005_mobananas', 'nas_bench_201_v005'), ('v005_moead', 'nas_bench_201_v005'), ('v005_motpe', 'nas_bench_201_v005'), ('v005_nsga3', 'nas_bench_201_v005'), ('v005_nsga_net', 'nas_bench_201_v005'), ('v005_nsganetv2', 'nas_bench_201_v005'), ('v005_p3_canonical', 'nas_bench_201_v005'), ('v005_p3_elympus', 'nas_bench_201_v005'), ('v005_p3net', 'nas_bench_201_v005'), ('v005_p3net_gate', 'nas_bench_201_v005'), ('v005_p3net_nolink', 'nas_bench_201_v005'), ('v005_qnehvi', 'nas_bench_201_v005'), ('v005_qparego', 'nas_bench_201_v005'), ('v005_random_search', 'nas_bench_201_v005'), ('v005_regevo', 'nas_bench_201_v005'), ('v005_reinforce', 'nas_bench_201_v005'), ('v005_shemoa', 'nas_bench_201_v005')]