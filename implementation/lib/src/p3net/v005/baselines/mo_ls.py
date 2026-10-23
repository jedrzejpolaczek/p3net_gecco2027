"""MO-LS: random-restart local search with a random scalarisation (card `mo-ls.md`).

Den Ottelander et al., EMO 2021, §3, and their code (MacroNAS, `MO/LS.cpp`,
`loop = false`, `NewScalarization::RANDOM`):
L1 a random start; L2 lambda ~ U(0, 1); L3 one round over the variables in random
order, every value of a variable evaluated, the walk moving to the best one iff
the scalarisation strictly improves; L4 then a restart. Scalarisation:
minimise lambda * f1_n + (1 - lambda) * f2_n with min-max normalisation by the
points evaluated so far (L-1 b; the code uses benchmark-wide constants).
"""

from __future__ import annotations

from p3net.v005.common import is_valid, online_minmax, random_genotype
from p3net.v005.stepper import StepMethod


class MOLS(StepMethod):
    def __init__(self, space, budget, rng, *, observer=None):
        super().__init__(space, budget, rng, observer=observer)

    def config(self) -> dict:
        return {"loop": False, "scalarization": "random", "normalisation": "online min-max"}

    def _run(self):
        while True:
            start = random_genotype(self.space, self.rng)
            for _ in range(1000):  # L1: a new start (not an already evaluated one)
                if start not in self.cache:
                    break
                start = random_genotype(self.space, self.rng)
            lam = self.rng.random()  # L2
            cur = start
            f_cur = yield cur
            order = list(range(len(self.domains)))
            self.rng.shuffle(order)
            for i in order:  # L3: one round
                options = [(cur, f_cur)]
                for v in range(self.domains[i]):
                    if v == cur.values[i]:
                        continue
                    cand = cur.with_values(indices=[i], new_values=[v])
                    if is_valid(self.space, cand):
                        options.append((cand, (yield cand)))
                norm = online_minmax([o.objectives for o in self.cache.history()])

                def s(f):
                    a, b = norm(f)
                    return lam * a + (1.0 - lam) * b

                best = min(options[1:], key=lambda o: s(o[1]), default=None)
                if best is not None and s(best[1]) < s(f_cur):
                    cur, f_cur = best
            # L4: restart
