"""
p3net.problem -- generic search-space machinery: SearchSpace/Genotype,
Decoder/Validity protocols, Pareto dominance and fidelity-ladder utilities.

Domain-agnostic by design -- see genotype.py, decoding.py, objectives.py
for what deliberately does NOT live here (any NAS-specific concept belongs
in ../experiments/search_spaces/nas_genotype.py instead).

TODO:
- Re-export the public API once genotype.py, decoding.py, objectives.py are
  implemented (SearchSpace, Genotype, Decoder, Validity, pareto_front,
  FidelityLadder, ...).

Reference: chapters/v003/problem_formulation/main.tex
"""
