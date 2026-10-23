"""Level 2 (v005-level2-criteria.md), deterministic: multi-fidelity schedules.

- Hyperband (`bracket_schedule`) = Li et al. 2018 (JMLR), Table 1 (R = 81, eta = 3).
- MO-BOHB brackets = the authors' hpbandster code (`mobohb/hpbandster/optimizers/mobohb.py`,
  `__init__` lines 106-107 and `get_next_iteration` lines 143-146), formulas copied below
  verbatim, for every max fidelity used in the experiments. Promotion follows
  `SuccessiveHalvingMOBOHB` (whole NDS fronts while they fit, then one more whole
  front, so more than `ns` configurations advance); objectives on a dominance chain make
  every configuration its own front, so the expected stage sizes are exact.
"""

from __future__ import annotations

import math
import random

import numpy as np
import pytest

from p3net.problem.genotype import CategoricalDomain, SearchSpace
from p3net.v005.mf import MOBOHB, bracket_schedule


def test_hyperband_equals_li_et_al_table_1():
    li = [[(81, 1), (27, 3), (9, 9), (3, 27), (1, 81)], [(34, 3), (11, 9), (3, 27), (1, 81)],
          [(15, 9), (5, 27), (1, 81)], [(8, 27), (2, 81)], [(5, 81)]]
    assert bracket_schedule(3, 1, 81) == li


def _advance(rank: np.ndarray, num_configs_next: int) -> int:
    """`SuccessiveHalvingMOBOHB._advance_to_next_stage` (sucessivehalvingmobohb.py lines
    30-39): whole NDS fronts while they fit, then always one more whole front."""
    indices = np.arange(len(rank))
    keep = np.array([], dtype=int)
    i = 0
    while len(keep) + sum(rank == i) <= num_configs_next:
        keep = np.append(keep, indices[rank == i])
        i += 1
    keep = np.append(keep, indices[rank == i])
    return len(keep)


def _hpbandster(E: int, eta: int = 2):
    """Stage sizes and budgets of the authors' code when every configuration is its own
    NDS front (objective vectors on a dominance chain)."""
    min_budget, max_budget = math.ceil(0.2 * E), E
    max_SH_iter = -int(np.log(min_budget / max_budget) / np.log(eta)) + 1
    budgets = max_budget * np.power(eta, -np.linspace(max_SH_iter - 1, 0, max_SH_iter))
    out = []
    for iteration in range(max_SH_iter):
        s = max_SH_iter - 1 - (iteration % max_SH_iter)
        n0 = int(np.floor((max_SH_iter) / (s + 1)) * eta ** s)
        ns = [max(int(n0 * (eta ** (-i))), 1) for i in range(s + 1)]
        bs = [max(1, round(b)) for b in budgets[(-s - 1):]]
        sizes = [ns[0]]
        for stage in range(1, s + 1):
            sizes.append(_advance(np.arange(sizes[-1]), ns[stage]))
        out.append(list(zip(sizes, bs)))
    return out


@pytest.mark.parametrize("E", [12, 25, 50, 100, 200])
def test_mobohb_brackets_equal_hpbandster(E):
    space = SearchSpace(domains=tuple(CategoricalDomain(values=tuple(range(4))) for _ in range(6)))
    m = MOBOHB(space, 10**6, random.Random(0), max_epochs=E, num_initial_samples=0)
    gen = m._run()
    ours, batch, counter = [], next(gen), 0
    for _ in range(m.max_sh):
        bracket = []
        while True:
            bracket.append((len(batch), batch[0][1]))
            # strictly ordered objectives -> every configuration is its own NDS front
            objs = [(float(counter + j), float(counter + j)) for j in range(len(batch))]
            counter += len(batch)
            nxt = gen.send(objs)
            if nxt[0][1] <= batch[0][1]:  # a new bracket starts at a lower (or equal) budget
                batch = nxt
                break
            batch = nxt
        ours.append(bracket)
    assert ours == _hpbandster(E)


@pytest.mark.parametrize("b, expected", [(50, 12), (100, 25), (350, 50)])
def test_mobohb_initial_design_at_max_budget(b, expected):
    """`get_MOBOHB(init=True)`: the first iteration is num_initial_samples random
    configurations at the max budget; size by BB-4, min(50, floor(0.25 b))."""
    space = SearchSpace(domains=tuple(CategoricalDomain(values=tuple(range(4))) for _ in range(6)))
    m = MOBOHB(space, b, random.Random(0), max_epochs=25)
    first = next(m._run())
    assert len(first) == expected
    assert {e for _, e in first} == {25}
    assert len({g for g, _ in first}) == expected
