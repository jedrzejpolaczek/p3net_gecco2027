"""Diagnostic for the P3-eLyMPuS level-2 test: our evaluation cost split by phase, to set
against the reference's own breakdown (`OMstats_cost`, `FIHCcost_FFEregular`,
`FFEmissLinkDetection`, `FFEdepDiscovery` in IslandGA's `*_out.txt`).

Phases: init (random solution), mix (P3 mixing), pair (pair computation for a context
with no list entry), verify (re-computation of an existing entry), rll (RecursiveLL).
Each request is attributed to the innermost phase; counted as unique evaluations and as
all requests (cache hits included) and, for pair/verify, without the request for the
solution itself (the reference holds its value).

  python elympus_cost_breakdown.py --problem DIR --runs 200 --out FILE
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from elympus_vs_islandga import make_f, read_problem  # noqa: E402

PHASES = ("init", "mix", "pair", "verify", "rll")


def _one(args) -> dict:
    problem_dir, seed = args
    from p3net.harness.runner import Observation, RunState
    from p3net.problem.genotype import CategoricalDomain, SearchSpace
    from p3net.v005 import elympus as el

    tag: list = [None]

    def tagged(gen, name):
        msg = None
        try:
            g = next(gen)
            while True:
                if tag[0] is None:
                    tag[0] = name
                msg = yield g
                g = gen.send(msg)
        except StopIteration as stop:
            return stop.value

    orig_pc, orig_rll, orig_compute = el.ELyMPuS._pc_gen, el.ELyMPuS._rll_gen, el.ELyMPuS._compute
    orig_mix = el.P3ELyMPuS._mix_real

    def pc(self, x, var, value, verify):
        name = "pair" if self._find(tuple(x.values), var) is None or not verify else "verify"
        return (yield from tagged(orig_pc(self, x, var, value, verify), name))

    def rll(self, x1, x2, var):
        return (yield from tagged(orig_rll(self, x1, x2, var), "rll"))

    def compute(self, x, var):
        gen, msg = orig_compute(self, x, var), None
        try:
            g = next(gen)
            while True:
                if tuple(g.values) == tuple(x):
                    selfreq[0] = True
                msg = yield g
                g = gen.send(msg)
        except StopIteration as stop:
            return stop.value

    def mix(self, *a):
        return (yield from tagged(orig_mix(self, *a), "mix"))

    el.ELyMPuS._pc_gen, el.ELyMPuS._rll_gen, el.ELyMPuS._compute = pc, rll, compute
    el.P3ELyMPuS._mix_real = mix
    selfreq = [False]

    p = read_problem(Path(problem_dir))
    F, opt = make_f(p)
    space = SearchSpace(domains=tuple(CategoricalDomain(values=(0, 1)) for _ in range(p["n"])))
    m = el.P3ELyMPuS(space, 10_000_000, random.Random(seed))
    unique = {k: 0 for k in PHASES}
    requests = {k: 0 for k in PHASES}
    no_self = {k: 0 for k in PHASES}
    get = m.cache.get

    def counting_get(g):
        r = get(g)
        if r is not None:
            ph = tag[0] or "init"
            requests[ph] += 1
            if not selfreq[0]:
                no_self[ph] += 1
            tag[0], selfreq[0] = None, False
        return r

    m.cache.get = counting_get
    state = RunState()
    while True:
        props = m.propose(state)
        if not props:
            break
        ph = tag[0] or "init"
        unique[ph] += 1
        requests[ph] += 1
        no_self[ph] += 1
        tag[0], selfreq[0] = None, False
        g = props[0]
        Fv = F(g.values)
        cost = opt + 1.0 - Fv
        state.evaluations_used += 1
        m.update(state, [Observation(genotype=g, objectives=(cost, cost))])
        if Fv >= opt:
            break
    return {"seed": seed, "unique": unique, "requests": requests, "no_self": no_self}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", required=True)
    ap.add_argument("--runs", type=int, default=200)
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with ProcessPoolExecutor(a.workers) as ex:
        res = list(ex.map(_one, [(a.problem, s) for s in range(a.runs)]))
    Path(a.out).write_text(json.dumps(res))
    for kind in ("unique", "requests", "no_self"):
        print(kind, {k: float(np.median([r[kind][k] for r in res])) for k in PHASES},
              "total", float(np.median([sum(r[kind].values()) for r in res])))


if __name__ == "__main__":
    main()
