"""
Statistical comparison: paired Wilcoxon signed-rank + Holm-Bonferroni +
effect size.

TODO:
- Implement paired Wilcoxon signed-rank tests, one per comparison in the
  defined comparison set: P3Net (p3net.methods.p3net) vs. each of the other
  nine arms, per benchmark and per budget tier -- NOT every pairwise
  combination among all arms/baselines.
- Apply Holm-Bonferroni correction across exactly that comparison set (the
  correction count depends on this scope being right).
- Report an effect size (e.g. Cliff's delta) alongside every corrected
  p-value -- required for every comparison, not optional.
- This is intentionally stricter than bartnik2026evolutionary's
  uncorrected comparisons with no effect size -- preserve that as a
  deliberate methodological choice, not something to "simplify away".

Reference: chapters/v003/results/main.tex ("Statistical plan");
chapters/v003/notes/main.tex ("Comparison set for correction").
"""
