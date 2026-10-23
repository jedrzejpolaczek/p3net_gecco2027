"""Exploratory look at run root b4d25cac, following notes/plans/v004-preregistration.md:
frozen fronts from s1+s3+s7 seeds 1-30, two-sided Mann-Whitney U, Holm per cell, Cliff's delta
oriented so positive favours the reference arm. Not the paper's reporting code."""
import json, os, pickle, sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

ROOT = Path(__file__).resolve().parents[2] / "implementation" / "experiments"
# All intermediate files (pickles, CSVs) live here, outside the repo by default.
HERE = Path(os.environ["V004_OUT"])

COMPARISON = ["p3net", "p3_alone", "p3_alone_pop20", "p3_alone_pop40", "p3_absolute", "nsga_net",
              "nsganetv2", "sh_emoa", "mo_bohb", "tpe", "random_search", "mo_ls", "botorch_qnehvi",
              "botorch_qparego", "smac3_parego", "regularized_evolution_mo", "nsga3", "moead",
              "reinforce_mo", "bananas_mo", "oss_vizier", "bartnik_p3", "przewozniczek_p3elympus",
              "canonical_p3_scalar_fihc"]
FINAL_VARIANTS = ["p3_absolute_cascade", "p3net_bartnik", "p3net_bartnik_fihc", "p3net_elympus"]
MF = ["hyperband_mo", "asha_mo", "bohb_mo"]
S2 = ["p3net_s1_initial", "p3net_s2_analytic_cost", "p3net_s3_ridge", "p3net_s4_eager_mixing"]
S4 = ["p3net_cascade_inherited_cost", "p3net_cascade_f1_truncation", "p3net_cascade_grow_on_stall",
      "p3net_cascade_transient_donors", "p3net_cascade_threshold_permissive",
      "p3net_cascade_kappa1_thr0", "p3net_cascade_kappa1_thr1eps", "p3net_cascade_kappa1_thr2eps",
      "p3net_cascade_kappalog_thr0", "p3net_cascade_kappalog_thr1eps", "p3net_cascade_kappalog_thr2eps",
      "p3net_cascade_kappa2log_thr1eps", "p3net_cascade_kappa2log_thr2eps",
      "p3net_cascade_kappainf_thr0", "p3net_cascade_kappainf_thr1eps", "p3net_cascade_kappainf_thr2eps"]
REF = "p3net_cascade"
ORACLE_SPACES = {"nas_hpo_bench_ii", "fcnet_protein_structure", "fcnet_naval_propulsion",
                 "fcnet_parkinsons_telemonitoring", "fcnet_slice_localization"}
FRONT_METHODS = set(COMPARISON) | {REF} | set(FINAL_VARIANTS) | set(MF)


def nd2(points):
    pts = sorted(set(points))
    out, best = [], float("inf")
    for p in pts:
        if p[1] < best:
            out.append(p); best = p[1]
    return out


def hv2(points, ref):
    front = [p for p in nd2(points) if p[0] < ref[0] and p[1] < ref[1]]
    total, prev_f2 = 0.0, ref[1]
    for f1, f2 in front:  # f1 ascending, f2 descending
        total += (ref[0] - f1) * (prev_f2 - f2)
        prev_f2 = f2
    return total


def igd_plus_norm(approx, oracle):
    o = np.asarray(oracle, float); a = np.asarray(nd2(approx), float)
    lo, hi = o.min(0), o.max(0); span = np.where(hi > lo, hi - lo, 1.0)
    o = (o - lo) / span; a = (a - lo) / span
    d = np.maximum(a[None, :, :] - o[:, None, :], 0.0)
    return float(np.sqrt((d ** 2).sum(-1)).min(1).mean())


def cliffs(a, b):
    a = np.asarray(a); b = np.asarray(b)
    return float((np.sign(a[:, None] - b[None, :])).mean())


def holm(ps):
    ps = np.asarray(ps, float); m = len(ps); order = np.argsort(ps)
    adj = np.empty(m); running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * ps[i])); adj[i] = running
    return adj


def main():
    recs = pickle.load(open(HERE / "runs.pkl", "rb"))
    bad = [r for r in recs if "error" in r]
    # The GP arms run in a separate root (v004-gp-small); the few leftovers here are aborted runs.
    gp = ("botorch_qnehvi", "botorch_qparego", "oss_vizier")
    recs = [r for r in recs if "error" not in r and r["obj"] and r["method"] not in gp]
    if (HERE / "runs_gp.pkl").exists():
        gp_recs = pickle.load(open(HERE / "runs_gp.pkl", "rb"))
        bad += [r for r in gp_recs if "error" in r]
        gp_recs = [r for r in gp_recs if "error" not in r and r["obj"] and r["method"] in gp]
        print("gp-small runs:", len(gp_recs))
        recs += gp_recs
    print("loaded", len(recs), "runs;", len(bad), "unreadable")

    # Frozen fronts (prereg section 3).
    oracle = {}
    for s in ORACLE_SPACES:
        p = ROOT / "results/reference_fronts" / f"oracle__{s}.json"
        d = json.loads(p.read_text())
        oracle[s] = [tuple(x) for x in (d["front"] if isinstance(d, dict) else d)]
    pool = defaultdict(list)
    for r in recs:
        if r["space"] in ORACLE_SPACES or r["seed"] > 30:
            continue
        if r["space"] == "nas_bench_201" or r["method"] in FRONT_METHODS:
            pool[r["space"]].extend(r["obj"])
    fronts = {s: (nd2(pts), tuple(np.max(np.asarray(pts), 0) + 1e-6)) for s, pts in pool.items()}
    json.dump({s: {"front_size": len(f), "ref": list(rp), "pooled_points": len(pool[s])}
               for s, (f, rp) in fronts.items()}, open(HERE / "fronts_info.json", "w"), indent=1)

    rows = []
    for r in recs:
        s = r["space"]
        if s in oracle:
            metric, val = "igd_plus", igd_plus_norm(r["obj"], oracle[s])
        else:
            f, rp = fronts[s]
            metric, val = "hv_rel", hv2(r["obj"], rp) / hv2(f, rp)
        d = r["diag"]
        rows.append(dict(method=r["method"], space=s, budget=r["budget"], seed=r["seed"],
                         seeds="31-60" if r["seed"] > 30 else "1-30", metric=metric, value=val,
                         evals=r["evals"], n_hist=len(r["obj"]),
                         bootstrap=d.get("bootstrap_proposals"), mixing=d.get("mixing_proposals"),
                         dup=d.get("duplication_rate"), wall=d.get("res_wall_seconds"),
                         cpu=d.get("res_cpu_seconds"), opt=d.get("res_optimizer_seconds"),
                         rss=d.get("res_process_peak_rss_mb"),
                         simtrain=d.get("res_simulated_training_seconds")))
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "per_run.csv", index=False)

    # Per-run diagnostics that do not fit the flat table.
    diag = {(r["method"], r["space"], r["budget"], r["seed"]): r["diag"] for r in recs
            if r["method"].startswith("p3") or r["method"] in ("bartnik_p3", "przewozniczek_p3elympus",
                                                               "canonical_p3_scalar_fihc")}
    pickle.dump(diag, open(HERE / "diag.pkl", "wb"))

    # Comparisons.
    better_sign = {"hv_rel": 1.0, "igd_plus": -1.0}
    out = []

    def family(name, ref, arms, seeds, spaces=None):
        sub = df[df.seeds == seeds]
        for (s, b), cell in sub.groupby(["space", "budget"]):
            if spaces and s not in spaces:
                continue
            rv = cell[cell.method == ref].value.values
            if len(rv) < 2:
                continue
            res = []
            for a in arms:
                av = cell[cell.method == a].value.values
                if len(av) < 2 or a == ref:
                    continue
                p = mannwhitneyu(rv, av, alternative="two-sided").pvalue
                sg = better_sign[cell.metric.iloc[0]]
                res.append(dict(family=name, seeds=seeds, space=s, budget=b, ref=ref, arm=a,
                                n_ref=len(rv), n_arm=len(av), med_ref=np.median(rv), med_arm=np.median(av),
                                p=p, delta=sg * cliffs(rv, av)))
            if res:
                for x, ap in zip(res, holm([x["p"] for x in res])):
                    x["adj_p"] = ap; x["sig"] = ap < 0.05; out.append(x)

    for seeds in ("1-30", "31-60"):
        family("Q1", REF, COMPARISON, seeds)
        family("Q4", REF, FINAL_VARIANTS, seeds)
        family("Q7", REF, MF, seeds)
        family("vsRS", "random_search", sorted(set(df.method) - {"random_search"}), seeds)
    family("Q3", REF, S4, "1-30")
    family("NB201", REF, ["p3net", "p3net_bartnik", "p3net_elympus", "bartnik_p3", "przewozniczek_p3elympus",
                          "canonical_p3_scalar_fihc", "mo_ls", "random_search"], "1-30", {"nas_bench_201"})
    family("NB201_vsRS", "random_search", ["p3net", REF, "p3net_bartnik", "p3net_elympus", "bartnik_p3",
                                           "przewozniczek_p3elympus", "canonical_p3_scalar_fihc", "mo_ls"],
           "1-30", {"nas_bench_201"})
    # Q2: stage transitions, one family per cell.
    sub = df[df.seeds == "1-30"]
    trans = [("p3net_s1_initial", "p3net_s2_analytic_cost"), ("p3net_s2_analytic_cost", "p3net_s3_ridge"),
             ("p3net_s3_ridge", "p3net"), ("p3net", "p3net_s4_eager_mixing"), ("p3net", REF)]
    for (s, b), cell in sub.groupby(["space", "budget"]):
        res = []
        for a, bb in trans:
            av = cell[cell.method == bb].value.values; rv = cell[cell.method == a].value.values
            if len(av) < 2 or len(rv) < 2:
                continue
            sg = better_sign[cell.metric.iloc[0]]
            res.append(dict(family="Q2", seeds="1-30", space=s, budget=b, ref=a, arm=bb, n_ref=len(rv),
                            n_arm=len(av), med_ref=np.median(rv), med_arm=np.median(av),
                            p=mannwhitneyu(av, rv, alternative="two-sided").pvalue, delta=sg * cliffs(av, rv)))
        for x, ap in zip(res, holm([x["p"] for x in res])):
            x["adj_p"] = ap; x["sig"] = ap < 0.05; out.append(x)
    cmp = pd.DataFrame(out)
    cmp.to_csv(HERE / "comparisons.csv", index=False)

    summ = df.groupby(["seeds", "space", "budget", "method"]).value.agg(
        n="count", median="median", q1=lambda v: v.quantile(.25), q3=lambda v: v.quantile(.75)).reset_index()
    summ.to_csv(HERE / "summary.csv", index=False)
    print("per_run", df.shape, "comparisons", cmp.shape)


if __name__ == "__main__":
    main()
