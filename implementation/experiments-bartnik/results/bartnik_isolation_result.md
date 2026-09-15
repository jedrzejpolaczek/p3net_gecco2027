# Bartnik-algorithm-class isolation experiment: bartnik_p3 vs. the p3net baseline set

Architecture-only NAS-Bench-201 (no Theta), testing the reconstruction of Bartnik's own winning algorithm class (bartnik2026evolutionary) against exactly the baseline set p3net itself is compared against, plus p3net as a direct engine-vs-engine reference point (conclusions/main.tex, "Why the results are what they are").

| Budget | Baseline | n | Median bartnik_p3 | Median baseline | Adj. p | Cliff's delta | Reject H0 |
|---|---|---|---|---|---|---|---|
| 100 | random_search | 30 | 0.9856 | 0.9857 | 1.0000 | +0.113 | False |
| 100 | sh_emoa | 30 | 0.9856 | 0.9892 | 0.3052 | -0.338 | False |
| 100 | tpe | 30 | 0.9856 | 0.9890 | 0.0863 | -0.382 | False |
| 100 | mo_bohb | 30 | 0.9856 | 0.9842 | 1.0000 | +0.238 | False |
| 100 | nsga_net | 30 | 0.9856 | 0.9859 | 1.0000 | +0.060 | False |
| 100 | nsganetv2 | 30 | 0.9856 | 0.9801 | 0.0451 | +0.433 | True |
| 100 | p3_alone | 30 | 0.9856 | 0.9804 | 0.0016 | +0.518 | True |
| 100 | p3_absolute | 30 | 0.9856 | 0.9848 | 1.0000 | +0.036 | False |
| 100 | p3net | 30 | 0.9856 | 0.9851 | 1.0000 | +0.124 | False |
| 350 | random_search | 30 | 0.9935 | 0.9918 | 0.5333 | +0.273 | False |
| 350 | sh_emoa | 30 | 0.9935 | 0.9972 | 0.0000 | -0.793 | True |
| 350 | tpe | 30 | 0.9935 | 0.9952 | 0.3272 | -0.362 | False |
| 350 | mo_bohb | 30 | 0.9935 | 0.9910 | 0.1045 | +0.460 | False |
| 350 | nsga_net | 30 | 0.9935 | 0.9976 | 0.0001 | -0.800 | True |
| 350 | nsganetv2 | 30 | 0.9935 | 0.9890 | 0.0219 | +0.467 | True |
| 350 | p3_alone | 30 | 0.9935 | 0.9939 | 0.4042 | -0.220 | False |
| 350 | p3_absolute | 30 | 0.9935 | 0.9921 | 1.0000 | +0.193 | False |
| 350 | p3net | 30 | 0.9935 | 0.9923 | 0.9820 | +0.222 | False |
