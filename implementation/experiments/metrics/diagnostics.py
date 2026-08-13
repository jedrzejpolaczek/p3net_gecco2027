"""
Genotype duplication rate and archive turnover diagnostics.

TODO:
- Implement genotype duplication rate: measured under the identical joint
  genotype encoding fixed for every compared method
  (experiments/search_spaces/nas_genotype.py), counted at PROPOSAL time
  (every candidate a search operator generates), not at evaluation time --
  must reflect what each operator proposes, not an artifact of the shared
  dedup cache (p3net.harness.evaluation_cache).
- Implement archive turnover over the course of search.
- This diagnostic is the empirical test of whether P3's dependency-aware
  operator actually generates fewer duplicates than NSGA-II's blind
  crossover -- the paper is explicit that duplicates (decoding redundancy)
  and variable dependencies (fitness relevance) are different phenomena
  that need not coincide; this module measures whether they do, it does
  not assume it.

Reference: chapters/v003/introduction/main.tex (NSGA-Net duplication-rate
paragraphs); chapters/v003/results/main.tex ("Diagnostics").
"""
