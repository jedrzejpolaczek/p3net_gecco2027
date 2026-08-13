"""
Concrete StoppingRule implementations for this paper's experiment,
satisfying the p3net.harness.runner.StoppingRule protocol.

TODO:
- Implement the exploration-collapse criterion this paper's stopping rule
  needs on top of plain budget exhaustion, analogous to the one
  bartnik2026evolutionary needed for NAS-Bench-201-scale spaces (small
  search spaces can converge/exhaust diversity before the evaluation
  budget runs out).
- Compose it with p3net.harness.runner's default budget-exhaustion
  StoppingRule (stop on budget exhaustion OR exploration collapse), rather
  than reimplementing budget tracking here.
- Wire the concrete rule into experiments/scripts/run_experiment.py and
  experiments/scripts/run_grid.py via
  experiments/configs/experiment/budgets.yaml.

Reference: chapters/v003/results/main.tex ("Budgets, seeds, stopping" --
"a stopping rule covering both the evaluation budget and... an exploration
collapse criterion"). Generic interface this implements:
src/p3net/harness/runner.py (StoppingRule protocol).
"""
