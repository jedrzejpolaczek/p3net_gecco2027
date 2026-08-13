"""
Sweep driver: full ablation grid (9 arms) + 5 extra baselines, both
benchmarks, all budget tiers, all seeds.

TODO:
- Enumerate every (method, benchmark, budget tier, seed) combination per
  experiments/configs/methods/*.yaml x
  experiments/configs/search_spaces/*.yaml x
  experiments/configs/experiment/budgets.yaml, and dispatch each to
  experiments/scripts/run_experiment.py (or the equivalent in-process
  call).
- Skip combinations already cached (p3net.harness.evaluation_cache) rather
  than re-running them.

Reference: chapters/v003/results/main.tex ("Baselines", Table
tab:ablation-grid, "Budgets, seeds, stopping").
"""
