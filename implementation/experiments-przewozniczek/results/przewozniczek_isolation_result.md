# P3-eLyMPuS isolation experiment: przewozniczek_p3elympus vs. the p3net baseline set

Architecture-only NAS-Bench-201 (no Theta), testing this project's own k-ary generalisation of P3-eLyMPuS (przewozniczek2026lympus) against exactly the baseline set p3net itself is compared against, plus p3net as a direct engine-vs-engine reference point (conclusions/main.tex, "Why the results are what they are").

| Budget | Baseline | n | Median przewozniczek_p3elympus | Median baseline | Adj. p | Cliff's delta | Reject H0 |
|---|---|---|---|---|---|---|---|
| 100 | random_search | 30 | 0.9854 | 0.9857 | 1.0000 | -0.004 | False |
| 100 | sh_emoa | 30 | 0.9854 | 0.9892 | 0.0651 | -0.469 | False |
| 100 | tpe | 30 | 0.9854 | 0.9890 | 0.0049 | -0.511 | True |
| 100 | mo_bohb | 30 | 0.9854 | 0.9842 | 1.0000 | +0.111 | False |
| 100 | nsga_net | 30 | 0.9854 | 0.9859 | 1.0000 | -0.042 | False |
| 100 | nsganetv2 | 30 | 0.9854 | 0.9801 | 0.0256 | +0.347 | True |
| 100 | p3_alone | 30 | 0.9854 | 0.9804 | 0.0061 | +0.433 | True |
| 100 | p3_absolute | 30 | 0.9854 | 0.9848 | 1.0000 | -0.107 | False |
| 100 | p3net | 30 | 0.9854 | 0.9851 | 1.0000 | -0.033 | False |
| 350 | random_search | 30 | 0.9962 | 0.9918 | 0.0001 | +0.691 | True |
| 350 | sh_emoa | 30 | 0.9962 | 0.9972 | 0.0484 | -0.482 | True |
| 350 | tpe | 30 | 0.9962 | 0.9952 | 1.0000 | +0.162 | False |
| 350 | mo_bohb | 30 | 0.9962 | 0.9910 | 0.0000 | +0.813 | True |
| 350 | nsga_net | 30 | 0.9962 | 0.9976 | 0.0160 | -0.529 | True |
| 350 | nsganetv2 | 30 | 0.9962 | 0.9890 | 0.0000 | +0.716 | True |
| 350 | p3_alone | 30 | 0.9962 | 0.9939 | 0.6156 | +0.280 | False |
| 350 | p3_absolute | 30 | 0.9962 | 0.9921 | 0.0014 | +0.649 | True |
| 350 | p3net | 30 | 0.9962 | 0.9923 | 0.0000 | +0.707 | True |
