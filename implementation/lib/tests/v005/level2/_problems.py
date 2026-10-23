"""Shared level-2 problems (pure Python: also imported by reference runners that live in
old environments, e.g. vendor/nsganet-env with Python 3.8)."""

from __future__ import annotations

import random

PROBLEMS = {
    # additive, 10 variables x 8 values (the MOEA/D level-2 problem)
    "additive": {"domains": [8] * 10, "ref": (11.0, 14.0)},
    # k-ary trap (f1, 4 blocks of 3 variables with 3 values; optimum all 2) vs sum of values (f2)
    "trap": {"domains": [3] * 12, "ref": (13.0, 25.0)},
}


def objective(name: str):
    if name == "additive":
        rng = random.Random(0)
        domains = PROBLEMS[name]["domains"]
        w1 = [[rng.random() for _ in range(k)] for k in domains]
        w2 = [[1.0 - x + 0.3 * rng.random() for x in row] for row in w1]

        def f(x):
            x = [int(v) for v in x]
            return sum(w1[i][v] for i, v in enumerate(x)), sum(w2[i][v] for i, v in enumerate(x))

        return f
    if name == "trap":
        def f(x):
            x = [int(v) for v in x]
            f1 = 0.0
            for b in range(4):
                u = x[3 * b:3 * b + 3]
                f1 += 0.0 if all(v == 2 for v in u) else 1.0 + 0.1 * sum(u)  # deceptive towards 0
            return f1 + 1.0, float(sum(x)) + 1.0

        return f
    raise KeyError(name)


def hv(points, ref):
    pts = sorted(p for p in points if p[0] < ref[0] and p[1] < ref[1])
    total, best = 0.0, ref[1]
    for x, y in pts:
        if y < best:
            total += (ref[0] - x) * (best - y)
            best = y
    return total
