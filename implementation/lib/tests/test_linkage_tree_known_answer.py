"""Known-answer test for linkage learning on a categorical genotype.

P3's premise is that normalised mutual information plus UPGMA clustering
recovers groups of jointly-determined variables. That was only ever
validated on binary problems in the literature; this project applies it to
k-ary categorical genotypes. Here the answer is known by construction: each
block of variables is copied as a whole from one of two block patterns, so
variables inside a block are perfectly dependent and variables in different
blocks are independent. The tree must contain every true block as a node.

Blocks are interleaved through a fixed random permutation so that adjacency
cannot accidentally produce the right answer.

Criterion fixed before first run: every true block recovered in every seed.
"""

from __future__ import annotations

import random

import pytest

from p3net.problem.genotype import Genotype
from p3net.search_engines.p3.linkage_tree import build_linkage_tree, linkage_subsets

ALPHABET = (0, 1, 2)


def _structured_population(*, blocks: int, block_len: int, size: int, seed: int):
    rng = random.Random(seed)
    n = blocks * block_len
    positions = list(range(n))
    rng.shuffle(positions)
    true_blocks = [frozenset(positions[b * block_len : (b + 1) * block_len]) for b in range(blocks)]
    population = []
    for _ in range(size):
        values = [0] * n
        for block in true_blocks:
            # each block copied whole from one of two distinct k-ary patterns
            pattern_a = [0] * block_len
            pattern_b = [1 if i % 2 == 0 else 2 for i in range(block_len)]  # uses the other two symbols
            chosen = pattern_a if rng.random() < 0.5 else pattern_b
            for pos, v in zip(sorted(block), chosen):
                values[pos] = v
        population.append(Genotype(values=tuple(values)))
    return population, true_blocks


@pytest.mark.parametrize("seed", range(10))
def test_linkage_tree_recovers_every_true_block_on_a_kary_genotype(seed):
    population, true_blocks = _structured_population(blocks=5, block_len=4, size=80, seed=seed)
    subsets = set(linkage_subsets(build_linkage_tree(population)))
    missing = [sorted(b) for b in true_blocks if b not in subsets]
    assert not missing, f"blocks not recovered as linkage-tree nodes: {missing}"


def test_independent_variables_are_not_merged_before_dependent_ones():
    """Sanity on the ordering: in a population with true blocks, no subset
    that straddles two blocks may appear before (i.e. be smaller than) a
    complete block it partially contains."""
    population, true_blocks = _structured_population(blocks=4, block_len=3, size=80, seed=0)
    for subset in linkage_subsets(build_linkage_tree(population)):
        touched = [b for b in true_blocks if subset & b]
        if len(touched) > 1:
            assert all(b <= subset for b in touched), f"subset {sorted(subset)} splits a true block"
