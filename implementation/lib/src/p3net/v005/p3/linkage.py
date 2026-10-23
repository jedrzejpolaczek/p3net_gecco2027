"""P3 linkage learning (Goldman & Punch, GECCO'14, §2.2 and Fig. 2, p. 786;
card `p3net.md` P13-P18).

- FrequencyTable (P13): value statistics of the solutions on one level.
- entropy (Eq. 2) and cluster_distance (Eq. 1).
- build_clusters (Fig. 2): agglomerative clustering from singletons, merging the
  closest pair by D; `useful` keeps every created cluster including singletons
  (P15), drops both children of a D = 0 merge (P16), is ordered smallest-first
  with random ties (P17) and excludes the whole-genotype root (P18).
"""

from __future__ import annotations

import math
from collections import Counter

from p3net.problem.genotype import Genotype

_EPS = 1e-12


class FrequencyTable:
    """Counts of the values of every variable tuple over the added solutions.
    Entropies are computed on demand and cached until the next `add`."""

    def __init__(self, domains: list[int]):
        self.domains = list(domains)
        self.rows: list[tuple[int, ...]] = []
        self._cache: dict[tuple[int, ...], float] = {}

    def add(self, g: Genotype) -> None:
        self.rows.append(tuple(g.values))
        self._cache.clear()

    def __len__(self) -> int:
        return len(self.rows)

    def entropy(self, vars: tuple[int, ...]) -> float:
        """Eq. 2: H = -sum p log p over the joint values of `vars`."""
        key = tuple(sorted(vars))
        if key not in self._cache:
            n = len(self.rows)
            if n == 0:
                self._cache[key] = 0.0
            else:
                counts = Counter(tuple(r[i] for i in key) for r in self.rows)
                self._cache[key] = -sum((c / n) * math.log(c / n) for c in counts.values())
        return self._cache[key]


def _pair_distance(table: FrequencyTable, a: int, b: int) -> float:
    h_ab = table.entropy((a, b))
    if h_ab <= _EPS:  # both variables constant: they predict each other perfectly
        return 0.0
    return 2.0 - (table.entropy((a,)) + table.entropy((b,))) / h_ab


def _penalty(known, a: int, b: int) -> float:
    """E-4 (OLyMPuS `Population::get_distance`): +1 for a pair the VIG does not know;
    known=None is Goldman's P3."""
    return 0.0 if known is None or known(a, b) else 1.0


def cluster_distance(table: FrequencyTable, ci: tuple[int, ...], cj: tuple[int, ...], known=None) -> float:
    """Eq. 1: D(Ci, Cj) = 1/(|Ci||Cj|) sum_{a in Ci, b in Cj} [2 - (H(a)+H(b))/H(a u b)]
    (+1 per pair with `not known(a, b)`, E-4)."""
    total = sum(_pair_distance(table, a, b) + _penalty(known, a, b) for a in ci for b in cj)
    return total / (len(ci) * len(cj))


def build_clusters(table: FrequencyTable, rng, known=None) -> list[tuple[int, ...]]:
    """Fig. 2 'Cluster-Creation'. Returns the clusters in usage order (P17).
    `known(a, b)`: E-4 linkage of P3-eLyMPuS (+1 for unknown pairs); None = Goldman's P3."""
    n = len(table.domains)
    if n < 2:
        return []
    pair = {(a, b): _pair_distance(table, a, b) + _penalty(known, a, b)
            for a in range(n) for b in range(a + 1, n)}

    def dist(ci: tuple[int, ...], cj: tuple[int, ...]) -> float:
        s = sum(pair[(min(a, b), max(a, b))] for a in ci for b in cj)
        return s / (len(ci) * len(cj))

    active: list[tuple[int, ...]] = [(i,) for i in range(n)]
    useful: list[tuple[int, ...]] = list(active)
    while len(active) > 1:
        best, cands = math.inf, []
        for x in range(len(active)):
            for y in range(x + 1, len(active)):
                d = dist(active[x], active[y])
                if d < best - _EPS:
                    best, cands = d, [(x, y)]
                elif abs(d - best) <= _EPS:
                    cands.append((x, y))
        x, y = cands[rng.randrange(len(cands))]
        ci, cj = active[x], active[y]
        merged = tuple(sorted(ci + cj))
        if best <= _EPS:  # P16: sub-clusters that predict each other perfectly
            useful = [c for c in useful if c not in (ci, cj)]
        useful.append(merged)
        active = [c for k, c in enumerate(active) if k not in (x, y)] + [merged]
    root = tuple(range(n))
    useful = [c for c in useful if c != root]  # P18
    rng.shuffle(useful)
    useful.sort(key=len)  # P17: smallest first, ties in random order (stable sort)
    return useful
