"""Shared one-hot encoding helpers for the two regression-based surrogates
(absolute_regressor.py, relative_linkage_aware.py). Internal module -- not
re-exported from p3net.surrogates.__init__.

Extracted after a maintainability audit found this logic duplicated
verbatim in both call sites; kept here as the single source of truth so the
two surrogates cannot silently drift apart on encoding behaviour.
"""

from __future__ import annotations

from typing import Any

from p3net.harness.runner import Observation
from p3net.problem.genotype import Genotype


def build_vocab(observations: list[Observation]) -> list[dict[Any, int]]:
    """Build a per-coordinate value -> index vocabulary from the observed
    genotypes, used to one-hot encode any genotype over the same
    SearchSpace consistently between fit and predict."""
    n = len(observations[0].genotype.values)
    vocab: list[dict[Any, int]] = [dict() for _ in range(n)]
    for obs in observations:
        for i, v in enumerate(obs.genotype.values):
            if v not in vocab[i]:
                vocab[i][v] = len(vocab[i])
    return vocab


def one_hot(genotype: Genotype, vocab: list[dict[Any, int]]) -> list[float]:
    """One-hot encode a genotype against a vocabulary built by
    build_vocab(). A value not present in the vocabulary at predict time
    (unseen at fit time) encodes as an all-zero slice for that
    coordinate."""
    features: list[float] = []
    for i, v in enumerate(genotype.values):
        slot = [0.0] * len(vocab[i])
        idx = vocab[i].get(v)
        if idx is not None:
            slot[idx] = 1.0
        features.extend(slot)
    return features
