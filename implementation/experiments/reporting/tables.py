"""
Fixed-budget summary table (median, IQR, corrected p-values, effect sizes).

TODO:
- Generate, per benchmark and budget tier, the summary table across all
  nine baselines/ablations (Table tab:ablation-grid) plus the five extra
  baselines: median and IQR of the chosen metric (p3net.metrics.hypervolume,
  and p3net.metrics.igd_plus where applicable), corrected p-value and
  effect size from experiments/stats/significance.py.
- Also produce the "number of full sweeps completed within budget"
  side-table specific to the P3-alone ablation (experiments/methods/
  p3_alone.py).

Reference: chapters/v003/results/main.tex ("This section reports... a
fixed-budget summary table (median, IQR, corrected p values, effect
sizes)... Findings" TODO).
"""
