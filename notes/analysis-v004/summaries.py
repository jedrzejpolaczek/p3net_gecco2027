"""Summary tables printed during the first exploratory pass over v004.

Reads per_run.csv, comparisons.csv and timing.csv from $V004_OUT (written by analyze.py and timing.py).
Space groups: primary = JAHS-Bench-201 x3 + NAS-HPO-Bench-II; FCNet = 4 tasks; NB201 = architecture-only.
Confirmatory = seeds 31-60 on primary; FCNet and NB201 have seeds 1-30 only (exploratory / descriptive).
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(os.environ["V004_OUT"])
pd.set_option("display.width", 250, "display.max_rows", 3000, "display.max_columns", 40)

df = pd.read_csv(OUT / "per_run.csv")
c = pd.read_csv(OUT / "comparisons.csv")
timing = pd.read_csv(OUT / "timing.csv") if (OUT / "timing.csv").exists() else None


def group(space):
    if space == "nas_bench_201":
        return "NB201"
    return "FCNet" if space.startswith("fcnet") else "primary"


c["grp"] = c.space.map(group)
DESIGN = [m for m in df.method.unique() if m.startswith("p3net_s") or m.startswith("p3net_cascade_")]


def outcome_counts(x):
    """'+' = reference significantly better, '-' = significantly worse, '0' = no rejection; dpos = cells with delta > 0."""
    x = x.assign(res=np.where(x.sig, np.where(x.delta > 0, "+", "-"), "0"))
    t = x.groupby(["arm", "res"]).size().unstack(fill_value=0)
    for k in "+-0":
        if k not in t:
            t[k] = 0
    t["dpos"] = x.groupby("arm").delta.apply(lambda d: (d > 0).sum())
    t["n"] = x.groupby("arm").size()
    return t[["+", "-", "0", "dpos", "n"]].sort_values(["-", "+"])


print("### Q1/Q4/Q7: reference S5 (p3net_cascade)")
for fam in ["Q1", "Q4", "Q7"]:
    for seeds, g in [("1-30", "primary"), ("31-60", "primary"), ("1-30", "FCNet")]:
        x = c[(c.family == fam) & (c.seeds == seeds) & (c.grp == g)]
        if len(x):
            print(f"\n== {fam} seeds {seeds} {g}")
            print(outcome_counts(x).to_string())

print("\n### Every arm vs random search ('beats RS' = arm significantly better than RS)")
for seeds, g in [("1-30", "primary"), ("31-60", "primary"), ("1-30", "FCNet")]:
    x = c[(c.family == "vsRS") & (c.seeds == seeds) & (c.grp == g)].copy()
    x["res"] = np.where(x.sig, np.where(x.delta < 0, "beats RS", "worse than RS"), "no difference")
    print(f"\n== seeds {seeds} {g}")
    print(x.groupby(["arm", "res"]).size().unstack(fill_value=0).to_string())
x = c[c.family == "NB201_vsRS"][["budget", "arm", "med_ref", "med_arm", "adj_p", "delta"]]
print("\n== NB201 vs RS (descriptive)\n" + x.to_string(index=False))

print("\n### Q2 design path (delta > 0: later stage better) and Q3 design defence (+ = S5 better)")
for fam in ["Q2", "Q3"]:
    x = c[c.family == fam].copy()
    x["res"] = np.where(x.sig, np.where(x.delta > 0, "+", "-"), "0")
    keys = ["grp", "ref", "arm", "res"] if fam == "Q2" else ["grp", "arm", "res"]
    print(f"\n== {fam}\n" + x.groupby(keys).size().unstack(fill_value=0).to_string())


def ranks(sub, budgets=None):
    """Mean rank of each arm's per-cell median (1 = best), over the cells in `sub`."""
    sub = sub[~sub.method.isin(DESIGN)]
    if budgets:
        sub = sub[sub.budget.isin(budgets)]
    med = sub.groupby(["space", "budget", "method"]).value.median().reset_index()
    # IGD+ (NAS-HPO-II, FCNet) is minimised, relative HV (JAHS, NB201) maximised.
    med["s"] = np.where(med.space.str.contains("nas_hpo|fcnet"), med.value, -med.value)
    med["rank"] = med.groupby(["space", "budget"]).s.rank()
    return med.groupby("method")["rank"].mean().round(1), med.groupby(["space", "budget"]).method.nunique().max()


print("\n### Mean rank by problem type (all budgets; GP arms only have 50/100 and are ranked separately below)")
for label, budgets in [("all budgets", None), ("budgets 50 and 100 only", [50, 100])]:
    cols = {}
    for name, sub in [("JAHS", df[(df.seeds == "31-60") & df.space.str.startswith("jahs")]),
                      ("NAS-HPO", df[(df.seeds == "31-60") & (df.space == "nas_hpo_bench_ii")]),
                      ("FCNet", df[df.space.str.startswith("fcnet")]),
                      ("NB201", df[df.space == "nas_bench_201"])]:
        r, n = ranks(sub, budgets)
        cols[f"{name}(n={n})"] = r
    print(f"\n== {label}\n" + pd.DataFrame(cols).sort_values(list(cols)[0]).to_string())

print("\n### Bootstrap share (median, seeds 1-30): P3Net engines")
d = df[df.method.isin(["p3net", "p3net_cascade", "p3_absolute_cascade", "p3_absolute"]) & (df.seeds == "1-30")].copy()
d["share"] = d.bootstrap / (d.bootstrap + d.mixing)
print(d.pivot_table(index=["space", "method"], columns="budget", values="share", aggfunc="median").round(3).to_string())

if timing is not None:
    print("\n### Quality vs cost relative to S5 per space (Q1+Q7; wall time: s9 for primary, grid medians at b=350 for FCNet)")
    q = c[c.family.isin(["Q1", "Q7"]) & (((c.seeds == "31-60") & (c.grp == "primary")) | ((c.seeds == "1-30") & (c.grp == "FCNet")))].copy()
    q["w"] = (q.sig & (q.delta > 0)).astype(int)
    q["l"] = (q.sig & (q.delta < 0)).astype(int)
    g = q.groupby(["space", "arm"]).agg(W=("w", "sum"), L=("l", "sum")).reset_index()
    tm = timing.rename(columns={"wall_seconds": "wall"})[["method", "space", "wall"]]
    grid = df[(df.budget == 350) & df.space.str.startswith("fcnet")].groupby(["method", "space"]).wall.median().reset_index()
    cost = pd.concat([tm, grid]).rename(columns={"method": "arm"})
    s5 = cost[cost.arm == "p3net_cascade"].set_index("space").wall
    g = g.merge(cost, on=["space", "arm"], how="left")
    g["x"] = g.wall / g.space.map(s5)
    fmt = lambda t: ", ".join(f"{r.arm}({r.W}+/{r.L}-, x{r.x:.1f})" for r in t.sort_values("x").itertuples())
    for s, h in g.groupby("space"):
        print(f"\n## {s}")
        print(" S5 not worse and faster:", fmt(h[(h.L == 0) & (h.x > 1)]))
        print(" arm better but slower:  ", fmt(h[(h.L > 0) & (h.x > 1)]))
        print(" arm better and faster:  ", fmt(h[(h.L > 0) & (h.x <= 1)]))
