"""
NSGA-Net (engine-only ablation, NSGA-II side -- no surrogate, every
candidate fully trained/evaluated).

TODO:
- Implement plain NSGA-II (experiments.search_engines.nsga2) with every
  generated candidate fully evaluated via f1 -- no surrogate anywhere in the
  loop.
- This is the symmetric counterpart to experiments/methods/p3_alone.py;
  unlike P3 alone, standard NSGA-II is not expected to be budget-starved at
  generational population sizes, so do not silently import P3-alone's
  budget-exhaustion handling here.
- Apply the same shared deduplication cache (p3net.harness.evaluation_cache)
  and constraint handling as every other arm (Fairness controls).

Reference: chapters/v003/results/main.tex ("Baselines" -- "NSGA-Net
(NSGA-II with no surrogate, every candidate fully evaluated) as the
engine-only ablation on the NSGA-II side, symmetric to the P3-only
ablation below").
"""
