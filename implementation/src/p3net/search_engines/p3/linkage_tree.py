"""
Linkage tree construction: agglomerative UPGMA clustering over normalised
mutual information between genotype variables.

Library-scope note: operates on any Genotype produced from the generic
SearchSpace in problem/genotype.py -- must not assume "architecture edge" or
"hyperparameter" variable semantics. The paper's own genotype (six
architecture edges + discretised Theta, all categorical after applying its
own discretisation option (i)) is just one instance of a SearchSpace this
module is handed; it works identically on any other categorical genotype.

TODO:
- Compute a normalised mutual-information-based dependency measure between
  genotype variables from the current population.
- Build the tree via agglomerative, UPGMA-style hierarchical clustering over
  that measure, yielding the nested family of variable subsets F used by
  optimal mixing.
- Require only that every variable in the genotype is categorical (finite
  domain) -- continuous variables must already be discretised by whatever
  SearchSpace/discretisation policy the caller chose (problem/genotype.py);
  this module performs no discretisation itself and has no opinion on how a
  caller reached a categorical encoding.
- Enforce the rebuild granularity rule: the tree built at the start of a
  search iteration is reused for every parent's sweep within that iteration,
  and is only rebuilt at the next pass through step 6 of the search loop
  (methods/p3net.py) -- do not rebuild mid-sweep.

Reference: chapters/v003/proposed_optimizer/main.tex ("Representation and
linkage tree", Figure fig:linkage-tree); chapters/v003/notes/main.tex
("Search engine" table, "Tree rebuild granularity"). Concrete NAS genotype
this is exercised against: experiments/search_spaces/nas_genotype.py.
"""
