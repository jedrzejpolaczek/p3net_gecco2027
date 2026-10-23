"""Decompose S5 -> p3net_elympus into ladder steps; surrogate accuracy; f1/f2 profile."""
import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr

# All intermediate files (pickles, CSVs) live here, outside the repo by default.
HERE = Path(os.environ["V004_OUT"])
LADDER = ["p3net_cascade", "p3net_bartnik", "p3net_bartnik_fihc", "p3net_elympus"]
NAMES = {"p3net_cascade": "S5", "p3net_bartnik": "RF", "p3net_bartnik_fihc": "RF+FIHC", "p3net_elympus": "RF+eLy"}


def grp(s):
    if s.startswith("fcnet"):
        return "FCNet"
    if s == "nas_bench_201":
        return "NB201"
    if s == "nas_hpo_bench_ii":
        return "NAS-HPO"
    return "JAHS"


def holm(ps):
    ps = np.asarray(ps); order = np.argsort(ps); adj = np.empty(len(ps)); run = 0
    for r, i in enumerate(order):
        run = max(run, min(1, (len(ps) - r) * ps[i])); adj[i] = run
    return adj


def cliffs(a, b):
    return float(np.sign(np.subtract.outer(a, b)).mean())


df = pd.read_csv(HERE / "per_run.csv")
# exploratory seeds for FCNet/NB201, held-out for primary
use = df[((df.seeds == "31-60") & ~df.space.str.startswith("fcnet") & (df.space != "nas_bench_201"))
         | ((df.seeds == "1-30") & (df.space.str.startswith("fcnet") | (df.space == "nas_bench_201")))]
use = use[use.method.isin(LADDER)]
steps = [("p3net_cascade", "p3net_bartnik"), ("p3net_bartnik", "p3net_bartnik_fihc"),
         ("p3net_bartnik_fihc", "p3net_elympus"), ("p3net_cascade", "p3net_elympus")]
rows = []
for (s, b), cell in use.groupby(["space", "budget"]):
    sign = -1 if cell.metric.iloc[0] == "igd_plus" else 1
    res = []
    for a, c in steps:
        va = cell[cell.method == a].value.values; vc = cell[cell.method == c].value.values
        if len(va) < 2 or len(vc) < 2:
            continue
        res.append(dict(space=s, g=grp(s), budget=b, step=f"{NAMES[a]}->{NAMES[c]}",
                        p=mannwhitneyu(vc, va).pvalue, d=sign * cliffs(vc, va)))
    for r, ap in zip(res, holm([r["p"] for r in res])):
        r["sig"] = ap < 0.05; rows.append(r)
L = pd.DataFrame(rows)
L["res"] = np.where(L.sig, np.where(L.d > 0, "lepiej", "gorzej"), "=")
print("A. Kroki drabinki (późniejszy względem wcześniejszego), liczba komórek")
print(L.groupby(["step", "g", "res"]).size().unstack(fill_value=0).to_string())
print("\nA2. mediana Cliff delta kroku")
print(L.pivot_table(index="step", columns="g", values="d", aggfunc="median").round(2).to_string())

# B. surrogate accuracy, seeds 1-30, budget 350
diag = pickle.load(open(HERE / "diag.pkl", "rb"))
acc = []
for (m, s, b, seed), d in diag.items():
    if m not in LADDER or b != 350 or seed > 30 or not d.get("sq_log"):
        continue
    arr = np.array([(p, t) for _, p, t in d["sq_log"] if p is not None and t is not None], float)
    if len(arr) < 5:
        continue
    rho = spearmanr(arr[:, 0], arr[:, 1]).statistic
    pos = arr[:, 0] >= 0
    prec = (arr[pos, 1] > 0).mean() if pos.any() else np.nan
    base = (arr[:, 1] > 0).mean()
    acc.append(dict(m=NAMES[m], g=grp(s), rho=rho, prec=prec, base=base))
A = pd.DataFrame(acc)
print("\nB. Jakość surogatu (budżet 350, seedy 1-30): Spearman pred vs true, precyzja akceptacji, base rate")
print(A.groupby(["g", "m"])[["rho", "prec", "base"]].median().round(3).unstack("m").to_string())

# C. f1/f2 profile of evaluated points
recs = pickle.load(open(HERE / "runs.pkl", "rb"))
prof = []
for r in recs:
    if r["method"] not in LADDER or r["budget"] != 350:
        continue
    o = np.asarray(r["obj"], float)
    prof.append(dict(m=NAMES[r["method"]], space=r["space"], g=grp(r["space"]),
                     best_f1=o[:, 0].min(), med_f2=np.median(o[:, 1])))
P = pd.DataFrame(prof)
ref = P[P.m == "S5"].groupby("space")[["best_f1", "med_f2"]].median()
P = P.join(ref, on="space", rsuffix="_S5")
P["best_f1_rel"] = P.best_f1 / P.best_f1_S5; P["med_f2_rel"] = P.med_f2 / P.med_f2_S5
print("\nC. Budżet 350: najlepsze f1 i mediana f2 ocenionych punktów, względem S5 (=1.0)")
print(P.groupby(["space", "m"])[["best_f1_rel", "med_f2_rel"]].median().round(3).unstack("m").to_string())
