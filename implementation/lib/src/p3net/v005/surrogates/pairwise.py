"""P3Net's pairwise surrogate (card `p3net-surrogate.md`; decisions S-1 a ... S-9 a).

- S-1 a: the model predicts the change of each objective between two solutions,
  delta(a, b) = log f(a) - log f(b); a chain from the last really evaluated
  ancestor x0 is predicted by telescoping, log f(x_m) = log f(x0) - sum delta(x_{i-1}, x_i).
- S-2 b: features of a pair = phi(a) - phi(b), with phi = one-hot of every variable
  plus one-hot of the value pair of every variable pair that shares a cluster of the
  current linkage tree (use_linkage=True); use_linkage=False gives the additive
  one-hot only (S-2 c, P3Net-nolink).
- S-3 a: log scale; non-positive objectives are rejected.
- S-4 a: random forest with library defaults, one per objective (S-5 a).
- Antisymmetry (W-S9) by construction: delta(a, b) = (m(z) - m(-z)) / 2.
- S-8: grouped_cv_folds splits by solutions, not by pairs.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence

import numpy as np
from sklearn.ensemble import RandomForestRegressor

from p3net.harness.runner import Observation
from p3net.problem.genotype import Genotype

#: Cap on the number of ordered training pairs (all pairs grow as N^2).
MAX_PAIRS = 3000


def _flatten(tree):
    t = tree.tree_
    return (t.children_left.tolist(), t.children_right.tolist(), t.feature.tolist(), t.threshold.tolist(),
            t.value[:, 0, 0].tolist())


def _tree_value(flat, x) -> float:
    left, right, feat, thr, val = flat
    node = 0
    while left[node] != -1:
        node = left[node] if x[feat[node]] <= thr[node] else right[node]
    return val[node]


class PairwiseSurrogate:
    def __init__(self, domains: Sequence[int], *, use_linkage: bool = True, rng=None):
        self.domains = [int(k) for k in domains]
        self.use_linkage = bool(use_linkage)
        self.rng = rng
        self._offsets = np.cumsum([0] + self.domains)
        self._pairs: list[tuple[int, int]] = []
        self._pair_offsets: list[int] = []
        self._dim = int(self._offsets[-1])
        self._models: list[RandomForestRegressor] = []
        self._delta_cache: dict[tuple[Genotype, Genotype], tuple[float, float]] = {}

    # -- features ---------------------------------------------------------------
    def _set_pairs(self, clusters: Sequence[tuple[int, ...]]) -> None:
        pairs: set[tuple[int, int]] = set()
        if self.use_linkage:
            for c in clusters:
                for i, j in itertools.combinations(sorted(c), 2):
                    pairs.add((i, j))
        self._pairs = sorted(pairs)
        off = int(self._offsets[-1])
        self._pair_offsets = []
        for i, j in self._pairs:
            self._pair_offsets.append(off)
            off += self.domains[i] * self.domains[j]
        self._dim = off

    def _phi(self, g: Genotype) -> np.ndarray:
        v = np.zeros(self._dim)
        x = g.values
        for i, xi in enumerate(x):
            v[self._offsets[i] + xi] = 1.0
        for (i, j), off in zip(self._pairs, self._pair_offsets):
            v[off + x[i] * self.domains[j] + x[j]] = 1.0
        return v

    def features(self, a: Genotype, b: Genotype) -> np.ndarray:
        return self._phi(a) - self._phi(b)

    # -- fitting ------------------------------------------------------------------
    def fit(self, history: Sequence[Observation], clusters: Sequence[tuple[int, ...]]) -> None:
        objs = np.array([o.objectives for o in history], dtype=float)
        if objs.size and np.any(objs <= 0):
            raise ValueError("log-scale surrogate (S-3 a) needs objectives > 0")
        self._set_pairs(clusters)
        self._delta_cache = {}
        n = len(history)
        all_pairs = [(a, b) for a in range(n) for b in range(n) if a != b]
        if len(all_pairs) > MAX_PAIRS:
            idx = self.rng.sample(range(len(all_pairs)), MAX_PAIRS)
            all_pairs = [all_pairs[i] for i in sorted(idx)]
        phis = np.array([self._phi(o.genotype) for o in history])
        logs = np.log(objs)
        ia = np.array([a for a, _ in all_pairs], dtype=int)
        ib = np.array([b for _, b in all_pairs], dtype=int)
        X = phis[ia] - phis[ib]
        self._models = []
        for k in range(objs.shape[1]):
            # rounding removes 1e-16 noise that would otherwise flip ties between equally
            # good splits and break the scale invariance of S-3 a (W-S5)
            y = np.round(logs[ia, k] - logs[ib, k], 9)  # ~1e-7 chance per value to sit on a boundary
            # Library defaults (S-4 a); n_jobs only parallelises the trees -- the fitted
            # forest is identical for a fixed random_state.
            m = RandomForestRegressor(random_state=self.rng.randrange(2**31), n_jobs=-1)
            m.fit(X, y)
            self._models.append(m)
        self._flat = [[_flatten(t) for t in m.estimators_] for m in self._models]

    # -- prediction ---------------------------------------------------------------
    def predict_delta(self, a: Genotype, b: Genotype) -> tuple[float, float]:
        """Predicted log f(a) - log f(b), both objectives (antisymmetric)."""
        key = (a, b)
        if key not in self._delta_cache:
            z = self.features(a, b)
            out = []
            for trees in self._flat:  # = RandomForestRegressor.predict, single-point traversal
                p_pos = sum(_tree_value(t, z) for t in trees) / len(trees)
                p_neg = sum(_tree_value(t, -z) for t in trees) / len(trees)
                out.append(float((p_pos - p_neg) / 2.0))
            self._delta_cache[key] = tuple(out)  # type: ignore[assignment]
            self._delta_cache[(b, a)] = tuple(-x for x in out)  # type: ignore[assignment]
        return self._delta_cache[key]

    def predict_chain(self, anchor: Observation, chain: Sequence[Genotype]) -> tuple[float, float]:
        """S-1 a: log objectives of the last chain element, telescoped from the
        really evaluated anchor (Q-06: log scale)."""
        logs = [math.log(x) for x in anchor.objectives]
        prev = anchor.genotype
        for g in chain:
            d = self.predict_delta(prev, g)
            logs = [lv - dv for lv, dv in zip(logs, d)]
            prev = g
        return tuple(logs)  # type: ignore[return-value]


def grouped_cv_folds(history: Sequence[Observation], n_folds: int, rng) -> list[tuple[set[int], set[int]]]:
    """S-8: folds over solutions -- every history index is validated exactly once and
    never sits in both parts of a fold (pairs are built within each part)."""
    idx = list(range(len(history)))
    rng.shuffle(idx)
    folds = [set(idx[k::n_folds]) for k in range(n_folds)]
    everything = set(range(len(history)))
    return [(everything - val, val) for val in folds]
