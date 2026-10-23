# BM-3: JAHS `size_MB` vs hyperparameters (cifar10)

- cells: 200, HP combinations per cell: 10, seed 0, nepochs 200
- benchmark load time: 352 s
- cells whose `size_MB` spread >= 1e-06 MB: 200 / 200
- max spread: 0.278218 MB; median spread: 0.024786 MB
- max relative spread (spread / mean): 0.3361

**Verdict (rule fixed in benchmarks.md before the run): analytic parameter count (size_MB varies with HP).**

Raw data: `bm3_jahs_size_vs_hp_cifar10.json`.
