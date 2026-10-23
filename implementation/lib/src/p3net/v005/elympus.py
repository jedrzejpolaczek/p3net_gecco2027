"""eLyMPuS on real evaluations (Przewozniczek, Chicano, Tinos, Komarnicki, GECCO'26,
pp. 647-651; reference code github.com/przewooz/OLyMPuS; card `elympus.md`, steps
E1-E11, decisions E-1 a, E-2 a, E-3 a, assumptions Z-E1-Z-E6).

- ELyMPuS (one per objective, E-2 a): empty VIG at start (E1); per variable g a
  list of entries (stored solution, objective of every value of g) -- the k-ary
  generalisation Z-E1 of the code's "best values" (`GeneContext_Values`); an entry
  matches a query when every variable dependent on g in the *current* VIG has the
  same value (E2, E4).
- partial_compare (Pseudocode 2): a hit costs nothing; with verification, or on a
  miss, the k values of g are evaluated really; a hit whose fresh answer differs
  triggers RecursiveLL (E3).
- recursive_ll (Pseudocode 3): halving the differing variables until the one that
  changes g's comparison is found; the edge is added both ways (symmetrical, Z-E6).
- OneOverX (E8, Z-E3): the 1/x verification schedule with the code's three extra
  rules (`vRefreshStrategy_Reset`, `v_update_optimized_individuals`).
- fihc_elympus (Pseudocode 4): FIHC with partial comparisons for both objectives, a
  move only on dominance (Z-E5), CheckCircuits on every improving move (E10).
- P3ELyMPuS (E-1 a): canonical P3 with its FIHC replaced by FIHC-eLyMPuS; the FIHC
  result is evaluated really before entering the pyramid (E-3 a).

The comparison logic is written as generators that yield a genotype whenever they
need a real objective value, so that the public callback functions and the ask-tell
method share one implementation.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Generator, Sequence

from p3net.problem.genotype import Genotype
from p3net.problem.objectives import dominates
from p3net.v005.common import is_valid
from p3net.v005.p3.engine import P3Engine


def _drive(gen: Generator, evaluate: Callable):
    """Run a generator that yields genotypes, answering each with evaluate(g)."""
    try:
        g = next(gen)
        while True:
            g = gen.send(evaluate(g))
    except StopIteration as stop:
        return stop.value


def _sign(x: float) -> int:
    return (x > 0) - (x < 0)


class _Entry:
    __slots__ = ("solution", "f")

    def __init__(self, solution: tuple[int, ...], f: list[float]):
        self.solution = solution  # the solution the k values were evaluated around
        self.f = f  # objective of the solution with g set to each value 0..k-1


class ELyMPuS:
    def __init__(self, domains: Sequence[int], rng):
        self.domains = [int(k) for k in domains]
        self.rng = rng
        self.vig: dict[int, set[int]] = {i: set() for i in range(len(self.domains))}
        self.entries: dict[int, list[_Entry]] = {i: [] for i in range(len(self.domains))}
        self.optima: set[Genotype] = set()  # local optima reached (Z-E3 rule 3)
        self.found = 0  # dependencies discovered in the current FIHC call

    # -- pair list ---------------------------------------------------------------
    def _find(self, x: tuple[int, ...], var: int) -> _Entry | None:
        ctx = self.vig[var]
        for e in self.entries[var]:
            if all(e.solution[j] == x[j] for j in ctx):
                return e
        return None

    def _compute(self, x: tuple[int, ...], var: int):
        """Real objective of x with `var` set to every value (Z-E1: one FIHC step)."""
        f = []
        for v in range(self.domains[var]):
            y = x[:var] + (v,) + x[var + 1:]
            f.append((yield Genotype(values=y)))
        return f

    @staticmethod
    def _ordering(f: Sequence[float]) -> tuple[int, ...]:
        return tuple(_sign(a - f[0]) for a in f[1:])

    def _pc_gen(self, x: Genotype, var: int, value: int, verify: bool):
        xv = tuple(x.values)
        e = self._find(xv, var)
        if e is not None and not verify:
            return _sign(e.f[xv[var]] - e.f[value])
        f = yield from self._compute(xv, var)
        if e is not None and self._ordering(e.f) != self._ordering(f):
            # E3: the stored answer is wrong in this context -> a missing dependency
            yield from self._rll_gen(Genotype(values=e.solution), x, var)
        self.entries[var].append(_Entry(xv, f))
        return _sign(f[xv[var]] - f[value])

    def partial_compare(self, x: Genotype, var: int, value: int, evaluate, verify: bool) -> int:
        """> 0 iff x with var := value is strictly better (smaller) than x (Q-14)."""
        return _drive(self._pc_gen(x, var, value, verify), evaluate)

    # -- RecursiveLL (Pseudocode 3) ------------------------------------------------
    def _rll_gen(self, x1: Genotype, x2: Genotype, var: int):
        a, b = tuple(x1.values), tuple(x2.values)
        D = [i for i in range(len(a)) if a[i] != b[i] and i != var]
        if not D:
            return None, 0
        r1 = self._ordering((yield from self._compute(a, var)))
        splits = 0
        while len(D) > 1:
            splits += 1
            D1, D2 = D[: len(D) // 2], D[len(D) // 2:]
            mid = list(a)
            for i in D1:
                mid[i] = b[i]
            mid = tuple(mid)
            r_mid = self._ordering((yield from self._compute(mid, var)))
            if r_mid == r1:  # the change of the comparison lies in D2 (between mid and b)
                a, D = mid, D2
            else:  # it lies in D1 (between a and mid)
                b, D = mid, D1
        v = D[0]
        if v not in self.vig[var]:
            self.vig[var].add(v)
            self.vig[v].add(var)
            self.found += 1
        return v, splits

    def recursive_ll(self, x1: Genotype, x2: Genotype, var: int, evaluate) -> tuple[int | None, int]:
        """(dependent variable, number of splits) -- Q-15."""
        return _drive(self._rll_gen(x1, x2, var), evaluate)


class OneOverX:
    """E8 1/x verification schedule with the reference code's rules (Z-E3):
    (1) always verify while the VIG is empty; (2) verify in the call following a
    call that discovered a dependency; (3) reset the counters when FIHC reaches an
    already found local optimum."""

    def __init__(self) -> None:
        self.next_check = 0
        self.step = 0
        self.found_prev = 0
        self.found_this = 0

    def start_call(self, vig_empty: bool) -> bool:
        self.found_prev, self.found_this = self.found_this, 0
        verify = False
        if self.found_prev > 0:
            verify, self.step = True, 0
        self.next_check -= 1
        if self.next_check <= 0:
            if self.found_prev == 0:
                self.step += 1
            self.next_check = self.step
            verify = True
        return verify or vig_empty

    def end_call(self, found_dependency: bool, repeated_optimum: bool) -> None:
        self.found_this += int(bool(found_dependency))
        if repeated_optimum:
            self.next_check = 0
            self.step = 0
            self.found_this = 0


def _fihc_elympus_gen(x: Genotype, els: tuple[ELyMPuS, ELyMPuS], schedule, rng,
                      order: list[int] | None, valid: Callable[[Genotype], bool]):
    """Pseudocode 4 for two objectives. Yields genotypes, receives (f1, f2)."""
    domains = els[0].domains
    n = len(domains)
    vig_empty = all(not any(e.vig.values()) for e in els)
    verify = schedule.start_call(vig_empty)
    for e in els:
        e.found = 0
    if order is None:
        order = list(range(n))
        rng.shuffle(order)

    def component(gen, k):
        """Lift a scalar generator of objective k to the vector protocol."""
        try:
            g = next(gen)
            while True:
                g = gen.send((yield g)[k])
        except StopIteration as stop:
            return stop.value

    cur = x
    trajectory: list[tuple[Genotype, int, int]] = []  # (solution before, var, value) of moves
    visited: list[Genotype] = [cur]
    quiet = pos = 0
    while quiet < n:
        i = order[pos % n]
        pos += 1
        changed = False
        for v in [v for v in range(domains[i]) if v != cur.values[i]]:
            cand = cur.with_values(indices=[i], new_values=[v])
            if not valid(cand):
                continue
            res = []
            for k, e in enumerate(els):
                res.append((yield from component(e._pc_gen(cur, i, v, verify), k)))
            if all(r >= 0 for r in res) and any(r > 0 for r in res):  # Z-E5: dominance
                trajectory.append((cur, i, v))
                cur = cand
                changed = True
                if cur in visited:  # E10: CheckCircuits
                    yield from _check_circuits(trajectory, els, component)
                    trajectory, visited = [], [cur]
                else:
                    visited.append(cur)
        quiet = 0 if changed else quiet + 1
    found = sum(e.found for e in els) > 0
    repeated = cur in els[0].optima
    els[0].optima.add(cur)
    schedule.end_call(found, repeated)
    return cur


def _check_circuits(trajectory, els, component):
    """Pseudocode 5: a return to a visited solution means some move was not an
    improvement; re-check the moves with real evaluations until the wrong answer is
    found (its RecursiveLL is run by partial comparison with verification)."""
    for sol, var, value in trajectory:
        for k, e in enumerate(els):
            before = e.found
            yield from component(e._pc_gen(sol, var, value, True), k)
            if e.found > before:
                return True
    return False


def fihc_elympus(x: Genotype, elympus: tuple[ELyMPuS, ELyMPuS], evaluate, schedule, rng,
                 order: list[int] | None = None) -> Genotype:
    """FIHC-eLyMPuS; evaluate(g) -> (f1, f2) (Q-14); `order` fixes the variable order (Q-16)."""
    return _drive(_fihc_elympus_gen(x, tuple(elympus), schedule, rng, order, lambda g: True), evaluate)


def vig_known(elympus_pair):
    """Z-E7: a variable pair is known when the dependency is in the VIG of either
    eLyMPuS instance (E-4 linkage: unknown pairs get distance + 1)."""
    vigs = [e.vig for e in elympus_pair]
    return lambda a, b: any(b in v.get(a, ()) for v in vigs)


class P3ELyMPuS(P3Engine):
    """E-1 a: canonical P3 with FIHC-eLyMPuS; eLyMPuS memory lives for the whole run (W-E13)."""

    def __init__(self, space, budget, rng, *, observer=None):
        super().__init__(space, budget, rng, step_evaluator="real", observer=observer)
        self.elympus = (ELyMPuS(self.domains, rng), ELyMPuS(self.domains, rng))
        self.schedule = OneOverX()
        self.pyramid.known = vig_known(self.elympus)  # E-4

    def _fihc(self, x: Genotype, fx):
        gen = _fihc_elympus_gen(x, self.elympus, self.schedule, self.rng, None,
                                lambda g: is_valid(self.space, g))
        try:
            g = next(gen)
            while True:
                g = gen.send((yield g))
        except StopIteration as stop:
            result = stop.value
        f_result = yield result  # E-3 a: the FIHC result is really evaluated
        return result, f_result
