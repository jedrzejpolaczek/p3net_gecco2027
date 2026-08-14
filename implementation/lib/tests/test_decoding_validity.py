"""Tests for p3net.problem.decoding -- generic Decoder/Validity protocols.

Note: the end-to-end "invalid candidates rejected before surrogate scoring"
ordering is an integration-level invariant of the search loop, covered by
tests/test_p3net_integration.py -- this file tests the Decoder/Validity
building blocks themselves, in isolation.
"""

from p3net.problem.decoding import is_valid, valid_subset
from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace


def make_toy_space() -> SearchSpace:
    return SearchSpace(domains=(CategoricalDomain(values=(0, 1, 2)),) * 3)


def sum_at_most_three(genotype: Genotype) -> float:
    """A synthetic Validity: valid iff the sum of coordinates is <= 3."""
    return sum(genotype.values) - 3


def to_string(genotype: Genotype) -> str:
    """A synthetic Decoder: turns a genotype into an arbitrary target type
    (here, a string) -- proves the library places no assumption on T."""
    return "-".join(str(v) for v in genotype.values)


def test_decoder_accepts_arbitrary_target_type():
    genotype = Genotype(values=(1, 2, 0))
    assert to_string(genotype) == "1-2-0"


def test_is_valid_splits_on_threshold():
    assert is_valid(Genotype(values=(0, 0, 0)), sum_at_most_three)
    assert is_valid(Genotype(values=(1, 1, 1)), sum_at_most_three)
    assert not is_valid(Genotype(values=(2, 2, 2)), sum_at_most_three)


def test_valid_subset_filters_correctly():
    genotypes = [
        Genotype(values=(0, 0, 0)),
        Genotype(values=(2, 2, 2)),
        Genotype(values=(1, 1, 0)),
    ]
    filtered = valid_subset(genotypes, sum_at_most_three)
    assert filtered == [genotypes[0], genotypes[2]]
