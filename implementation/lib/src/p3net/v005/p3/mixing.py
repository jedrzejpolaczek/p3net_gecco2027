"""Mixing a solution with one pyramid level (Goldman & Punch 2014, Fig. 3 and §2.3,
pp. 786-787; card `p3net.md` P20-P25) and the MO-GOMEA acceptance rule (D-1 b,
Luong et al. 2014).

`mix_steps` is a generator yielding (cluster, candidate, current) for every
changing proposal and receiving the accept decision; `mix_with_level` drives it
with a callback.
"""

from __future__ import annotations

from collections.abc import Callable, Generator, Sequence

from p3net.problem.genotype import Genotype
from p3net.problem.objectives import dominates


def mix_steps(
    g: Genotype, level: Sequence[Genotype], clusters: Sequence[tuple[int, ...]], rng
) -> Generator[tuple[tuple[int, ...], Genotype, Genotype], bool, Genotype]:
    """P20: clusters in the given order; P21-P23: donors in random order until one
    differs from the solution on the cluster (one donor per cluster); P22/P24: the
    change is kept iff accepted (ties are the acceptance rule's business); P25: at
    most one proposal per cluster. A cluster on which no donor differs yields
    (cluster, current, current) -- an unchanged step the driver must not evaluate."""
    cur = g
    for cluster in clusters:
        donors = list(level)
        rng.shuffle(donors)
        cand = None
        for d in donors:
            c = cur.with_values(indices=list(cluster), new_values=[d.values[i] for i in cluster])
            if c != cur:
                cand = c
                break
        if cand is None:
            yield cluster, cur, cur
            continue
        if (yield cluster, cand, cur):
            cur = cand
    return cur


def mix_with_level(
    g: Genotype,
    level: Sequence[Genotype],
    clusters: Sequence[tuple[int, ...]],
    accept: Callable[[Genotype, Genotype], bool],
    rng,
) -> Genotype:
    """accept(candidate, current) -> True keeps the change (interfaces §7, Q-04)."""
    steps = mix_steps(g, level, clusters, rng)
    try:
        cluster, cand, cur = next(steps)
        while True:
            decision = False if cand == cur else bool(accept(cand, cur))
            cluster, cand, cur = steps.send(decision)
    except StopIteration as stop:
        return stop.value


def mogomea_accept(new: Sequence[float], old: Sequence[float], archive: Sequence[Sequence[float]]) -> bool:
    """D-1 b (MO-GOMEA, Luong et al. 2014): keep the change iff the new solution
    dominates the old one, has the same objective values, or is not dominated by
    the elitist archive."""
    new, old = tuple(new), tuple(old)
    if dominates(new, old) or new == old:
        return True
    return not any(dominates(tuple(a), new) for a in archive)
