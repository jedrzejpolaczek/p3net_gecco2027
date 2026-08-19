"""Linkage tree construction: agglomerative UPGMA clustering over normalised
mutual information between genotype variables.

Library-scope note: operates on any Genotype produced from the generic
SearchSpace in problem/genotype.py -- must not assume "architecture edge" or
"hyperparameter" variable semantics. Requires only that every variable in
the genotype is categorical (finite domain); continuous variables must
already be discretised by whatever SearchSpace/discretisation policy the
caller chose. This module performs no discretisation itself.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

from sklearn.metrics import normalized_mutual_info_score

from p3net.problem.genotype import Genotype


@dataclass(frozen=True)
class LinkageNode:
    """One node of the linkage tree: a variable subset F, and (for internal
    nodes) its two children. Leaves have no children."""

    subset: frozenset[int]
    left: LinkageNode | None = None
    right: LinkageNode | None = None

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


def _pairwise_normalized_mutual_information(
    population: list[Genotype], n: int
) -> list[list[float]]:
    columns = [[g.values[i] for g in population] for i in range(n)]
    mi = [[0.0] * n for _ in range(n)]
    # sklearn's normalized_mutual_info_score warns whenever a column's
    # values don't look like small-integer cluster labels -- expected and
    # harmless here: genotype columns are discretised (this module's own
    # docstring requires it), but the discretised values themselves are
    # still floats/strings, not relabelled integers, which is all the
    # warning is actually detecting. Suppressed narrowly (this exact
    # message, this exact call site) rather than globally, so an
    # unrelated warning elsewhere still surfaces normally.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Clustering metrics expects discrete values",
            category=UserWarning,
        )
        for i in range(n):
            for j in range(i + 1, n):
                score = normalized_mutual_info_score(columns[i], columns[j])
                mi[i][j] = mi[j][i] = score
    return mi


def build_linkage_tree(population: list[Genotype]) -> LinkageNode:
    """Agglomerative, UPGMA-style hierarchical clustering over normalised
    mutual information between genotype variables (columns of the current
    population), yielding the nested family of variable subsets F used by
    optimal mixing (Figure fig:linkage-tree).
    """
    if not population:
        raise ValueError("cannot build a linkage tree from an empty population")
    n = len(population[0].values)
    if n == 0:
        raise ValueError("genotypes must have at least one variable")
    if any(len(g.values) != n for g in population):
        raise ValueError("all genotypes in the population must share the same dimensionality")
    if n == 1:
        return LinkageNode(subset=frozenset({0}))

    mi = _pairwise_normalized_mutual_information(population, n)

    clusters: dict[int, LinkageNode] = {i: LinkageNode(subset=frozenset({i})) for i in range(n)}
    members: dict[int, set[int]] = {i: {i} for i in range(n)}
    next_id = n

    def distance(a: int, b: int) -> float:
        pairs = [(i, j) for i in members[a] for j in members[b]]
        avg_mi = sum(mi[i][j] for i, j in pairs) / len(pairs)
        return 1.0 - avg_mi

    active = list(range(n))
    while len(active) > 1:
        best_pair: tuple[int, int] | None = None
        best_dist = float("inf")
        for a_idx in range(len(active)):
            for b_idx in range(a_idx + 1, len(active)):
                a, b = active[a_idx], active[b_idx]
                d = distance(a, b)
                if d < best_dist:
                    best_dist = d
                    best_pair = (a, b)
        assert best_pair is not None
        a, b = best_pair
        merged = LinkageNode(
            subset=clusters[a].subset | clusters[b].subset, left=clusters[a], right=clusters[b]
        )
        clusters[next_id] = merged
        members[next_id] = members[a] | members[b]
        active.remove(a)
        active.remove(b)
        active.append(next_id)
        next_id += 1

    return clusters[active[0]]


def linkage_subsets(root: LinkageNode) -> list[frozenset[int]]:
    """Flatten a linkage tree into the list of internal-node subsets F used
    by the optimal mixing sweep ("each internal node is a candidate linkage
    subset F")."""
    subsets: list[frozenset[int]] = []

    def walk(node: LinkageNode) -> None:
        if node.is_leaf:
            return
        subsets.append(node.subset)
        walk(node.left)  # type: ignore[arg-type]
        walk(node.right)  # type: ignore[arg-type]

    walk(root)
    return subsets
