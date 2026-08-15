"""delta_hat_F: relative, linkage-aware surrogate (P3Net's own
contribution)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from p3net.harness.runner import Observation
from p3net.problem.genotype import Genotype
from p3net.surrogates._encoding import build_vocab, one_hot


class NoLinkageTreeError(RuntimeError):
    """Raised when delta_hat_F is used without a linkage tree / subset
    context -- it cannot pair with NSGA-II, which has no linkage tree."""


def _pair_features(x: Genotype, x_prime: Genotype, vocab: list[dict[Any, int]]) -> list[float]:
    """One-hot encoding of BOTH endpoints, concatenated -- captures the
    full directional transition. A same-coordinates-changed diff mask
    alone cannot distinguish x -> x' from x' -> x, which have opposite-sign
    deltas; encoding both endpoints' actual values fixes that."""
    return one_hot(x, vocab) + one_hot(x_prime, vocab)


def _matching_subset(
    x: Genotype, x_prime: Genotype, subsets: list[frozenset[int]]
) -> frozenset[int] | None:
    diff_indices = {i for i in range(len(x.values)) if x.values[i] != x_prime.values[i]}
    if not diff_indices:
        return None
    for subset in subsets:
        if diff_indices <= subset:
            return subset
    return None


@dataclass
class RelativeLinkageAwareSurrogate:
    """delta_hat_F(x, x') ~= f1(x) - f1(x'), for x' differing from x only on
    a linkage subset F. Trained on pairwise fitness differences derived
    from H_t, restricted to pairs that differ only within one of the given
    linkage subsets. Mechanistically a regressor over continuous
    differences (closer to CS-GOMEA), not eLyMPuS's discrete comparison --
    no formal recovery guarantee is implied or checked here.
    """

    model_factory: Callable[[], Any]
    _model: Any = field(default=None, init=False, repr=False)
    _vocab: list[dict[Any, int]] | None = field(default=None, init=False, repr=False)
    _fitted_subsets: set[frozenset[int]] = field(default_factory=set, init=False, repr=False)

    def fit(
        self,
        observations: list[Observation],
        subsets: list[frozenset[int]],
        *,
        objective_index: int = 0,
    ) -> None:
        pairs = []
        for a in observations:
            for b in observations:
                if a is b:
                    continue
                if _matching_subset(a.genotype, b.genotype, subsets) is not None:
                    pairs.append((a, b))
        if not pairs:
            raise NoLinkageTreeError(
                "no observed pair differs only within a given linkage subset -- "
                "delta_hat_F cannot be fit without a linkage tree providing "
                "subsets that actually partition the observed variation"
            )
        self._vocab = build_vocab(observations)
        # Encode each distinct genotype once and reuse it across every pair
        # it appears in, rather than recomputing one_hot per pair -- H_t
        # grows over a run, so this loop's pair count grows quadratically
        # in |H_t| while the number of distinct genotypes only grows
        # linearly (profiled: one_hot was the single largest cost in a
        # 200-budget run, ~5.4M calls from re-encoding the same genotypes
        # repeatedly).
        encoded: dict[Genotype, list[float]] = {}
        for obs in observations:
            if obs.genotype not in encoded:
                encoded[obs.genotype] = one_hot(obs.genotype, self._vocab)
        X = [encoded[a.genotype] + encoded[b.genotype] for a, b in pairs]
        y = [a.objectives[objective_index] - b.objectives[objective_index] for a, b in pairs]
        self._model = self.model_factory()
        self._model.fit(X, y)
        self._fitted_subsets = set(subsets)

    def predict(self, x: Genotype, x_prime: Genotype, subset: frozenset[int]) -> float:
        if self._model is None or self._vocab is None:
            raise NoLinkageTreeError(
                "delta_hat_F.predict called before fit -- no linkage tree available yet"
            )
        if subset not in self._fitted_subsets:
            raise ValueError("this surrogate instance was not fit against the given linkage subset")
        return float(self._model.predict([_pair_features(x, x_prime, self._vocab)])[0])
