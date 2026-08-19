"""k-ary generalisation of the trap/bimodal-deceptive functions used by
`przewozniczek2026lympus` (Eq. 1, bim_ell over {0,1}) to validate eLyMPuS
before touching binary problems. Built for
`implementation/lib/src/p3net/surrogates/elympus.py`'s own Faza 2 synthetic
validation (notes/plans/experiments-przewozniczek-plan.md) -- not NAS-
specific, so it lives next to `genotype.py`/`objectives.py`, not in an
experiments-* fork.

Design: the source paper's bim_ell(u) is a deceptive trap over the
*unitation* u (count of 1s) of an order-ell binary block, with two optima --
u=0 and u=ell both score ell/2, monotonically decreasing away from either
towards the middle. Generalising "unitation" to an alphabet of size K>2
requires picking what u counts; there is no unique canonical choice (the
source paper never defines one, see notes/lympus-nas-adaptation-literature.md).
This module picks the simplest, most standard generalisation from the trap-
function literature: u = the number of block variables equal to a single
designated "target" value (here 0), everything else counts as "wrong". This
keeps the essential property eLyMPuS's non-monotonicity check needs --
whether moving one block variable towards the target value helps or hurts
depends on how many OTHER block variables are already at the target value,
i.e. genuine within-block non-monotonic dependency, generalised losslessly
to K>2 because "equal to target" vs "not" is a binary partition of any
alphabet size.
"""

from __future__ import annotations

from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace


def k_ary_trap_block(values: tuple[int, ...], *, target: int = 0) -> float:
    """Standard order-B trap function generalised to any alphabet: u = count
    of `target` among `values`. Deceptive optimum at u = B-1 (fitness B-1,
    reachable by hill-climbing from most starting points); global optimum
    only at u = B (fitness B), separated from the deceptive optimum by a
    fitness valley at u = B-1 -> not literally B-1 (this IS the trap: u=B-1
    scores the *worst*, forcing a simultaneous change of the last variable
    to escape). Maximisation convention internally; see `k_ary_trap_fitness`
    for the minimisation wrapper this repo's `dominates()` expects."""
    block_size = len(values)
    u = sum(1 for v in values if v == target)
    if u == block_size:
        return float(block_size)
    return float(block_size - 1 - u)


def build_k_ary_trap_space(
    *, n_blocks: int, block_size: int = 4, alphabet_size: int = 4
) -> SearchSpace:
    """n_blocks independent blocks of `block_size` variables each, alphabet
    {0, ..., alphabet_size - 1}. True dependency structure (ground-truth VIG
    for validation): every pair of variables within the same block is
    dependent; no dependency across blocks -- exactly the additive-separable
    structure of the source paper's Example 2.1."""
    if alphabet_size < 2:
        raise ValueError("alphabet_size must be >= 2")
    domain = CategoricalDomain(values=tuple(range(alphabet_size)))
    n = n_blocks * block_size
    return SearchSpace(domains=(domain,) * n)


def k_ary_trap_fitness(
    genotype: Genotype, *, block_size: int = 4, target: int = 0
) -> float:
    """Minimisation-convention total fitness: negative sum of per-block trap
    scores (higher raw trap score = better, so negate for `dominates()`'s
    lower-is-better convention used throughout this repo)."""
    n = len(genotype.values)
    if n % block_size != 0:
        raise ValueError("genotype length must be a multiple of block_size")
    total = 0.0
    for start in range(0, n, block_size):
        block = genotype.values[start : start + block_size]
        total += k_ary_trap_block(block, target=target)
    return -total


def true_dependency_graph(n_blocks: int, block_size: int) -> dict[int, set[int]]:
    """Ground-truth VIG for `build_k_ary_trap_space`'s additive-separable
    block structure -- used by the Faza 2 validation to check eLyMPuS
    behaves correctly when the empirical graph equals this exactly (Theorem
    1's precondition) and to check discovered dependencies are always a
    subset of this (soundness: eLyMPuS must never invent a false
    dependency)."""
    graph: dict[int, set[int]] = {i: set() for i in range(n_blocks * block_size)}
    for b in range(n_blocks):
        indices = list(range(b * block_size, (b + 1) * block_size))
        for i in indices:
            graph[i] = {j for j in indices if j != i}
    return graph
