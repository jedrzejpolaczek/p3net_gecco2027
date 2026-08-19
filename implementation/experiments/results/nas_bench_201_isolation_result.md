# NAS-Bench-201 isolation experiment: p3net vs random_search

Architecture-only NAS-Bench-201 (no Theta), testing whether removing this project's own joint architecture+hyperparameter genotype extension lets P3Net separate from random_search where it does not on the two joint benchmarks (conclusions/main.tex, "Why the results are what they are").

| Budget | n | Median p3net | Median random_search | Adj. p | Cliff's delta | Reject H0 |
|---|---|---|---|---|---|---|
| 100 | 30 | 0.9851 | 0.9857 | 0.9515 | +0.016 | False |
| 350 | 30 | 0.9923 | 0.9918 | 0.7415 | +0.118 | False |
