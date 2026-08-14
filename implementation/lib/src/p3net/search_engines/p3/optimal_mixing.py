"""Optimal mixing sweep (crossover on linkage subsets, no separate mutation
operator).

Library-scope note: donor provenance is an OPEN decision the paper itself
flags (Proposed Optimizer, "Parent, donor, and ancestor provenance" TODO):
whether a donor must come from H_t (like the parent and ancestor x0) or may
be a transient, surrogate-only individual from earlier in the same sweep.
This module currently draws donors from whatever `population` it is given
by the caller -- callers that want the H_t-only restriction should pass a
population filtered to H_t members; this is a caller-side choice, not
hardcoded here, until the paper's authors resolve the TODO.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass, field

from p3net.problem.genotype import Genotype
from p3net.search_engines.p3.linkage_tree import LinkageNode, linkage_subsets


@dataclass(frozen=True)
class Proposal:
    """One candidate modification produced by the sweep: `parent` with the
    coordinates in `subset` replaced by the donor's values there."""

    parent: Genotype
    subset: frozenset[int]
    candidate: Genotype
    donor: Genotype


def propose_modification(parent: Genotype, donor: Genotype, subset: frozenset[int]) -> Genotype:
    """x' = parent with x'_i = donor_i for i in subset, x'_i = parent_i
    otherwise."""
    indices = sorted(subset)
    new_values = [donor.values[i] for i in indices]
    return parent.with_values(indices=indices, new_values=new_values)


@dataclass
class SweepState:
    """Drives one optimal-mixing sweep step by step. The caller pulls one
    proposal at a time via `propose()`, decides acceptance externally (via
    a surrogate or a real evaluation), then reports back via `accept()` or
    `reject()` before calling `propose()` again. "The sweep continues from
    the resulting individual": an accepted proposal becomes `current`, and
    every subsequent proposal in the sweep is built from it, not from the
    original parent.
    """

    subsets: list[frozenset[int]]
    population: Sequence[Genotype]
    rng: random.Random
    current: Genotype
    _index: int = field(default=0)

    @classmethod
    def start(
        cls,
        parent: Genotype,
        linkage_tree_root: LinkageNode,
        population: Sequence[Genotype],
        rng: random.Random,
    ) -> SweepState:
        subsets = list(linkage_subsets(linkage_tree_root))
        rng.shuffle(subsets)
        return cls(subsets=subsets, population=population, rng=rng, current=parent)

    @property
    def done(self) -> bool:
        return self._index >= len(self.subsets)

    def propose(self) -> Proposal:
        if self.done:
            raise StopIteration("sweep already exhausted")
        subset = self.subsets[self._index]
        donor = self.rng.choice(list(self.population))
        candidate = propose_modification(self.current, donor, subset)
        return Proposal(parent=self.current, subset=subset, candidate=candidate, donor=donor)

    def accept(self, proposal: Proposal) -> None:
        self.current = proposal.candidate
        self._index += 1

    def reject(self, proposal: Proposal) -> None:
        self._index += 1
