"""
TODO:
- Test UPGMA clustering over normalised mutual information produces a
  valid nested family of variable subsets.
- Test the tree is rebuilt only at iteration boundaries (step 6), not
  mid-sweep -- same tree instance reused across every parent's sweep
  within one iteration.
- Test behaviour on the joint (architecture + discretised Theta) genotype,
  not just the architecture-only case.

Reference: src/p3net/search_engines/p3/linkage_tree.py;
chapters/v003/proposed_optimizer/main.tex ("Representation and linkage
tree").
"""
