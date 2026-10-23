"""First-improvement hill climber (Goldman & Punch 2014, §2.1, p. 786; card
`p3net.md` P10-P12; D-1: strict improvement = dominance).

The logic lives in `fihc_steps`, a generator yielding (candidate, current) pairs
and receiving the comparison result, so the same code serves the public function
`fihc` (comparison by callback) and the ask-tell methods (comparison after a real
evaluation).
"""

from __future__ import annotations

from collections.abc import Callable, Generator

from p3net.problem.genotype import Genotype


def fihc_steps(
    g: Genotype, domains: list[int], rng, order: list[int] | None = None
) -> Generator[tuple[Genotype, Genotype], int, Genotype]:
    """P10: positions in random order (or `order`); P11: every other value of the
    position is compared with the current solution, in increasing value order, and
    a strictly better one replaces it; P12: repeat until a full cycle of positions
    brings no change -- positions checked since the last change are not re-checked.

    The value order is fixed (the source does not specify one) so that, given the
    position order, the trajectory does not depend on the generator (W-E12)."""
    n = len(domains)
    if order is None:
        order = list(range(n))
        rng.shuffle(order)
    cur = g
    quiet = 0  # positions checked without a change since the last change
    pos = 0
    while quiet < n:
        i = order[pos % n]
        pos += 1
        changed = False
        for v in [v for v in range(domains[i]) if v != cur.values[i]]:
            cand = cur.with_values(indices=[i], new_values=[v])
            if (yield cand, cur) > 0:
                cur = cand
                changed = True
        quiet = 0 if changed else quiet + 1
    return cur


def fihc(
    g: Genotype,
    compare: Callable[[Genotype, Genotype], int],
    domains: list[int],
    rng,
    order: list[int] | None = None,
) -> Genotype:
    """compare(a, b) > 0 iff a is strictly better than b (interfaces §1, Q-14)."""
    steps = fihc_steps(g, domains, rng, order)
    try:
        cand, cur = next(steps)
        while True:
            cand, cur = steps.send(compare(cand, cur))
    except StopIteration as stop:
        return stop.value
