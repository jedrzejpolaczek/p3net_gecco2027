"""
Concrete NAS search space: cell-graph architecture edges + discretised
training hyperparameters, implementing p3net.problem's generic
SearchSpace/Decoder/Validity interfaces.

This is the NAS-specific content that used to live directly in the
library's problem/genotype.py and problem/decoding.py before the
library/experiments split -- it now depends ON p3net.problem rather than
being part of it, exactly the way any other p3net user's problem
definition would.

TODO:
- Instantiate p3net.problem.SearchSpace as Lambda = Lambda_1 x ... x
  Lambda_n x Theta: the per-edge categorical operation sets
  Lambda_1..Lambda_n (cell-graph encoding), plus Theta (learning rate,
  weight decay, ...) discretised into a finite, fixed-once bin set (option
  (i) from the paper's Problem Formulation; e.g. a log-spaced grid for
  learning rate) -- so the whole joint genotype is categorical and can be
  handed unmodified to p3net.search_engines.p3.linkage_tree /
  optimal_mixing.
- Implement the concrete Decoder D: genotype -> a network description
  consumable by experiments/substrates/*.py.
- Implement the concrete Validity g: does an input-output path exist
  through the cell graph (boolean, expressed in the real-valued g(x) <= 0
  form p3net.problem.decoding defines).
- This is also where the two search-space variants used across the
  baselines live: the shared discretised Theta encoding (used identically
  by P3Net and every other arm, per Fairness controls) and, separately, the
  unconstrained real-valued Theta encoding NSGANetV2 would natively use
  (for the nsganetv2_continuous.yaml control baseline in
  experiments/methods/nsganetv2.py).

Reference: chapters/v003/problem_formulation/main.tex (Formal definition,
"Handling Theta's continuity in P3"); chapters/v003/proposed_optimizer/
main.tex ("Representation and linkage tree"); chapters/v003/notes/main.tex
("Problem representation", "Encoding in baselines"). Generic interfaces
this implements: ../lib/src/p3net/problem/genotype.py, decoding.py.
"""
