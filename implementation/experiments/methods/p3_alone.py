"""
P3 alone (engine-only ablation, P3 side -- no surrogate).

TODO:
- Reuse p3net.search_engines.p3 (library import) unmodified, but replace
  every delta_hat_F acceptance check with a REAL evaluation of f1 (canonical
  optimal-mixing acceptance rule) -- every proposed modification within a
  sweep is gated by a genuine full evaluation, exactly as in the original P3
  hill-climbing / cross-level mixing steps.
- Expect and report budget exhaustion: under the {50, 100, 200}-evaluation
  budgets (experiments/configs/experiment/budgets.yaml), a single parent's
  full sweep alone can approach the smallest tier. Track and expose "number
  of full sweeps completed within budget" as a first-class diagnostic
  alongside hypervolume -- a weak result here must read as budget
  starvation, not engine failure.
- Still apply the shared deduplication cache (p3net.harness.evaluation_cache)
  and constraint handling (p3net.problem.decoding).

Reference: chapters/v003/results/main.tex ("Baselines" -- "Without a
surrogate, P3 alone follows the canonical optimal-mixing acceptance
rule..."); chapters/v003/notes/main.tex ("P3-without-surrogate budget
reality").
"""
