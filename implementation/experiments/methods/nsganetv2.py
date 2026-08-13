"""
NSGANetV2 (primary baseline): NSGA-II + absolute regressor surrogate,
discretised Theta. Also covers the nsganetv2_continuous control variant
(native real-valued Theta).

TODO:
- Implement NSGA-II (experiments.search_engines.nsga2) paired with
  p3net.surrogates.absolute_regressor scoring full candidate encodings.
- Default configuration searches the SAME discretised Theta as P3Net
  (Fairness controls), via experiments/search_spaces/nas_genotype.py's
  shared discretised encoding -- do not let this arm silently use a
  continuous encoding by default.
- Support a second configuration
  (experiments/configs/methods/nsganetv2_continuous.yaml) using the
  unconstrained, real-valued encoding of Theta this baseline would natively
  use (the continuous variant defined in
  experiments/search_spaces/nas_genotype.py), as an additional control
  isolating the effect of discretisation itself -- implement as a
  config-driven variant of this same module, not a separate
  reimplementation, so the two configurations only differ in Theta's
  encoding.
- Apply identical dedup cache, seed policy, and stopping rule as every other
  arm.

Reference: chapters/v003/results/main.tex ("Baselines", "Fairness
controls"); chapters/v003/notes/main.tex ("Encoding in baselines").
"""
