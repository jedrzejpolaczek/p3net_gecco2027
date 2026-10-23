"""Level 2 (v005-level2-criteria.md, "MO-DSA (Bartnik) vs SAGOMEA"): our MO-DSA on the
duplicated objective vs SAGOMEA (docker image `p3net-sagomea:1`, see `sagomea/Dockerfile`)
on the concatenated trap k = 5, n = 50, 500 distinct evaluations, best value per run.

  python modsa_vs_sagomea.py ours --runs 100 --workers 8 --out FILE
  python modsa_vs_sagomea.py compare OURS_FILE SAGOMEA_TXT   (lines "seed best n_evals")
"""

from __future__ import annotations

import argparse
import json
import random
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy import stats

N, K, BUDGET = 50, 5, 500
TABLE = [4, 3, 2, 1, 0, 5]


def trap(x) -> float:
    return float(sum(TABLE[sum(x[i:i + K])] for i in range(0, N, K)))


def _one(args) -> dict:
    seed, gate = args
    from p3net.harness.runner import Observation, RunState
    from p3net.problem.genotype import CategoricalDomain, SearchSpace
    from p3net.v005.bartnik import MODSA

    space = SearchSpace(domains=tuple(CategoricalDomain(values=(0, 1)) for _ in range(N)))
    m = MODSA(space, BUDGET, random.Random(seed), gate=gate)
    state, best, t0 = RunState(), -np.inf, time.perf_counter()
    while state.evaluations_used < BUDGET:
        props = m.propose(state)
        if not props:
            break
        obs = []
        for g in props:
            v = trap(g.values)
            best = max(best, v)
            c = float(N + 1) - v  # minimised, positive
            obs.append(Observation(genotype=g, objectives=(c, c)))
        state.evaluations_used += len(obs)
        m.update(state, obs)
    return {"seed": seed, "best": best, "evals": state.evaluations_used, "seconds": time.perf_counter() - t0,
            "stop_reason": getattr(m, "stop_reason", None)}


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("ours")
    o.add_argument("--runs", type=int, default=100)
    o.add_argument("--workers", type=int, default=8)
    o.add_argument("--out", required=True)
    o.add_argument("--gate", default="quantile", choices=["quantile", "elitist"])
    c = sub.add_parser("compare")
    c.add_argument("ours")
    c.add_argument("ref")
    a = ap.parse_args()
    if a.cmd == "ours":
        with ProcessPoolExecutor(a.workers) as ex:
            res = list(ex.map(_one, [(s, a.gate) for s in range(1, a.runs + 1)]))
        Path(a.out).write_text(json.dumps(res))
        print("median best", np.median([r["best"] for r in res]), "median s", np.median([r["seconds"] for r in res]))
        return
    ours = np.array([r["best"] for r in json.loads(Path(a.ours).read_text())])
    rows = [line.split() for line in Path(a.ref).read_text().splitlines()]
    ref = np.array([float(r[1]) for r in rows if len(r) == 3 and r[0].isdigit()])  # skip the shell's segfault notices
    med = float(np.median(ref))
    margin = 0.02 * med
    p_low = stats.ttest_ind(ours + margin, ref, equal_var=False, alternative="greater").pvalue
    p_high = stats.ttest_ind(ours - margin, ref, equal_var=False, alternative="less").pvalue
    print(json.dumps({"ours_median": float(np.median(ours)), "ours_mean": float(ours.mean()), "ref_median": med,
                      "ref_mean": float(ref.mean()), "n_ours": len(ours), "n_ref": len(ref),
                      "within_2pct": bool(abs(np.median(ours) - med) <= margin), "tost_p": float(max(p_low, p_high)),
                      "mwu_p": float(stats.mannwhitneyu(ours, ref).pvalue)}, indent=1))


if __name__ == "__main__":
    main()
