"""A9: hypervolume decomposition (cheap vs accurate end of the front) and duplicate share, v004.

HV in 2D (minimise f1 = error, f2 = cost) is the integral over f2 of (r1 - best f1 reachable at cost <= f2).
The f2 axis is split at t = median f2 of the frozen best-known front's points
(results/reference_fronts/<space>.json, A6): half of the front lies on each side. (The cost that halves the front's HV
falls beyond the front's f2 range on colorectal -- the rectangle of the best-f1 point dominates -- so it is not used.)
For each run:
  cheap    = HV of the run on f2 < t, divided by the same part of the frozen front;
  accurate = HV of the run on f2 >= t, divided likewise.
Both are in [0, 1] (up to the run beating the front, impossible on seeds 1-30); hv_rel is their mean weighted by
the front's HV in each part.

JAHS spaces only (HV-based metric); seeds 31-60 (confirmatory) and 1-30 separately.
Reads $V004_OUT/runs.pkl, runs_gp.pkl and per_run.csv (duplication_rate); writes hvdecomp.csv, prints medians.
"""
import json
import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(os.environ["V004_OUT"])
FRONTS = Path(__file__).resolve().parents[2] / "implementation/experiments/results/reference_fronts"
SPACES = ["jahs_bench_201", "jahs_bench_201_colorectal", "jahs_bench_201_fashion"]
ARMS = ["p3net_cascade", "random_search", "tpe", "sh_emoa", "bananas_mo", "oss_vizier", "nsga3", "smac3_parego",
        "botorch_qnehvi", "canonical_p3_scalar_fihc", "bartnik_p3", "przewozniczek_p3elympus", "p3net_s4_eager_mixing"]
GP = ("botorch_qnehvi", "botorch_qparego", "oss_vizier")


def staircase(points, ref):
    """Non-dominated points inside ref, f2 ascending: [(f2, f1)] with f1 strictly decreasing."""
    pts = sorted((f2, f1) for f1, f2 in points if f1 < ref[0] and f2 < ref[1])
    out, best = [], np.inf
    for f2, f1 in pts:
        if f1 < best:
            out.append((f2, f1))
            best = f1
    return out


def hv_between(stair, ref, lo, hi):
    """HV of the staircase restricted to f2 in [lo, hi)."""
    total = 0.0
    for i, (f2, f1) in enumerate(stair):
        nxt = stair[i + 1][0] if i + 1 < len(stair) else ref[1]
        a, b = max(f2, lo), min(nxt, hi)
        if b > a:
            total += (ref[0] - f1) * (b - a)
    return total


def split_point(stair, ref):
    """Cost t at which the front's HV is halved."""
    full = hv_between(stair, ref, -np.inf, np.inf)
    xs = sorted({f2 for f2, _ in stair} | {ref[1]})
    lo = xs[0]
    for x in xs[1:]:
        if hv_between(stair, ref, -np.inf, x) >= full / 2:
            a, b = lo, x  # bisection inside the segment
            for _ in range(60):
                m = (a + b) / 2
                a, b = (a, m) if hv_between(stair, ref, -np.inf, m) >= full / 2 else (m, b)
            return b
        lo = x
    return ref[1]


def main():
    recs = [r for r in pickle.load(open(HERE / "runs.pkl", "rb"))
            if "error" not in r and r["obj"] and r["method"] not in GP]
    recs += [r for r in pickle.load(open(HERE / "runs_gp.pkl", "rb"))
             if "error" not in r and r["obj"] and r["method"] in GP]
    info, rows = {}, []
    for s in SPACES:
        d = json.loads((FRONTS / f"{s}.json").read_text())
        ref = tuple(d["reference_point"])
        fs = staircase([tuple(p) for p in d["front"]], ref)
        t = float(np.median([f2 for f2, _ in fs]))
        fc, fa = hv_between(fs, ref, -np.inf, t), hv_between(fs, ref, t, np.inf)
        info[s] = dict(t=t, t_hv=split_point(fs, ref), front_cheap=fc, front_acc=fa, f2_range=(fs[0][0], fs[-1][0]))
        for r in recs:
            if r["space"] != s or r["method"] not in ARMS:
                continue
            st = staircase(r["obj"], ref)
            rows.append(dict(method=r["method"], space=s, budget=r["budget"], seed=r["seed"],
                             seeds="31-60" if r["seed"] > 30 else "1-30",
                             cheap=hv_between(st, ref, -np.inf, t) / fc, accurate=hv_between(st, ref, t, np.inf) / fa,
                             n_cheap=sum(f2 < t for _, f2 in r["obj"]), n=len(r["obj"])))
    df = pd.DataFrame(rows)
    df["share_cheap_evals"] = df.n_cheap / df.n
    dup = pd.read_csv(HERE / "per_run.csv", usecols=["method", "space", "budget", "seed", "dup"])
    df = df.merge(dup, on=["method", "space", "budget", "seed"], how="left")
    df.to_csv(HERE / "hvdecomp.csv", index=False)
    for s, i in info.items():
        w = i["front_cheap"] / (i["front_cheap"] + i["front_acc"])
        print(f"{s}: split t = {i['t']:.4f} (HV-half split {i['t_hv']:.4f}; front f2 range "
              f"{i['f2_range'][0]:.4f}-{i['f2_range'][1]:.4f}); cheap part = {w:.1%} of the front's HV")
    pd.set_option("display.width", 250)
    for seeds in ("31-60", "1-30"):
        g = df[df.seeds == seeds].groupby(["space", "budget", "method"])[
            ["cheap", "accurate", "share_cheap_evals", "dup"]].median().round(4)
        print(f"\n## seeds {seeds}: medians\n", g.to_string())
    # S5 minus each arm, per half, pooled over the JAHS cells (median over cells of median differences).
    for seeds in ("31-60", "1-30"):
        med = df[df.seeds == seeds].groupby(["space", "budget", "method"])[["cheap", "accurate"]].median()
        s5 = med.xs("p3net_cascade", level="method")
        diff = (s5 - med).dropna().groupby(level="method").agg(["median", "min", "max"]).round(4)
        print(f"\n## seeds {seeds}: S5 - arm (positive = S5 covers more), over JAHS cells\n", diff.to_string())
    allp = pd.read_csv(HERE / "per_run.csv", usecols=["method", "seeds", "dup"])
    print("\n## duplication_rate per method (all spaces, all budgets): median / max\n",
          allp.dropna().groupby("method").dup.agg(["median", "max", "count"]).sort_values("median").round(4).to_string())


if __name__ == "__main__":
    main()
