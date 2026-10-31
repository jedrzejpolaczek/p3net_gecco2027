"""K6, K7, K9 and the other descriptive analyses of pre-registration §5 (no tests).

Choices not fixed by the pre-registration text are marked CHOICE and listed in
notes/plans/v005-preregistration.md §5 (approved with the scripts, task 5a).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from analysis_v005 import spec
from analysis_v005.fronts import nondominated
from analysis_v005.metrics import hv_between, normalise_jahs
from analysis_v005.per_run import Scorer, points, records

# ---------------------------------------------------------------------------------------------- anytime


def _anytime_main(rec, score):
    """Metric after every evaluation; recomputed only when the non-dominated set changes."""
    space, front, values, last = rec["search_space"], [], [], float("nan")
    for h in rec["history"]:
        p = tuple(map(float, h["objectives"]))
        if not any(q[0] <= p[0] and q[1] <= p[1] for q in front):
            front = nondominated(front + [p])
            last = score(space, front)
        values.append(last)
    return values


def _anytime_mf(rec, score):
    """Metric at every 1/MF_GRID of the cost budget: front of the configurations trained to E so far."""
    space, E = rec["search_space"], spec.SPACES[rec["search_space"]][2]
    q = rec["diagnostics"].get("fidelity_queries", [])
    cost = np.cumsum([x["cost"] for x in q])
    grid = np.linspace(rec["budget"] / spec.MF_GRID, rec["budget"], spec.MF_GRID)
    out, front, j, last = [], [], 0, float("nan")
    for g in grid:
        changed = False
        while j < len(q) and cost[j] <= g + 1e-9:
            if q[j]["epochs"] == E:
                p = tuple(map(float, q[j]["objectives"]))
                if not any(f[0] <= p[0] and f[1] <= p[1] for f in front):
                    front, changed = nondominated(front + [p]), True
            j += 1
        if changed:
            last = score(space, front)
        out.append(last)
    return out


def _cum_training(rec):
    em = rec.get("evaluation_metrics", {})
    if "fidelity" in em:
        return np.cumsum([x if x is not None else np.nan for x in em["fidelity"]])
    return np.cumsum([r.get("training_seconds", np.nan) for r in em.get("history", [])]) if em else None


def anytime_and_targets(roots, final: pd.DataFrame):
    """K6. Returns (median curves, per-run cost to target).

    Cost to target (§5.2): first evaluation (MF: cost in full-evaluation equivalents) and cumulative
    simulated training seconds at which the run reaches the target. CHOICE: target for HV = q * best,
    for IGD+ = best / q, with best = the best median final value of any arm in the cell."""
    score = Scorer()
    best = {}
    for (space, budget), cell in final.groupby(["space", "budget"]):
        med = cell.groupby("method").value.median()
        best[(space, budget)] = med.max() if spec.SPACES[space][1] == "hv" else med.min()
    curves, targets = [], []
    for rec in records(roots):
        space, budget, method = rec["search_space"], rec["budget"], rec["method"]
        if space not in spec.SPACES:
            continue
        mf = "fidelity_queries" in rec.get("diagnostics", {})
        values = _anytime_mf(rec, score) if mf else _anytime_main(rec, score)
        curves.append((method, space, budget, rec["seed"], mf, values))
        b = best.get((space, budget))
        hv = spec.SPACES[space][1] == "hv"
        cum = _cum_training(rec)
        for q in spec.TARGETS:
            thr = None if b is None else (q * b if hv else b / q)
            hit = next((i for i, v in enumerate(values) if thr is not None and v == v
                        and (v >= thr if hv else v <= thr)), None)
            row = dict(method=method, space=space, budget=budget, seed=rec["seed"], target=q, threshold=thr,
                       reached=hit is not None)
            if hit is None:
                row.update(evaluations=np.nan, cost=np.nan, training_seconds=np.nan)
            elif mf:
                c = (hit + 1) * budget / spec.MF_GRID
                qc = np.cumsum([x["cost"] for x in rec["diagnostics"]["fidelity_queries"]])
                k = int(np.searchsorted(qc, c + 1e-9, side="right")) - 1
                row.update(evaluations=np.nan, cost=c,
                           training_seconds=float(cum[k]) if cum is not None and k >= 0 else np.nan)
            else:
                row.update(evaluations=hit + 1, cost=hit + 1,
                           training_seconds=float(cum[hit]) if cum is not None and len(cum) > hit else np.nan)
            targets.append(row)
    rows = []
    for (method, space, budget, mf), grp in pd.DataFrame(
            curves, columns=["method", "space", "budget", "seed", "mf", "v"]).groupby(
            ["method", "space", "budget", "mf"]):
        n = max(len(v) for v in grp.v)
        arr = np.full((len(grp), n), np.nan)
        for i, v in enumerate(grp.v):
            arr[i, :len(v)] = v
        with np.errstate(all="ignore"):
            med = np.nanmedian(arr, axis=0)
        for i, m in enumerate(med):
            rows.append(dict(method=method, space=space, budget=budget, axis="cost" if mf else "evaluations",
                             x=(i + 1) * budget / spec.MF_GRID if mf else i + 1, median=m, n_runs=len(grp)))
    return pd.DataFrame(rows), pd.DataFrame(targets)


# ------------------------------------------------------------------------------------------------ costs

COST_COLUMNS = ["method_wall_seconds", "wall_seconds", "peak_memory_process_mb", "peak_memory_server_mb",
                "peak_memory_gpu_mb", "simulated_training_seconds"]


def costs(df: pd.DataFrame) -> pd.DataFrame:
    """K7 (§5.3): medians per arm and cell; memory scope / method stated per row."""
    g = df.groupby(["method", "space", "budget"])
    out = g[COST_COLUMNS].median()
    out["n_runs"] = g.size()
    out["process_scope"] = g.peak_memory_process_scope.agg(lambda s: ",".join(sorted(set(map(str, s.dropna())))))
    out["server_method"] = g.peak_memory_server_method.agg(lambda s: ",".join(sorted(set(map(str, s.dropna())))))
    return out.reset_index()


# ---------------------------------------------------------------------------------- HV decomposition (K9)


def hv_decomposition(roots, df: pd.DataFrame) -> pd.DataFrame:
    """§5.6: split at the median f2 of the cell's pooled front (all runs of all arms in the cell,
    normalised). cheap / accurate = the run's HV on each side divided by the pooled front's."""
    score = Scorer()
    pooled = {}
    recs = [r for r in records(roots) if r["search_space"] in spec.JAHS_SPACES]
    for r in recs:
        pooled.setdefault((r["search_space"], r["budget"]), []).extend(points(r))
    ref = spec.HV_REF
    split = {}
    for key, pts in pooled.items():
        nf = nondominated(map(tuple, normalise_jahs(pts, score.bounds[key[0]])))
        t = float(np.median([p[1] for p in nf]))
        split[key] = (t, hv_between(nf, ref, -np.inf, t), hv_between(nf, ref, t, np.inf))
    rows = []
    for r in recs:
        key = (r["search_space"], r["budget"])
        t, fc, fa = split[key]
        pts = points(r)
        n = normalise_jahs(pts, score.bounds[key[0]]) if pts else np.empty((0, 2))
        rows.append(dict(method=r["method"], space=key[0], budget=key[1], seed=r["seed"], split_f2=t,
                         cheap=hv_between(n, ref, -np.inf, t) / fc if fc else np.nan,
                         accurate=hv_between(n, ref, t, np.inf) / fa if fa else np.nan,
                         share_cheap_evals=float(np.mean(n[:, 1] < t)) if len(n) else np.nan))
    return pd.DataFrame(rows)


def hv_sensitivity(roots) -> pd.DataFrame:
    """§5.6a (decision R5'): HV at the alternative reference points; medians per arm and cell, the rank
    of each arm under each point, and the Spearman correlation of the rankings with the primary one."""
    score = Scorer()
    rows = []
    for r in records(roots):
        if r["search_space"] not in spec.JAHS_SPACES:
            continue
        pts = points(r)
        row = dict(method=r["method"], space=r["search_space"], budget=r["budget"], seed=r["seed"])
        for ref in (spec.HV_REF, *spec.HV_SENSITIVITY_REFS):
            row[f"hv_{ref}"] = score(r["search_space"], pts, ref)
        rows.append(row)
    runs = pd.DataFrame(rows)
    if runs.empty:
        return runs
    cols = [c for c in runs.columns if c.startswith("hv_")]
    med = runs.groupby(["space", "budget", "method"])[cols].median().reset_index()
    for c in cols:
        med[f"rank_{c}"] = med.groupby(["space", "budget"])[c].rank(ascending=False)
    base = f"rank_hv_{spec.HV_REF}"
    for c in cols[1:]:
        rho = [dict(space=s, budget=b, **{f"spearman_{c}": g[base].corr(g[f"rank_{c}"], method="spearman")})
               for (s, b), g in med.groupby(["space", "budget"])]
        med = med.merge(pd.DataFrame(rho), on=["space", "budget"], how="left")
    return med


# ------------------------------------------------------------------------ regret, generalisation, Q7


def _f1_split(space: str, m: dict) -> tuple[float, float] | None:
    """(validation f1, test f1) of one evaluation from its full-fidelity metrics."""
    if "valid_mse" in m:
        return m["valid_mse"], m.get("test_mse", np.nan)
    if "valid_acc" in m:
        return 100.0 - m["valid_acc"], 100.0 - m.get("test_acc", np.nan)
    return None


def regret_and_generalisation(roots) -> pd.DataFrame:
    """§5.10 regret of f1: oracle spaces -> best f1 of the oracle front; JAHS -> best f1 seen in the cell.
    §5.9 CHOICE: for the run's final non-dominated set (validation objectives): mean test f1 of its
    members and mean (test - validation) gap."""
    from analysis_v005 import fronts

    recs = [r for r in records(roots) if r["search_space"] in spec.SPACES]
    best_cell = {}
    for r in recs:
        f1 = min((h["objectives"][0] for h in r["history"]), default=np.inf)
        k = (r["search_space"], r["budget"])
        best_cell[k] = min(best_cell.get(k, np.inf), f1)
    oracle_best = {s: min(p[0] for p in fronts.load_oracle(s)) for s in spec.ORACLE_SPACES
                   if (fronts.FRONT_DIR / f"oracle__{s}.json").exists()}
    rows = []
    for r in recs:
        space = r["search_space"]
        hist = r["history"]
        f1 = min((h["objectives"][0] for h in hist), default=np.nan)
        best = oracle_best.get(space, best_cell[(space, r["budget"])])
        nd = set(nondominated(points(r)))
        ems = r.get("evaluation_metrics", {}).get("history", [])
        test, gap = [], []
        for h, m in zip(hist, ems):
            if tuple(map(float, h["objectives"])) in nd:
                s = _f1_split(space, m)
                if s is not None:
                    test.append(s[1])
                    gap.append(s[1] - s[0])
        rows.append(dict(method=r["method"], space=space, budget=r["budget"], seed=r["seed"],
                         best_f1=f1, regret=f1 - best,
                         front_test_f1=float(np.mean(test)) if test else np.nan,
                         front_gap=float(np.mean(gap)) if gap else np.nan, front_size=len(nd)))
    return pd.DataFrame(rows)


def q7(df: pd.DataFrame) -> pd.DataFrame:
    """Q7 (supplement): medians of P3-eLyMPuS and canonical P3 per cell, oriented Cliff's delta."""
    from analysis_v005.tests import cliffs

    a, b = spec.Q7
    out = []
    for (space, budget), cell in df.groupby(["space", "budget"]):
        av = cell.loc[cell.method == a, "value"].dropna().to_numpy(float)
        bv = cell.loc[cell.method == b, "value"].dropna().to_numpy(float)
        if len(av) and len(bv):
            s = spec.better_sign(cell.metric.iloc[0])
            out.append(dict(space=space, budget=budget, n_a=len(av), n_b=len(bv), median_elympus=np.median(av),
                            median_canonical=np.median(bv), delta=cliffs(s * av, s * bv)))
    return pd.DataFrame(out)


def budget_use(df: pd.DataFrame) -> pd.DataFrame:
    """§5.5, §5.7: surrogate share (P3Net variants), duplicates, budget fully used, stop reasons,
    level-4 failures; per arm and cell."""
    rows = []
    for (method, space, budget), c in df.groupby(["method", "space", "budget"]):
        mf = c.cost_used.notna().any()
        spent = c.cost_used if mf else c.evaluations_used
        rows.append(dict(
            method=method, space=space, budget=budget, n_runs=len(c),
            # MF: cost within one full-evaluation equivalent of the budget (level-4 `stop` rule)
            budget_fully_used=float(np.mean(spent >= budget - (1.0 if mf else 0.0))),
            duplication_rate_median=c.duplication_rate.median(),
            surrogate_share_median=c.surrogate_share.median(), mixing_steps_median=c.mixing_steps.median(),
            stop_reasons="; ".join(sorted(set(map(str, c.stop_reason.dropna())))),
            level4_failed_runs=int((c.level4_ok == False).sum()),  # noqa: E712
            level4_failed_checks="; ".join(sorted({x for v in c.level4_failed for x in str(v).split(",") if x}))))
    return pd.DataFrame(rows)
