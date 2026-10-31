"""K4, K5 (pre-registration §4).

K4: per family and cell (space, budget): two-sided Mann-Whitney U of REF vs each arm present in the cell
    (unpaired), Holm-Bonferroni within the cell's family at alpha = 0.05, Cliff's delta oriented so that
    positive = better for REF. Median and IQR of both arms.
K5: Q3 TOST for the Q2 pairs: 90 % percentile bootstrap CI of the oriented delta (4 000 resamples);
    "equivalent" if inside (-m, m), "different" if it excludes 0, else "inconclusive"; m = 0.33 and 0.147.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

from analysis_v005 import spec
from stats.significance import holm_bonferroni_correction


def cliffs(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.sign(a[:, None] - b[None, :]).mean())


def _cell_values(cell: pd.DataFrame, method: str) -> np.ndarray:
    return cell.loc[cell.method == method, "value"].dropna().to_numpy(float)


def family_tests(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for name, arms, group in spec.families():
        sub = df[df.group == group]
        for (space, budget), cell in sub.groupby(["space", "budget"]):
            ref = _cell_values(cell, spec.REF)
            if len(ref) < 2:
                continue
            sign = spec.better_sign(cell.metric.iloc[0])
            rows = []
            for arm in arms:
                av = _cell_values(cell, arm)
                if len(av) < 2:
                    continue
                p = float(mannwhitneyu(ref, av, alternative="two-sided").pvalue)
                rows.append(dict(family=name, space=space, budget=budget, ref=spec.REF, arm=arm,
                                 n_ref=len(ref), n_arm=len(av), median_ref=np.median(ref), median_arm=np.median(av),
                                 iqr_ref=np.subtract(*np.quantile(ref, [.75, .25])),
                                 iqr_arm=np.subtract(*np.quantile(av, [.75, .25])),
                                 p=p, delta=cliffs(sign * ref, sign * av)))
            if not rows:
                continue
            for r, h in zip(rows, holm_bonferroni_correction([r["p"] for r in rows], alpha=spec.ALPHA)):
                r.update(family_size=len(rows), adj_p=h.adjusted_p_value, significant=h.reject_null,
                         direction=("REF better" if r["delta"] > 0 else "REF worse") if h.reject_null else "n.s.")
            out.extend(rows)
    return pd.DataFrame(out)


def _tost_cell(a: np.ndarray, b: np.ndarray, rng: np.random.Generator) -> dict:
    d = cliffs(a, b)
    ia = rng.integers(0, len(a), (spec.TOST_RESAMPLES, len(a)))
    ib = rng.integers(0, len(b), (spec.TOST_RESAMPLES, len(b)))
    ds = np.array([cliffs(a[i], b[j]) for i, j in zip(ia, ib)])
    lo, hi = np.quantile(ds, [0.05, 0.95])
    row = dict(delta=d, ci_lo=float(lo), ci_hi=float(hi))
    for m in spec.TOST_MARGINS:
        row[f"verdict_{m}"] = ("equivalent" if -m < lo and hi < m
                               else "different" if lo > 0 or hi < 0 else "inconclusive")
    return row


def tost(df: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(spec.TOST_SEED)
    out = []
    sub = df[df.group == "primary"]
    for (space, budget), cell in sub.groupby(["space", "budget"]):
        sign = spec.better_sign(cell.metric.iloc[0])
        ref = sign * _cell_values(cell, spec.REF)
        for arm in spec.Q2:
            av = sign * _cell_values(cell, arm)
            if len(ref) < 2 or len(av) < 2:
                continue
            out.append(dict(pair=f"{spec.REF} vs {arm}", space=space, budget=budget, n_ref=len(ref), n_arm=len(av),
                            **_tost_cell(ref, av, rng)))
    return pd.DataFrame(out)
