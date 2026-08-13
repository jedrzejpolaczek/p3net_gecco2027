"""
P3 + absolute regressor surrogate (surrogate-only ablation, isolating
linkage-aware design from the P3 engine itself).

TODO:
- Reuse p3net.search_engines.p3 (library import) unmodified; replace
  delta_hat_F (p3net.surrogates.relative_linkage_aware) with
  p3net.surrogates.absolute_regressor, in the NSGANetV2 style (regress f1
  directly from the full encoding).
- Otherwise keep the search loop identical to p3net.methods.p3net (chain
  depth handling, dedup cache, constraint handling) so the ONLY difference
  from P3Net is the surrogate.
- Note the acceptance rule needs rework here: an absolute regressor
  predicts f1(x') directly, not a relative delta -- decide and document how
  step-3 acceptance is computed from an absolute prediction (e.g. compare
  against parent's known f1), since the library's default zero-threshold
  rule in p3net.methods.p3net is phrased for delta_hat_F specifically.

Reference: chapters/v003/results/main.tex ("Baselines" -- "P3 with an
absolute regressor surrogate (in the style of NSGANetV2)...").
"""
