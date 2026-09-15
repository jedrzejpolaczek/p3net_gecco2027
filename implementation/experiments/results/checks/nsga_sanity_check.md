# NSGA-Net vs. optuna NSGA-II sanity check

n=20, alphabet {0,1,2}, budget 1000 unique evaluations, 10 seeds. Hypervolume normalised by the exact front's. Criterion fixed before the first run: NSGA-Net median within 5% of optuna NSGA-II, both above random search.

| Problem | NSGA-Net median | optuna NSGA-II median | Relative gap | MWU p | Random search median | Criterion met |
|---|---|---|---|---|---|---|
| linear | 0.9567 | 0.9481 | +0.91% | 0.595 | 0.7100 | yes |
| lotz | 0.6861 | 0.7165 | -4.23% | 0.208 | 0.1255 | yes |

Overall: criterion met
