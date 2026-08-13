"""
JAHS-Bench-201 adapter (primary benchmark, Category 2: continuous surrogate,
no enumerable oracle front).

TODO:
- Wrap the JAHS-Bench-201 Python API/package as the query substrate.
- Encode its joint search space: six categorical architecture edges + four
  hyperparameters (learning rate, weight decay, activation function, data
  augmentation) = ten search dimensions; four further fidelity dimensions
  (epochs, resolution, ...) tracked separately, not part of the searched
  genotype. Use experiments/search_spaces/nas_genotype.py for the genotype
  itself -- this module only needs to translate it to/from JAHS-Bench-201's
  own query format.
- Fix r_K's resolution setting once, and hold f2 constant at that setting
  regardless of the fidelity level f1 is queried at.
- Confirm/implement across the three JAHS-Bench-201 datasets it defines.
- No enumerable oracle front exists for this benchmark -- do not implement
  IGD+ here; p3net.metrics.hypervolume's best-known-front fallback applies
  instead (aggregation logic in experiments/reporting/).

Reference: chapters/v003/results/main.tex ("Benchmark and search space");
chapters/v003/related_work/main.tex (Category 1 vs Category 2 discussion).
"""
