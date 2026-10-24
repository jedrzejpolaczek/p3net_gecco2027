"""A9: equivalence tests (TOST) for the v004 pairs reported as "no difference", and S4' vs S5 directly.

Reads $V004_OUT/per_run.csv (analyze.py). Per (pair, space, budget) cell, seeds as given per pair:
- two-sided Mann-Whitney U p (no correction: these are descriptive pair checks, one per cell);
- Cliff's delta, oriented so positive favours arm A (HV larger / IGD+ smaller);
- 90% bootstrap percentile CI of delta (= TOST at alpha 0.05 on each side) and the verdict:
  "equiv" if the CI lies inside (-m, m), "differ" if it excludes 0, otherwise "inconcl.";
  margins m = 0.147 (negligible, Romano et al. 2006) and 0.33 (small);
- Hodges-Lehmann shift (median of pairwise differences, oriented like delta) with its 90% CI, raw units.

Writes $V004_OUT/equivalence.csv and prints a per-pair summary.
"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

HERE = Path(os.environ["V004_OUT"])
MAIN = ["jahs_bench_201", "jahs_bench_201_colorectal", "jahs_bench_201_fashion", "nas_hpo_bench_ii"]
MARGINS = (0.147, 0.33)
B = 4000
RNG = np.random.default_rng(20261024)

S1, S2, S3, S4 = "p3net_s1_initial", "p3net_s2_analytic_cost", "p3net_s3_ridge", "p3net"
S4P, S5 = "p3net_s4_eager_mixing", "p3net_cascade"
Q3_NULL = ["p3net_cascade_inherited_cost", "p3net_cascade_f1_truncation", "p3net_cascade_transient_donors",
           "p3net_cascade_threshold_permissive"]
#: (label, arm A, arm B, seed sets). A is the later / reference arm; delta > 0 favours A.
PAIRS = ([("S4' vs S5", S4P, S5, ("1-30",)),
          ("S5 vs inherited_cost", S5, "p3net_cascade_inherited_cost", ("1-30",)),
          ("M9 vs M10", "przewozniczek_p3elympus", "canonical_p3_scalar_fihc", ("1-30", "31-60")),
          ("S2 vs S1", S2, S1, ("1-30",)), ("S3 vs S2", S3, S2, ("1-30",)), ("S4 vs S3", S4, S3, ("1-30",)),
          ("S5 vs bartnik_p3", S5, "bartnik_p3", ("1-30", "31-60")),
          ("S5 vs M9", S5, "przewozniczek_p3elympus", ("1-30", "31-60")),
          ("S5 vs M10", S5, "canonical_p3_scalar_fihc", ("1-30", "31-60"))]
         + [(f"S5 vs {v.removeprefix('p3net_cascade_')}", S5, v, ("1-30",)) for v in Q3_NULL[1:]])


def cliffs(a, b):
    return float(np.sign(a[:, None] - b[None, :]).mean())


def cell(a, b, sign):
    a, b = sign * np.asarray(a, float), sign * np.asarray(b, float)
    d = cliffs(a, b)
    hl = float(np.median((a[:, None] - b[None, :]).ravel()))
    ia = RNG.integers(0, len(a), (B, len(a)))
    ib = RNG.integers(0, len(b), (B, len(b)))
    ds = np.empty(B)
    hs = np.empty(B)
    for k in range(B):
        x, y = a[ia[k]], b[ib[k]]
        ds[k] = cliffs(x, y)
        hs[k] = np.median((x[:, None] - y[None, :]).ravel())
    lo, hi = np.quantile(ds, [0.05, 0.95])
    hlo, hhi = np.quantile(hs, [0.05, 0.95])
    row = dict(delta=d, d_lo=lo, d_hi=hi, hl=hl, hl_lo=hlo, hl_hi=hhi,
               p=mannwhitneyu(a, b, alternative="two-sided").pvalue)
    for m in MARGINS:
        row[f"v{m}"] = "equiv" if -m < lo and hi < m else ("differ" if lo > 0 or hi < 0 else "inconcl.")
    return row


def main():
    df = pd.read_csv(HERE / "per_run.csv")
    sign = {"hv_rel": 1.0, "igd_plus": -1.0}
    out = []
    for label, a, b, seed_sets in PAIRS:
        for seeds in seed_sets:
            sub = df[(df.seeds == seeds) & df.method.isin([a, b])]
            for (s, bud), c in sub.groupby(["space", "budget"]):
                av, bv = c[c.method == a].value.values, c[c.method == b].value.values
                if len(av) < 2 or len(bv) < 2:
                    continue
                out.append(dict(pair=label, seeds=seeds, space=s, budget=bud, n_a=len(av), n_b=len(bv),
                                metric=c.metric.iloc[0], **cell(av, bv, sign[c.metric.iloc[0]])))
    res = pd.DataFrame(out)
    res.to_csv(HERE / "equivalence.csv", index=False)
    pd.set_option("display.width", 250)
    for (label, seeds), g in res.groupby(["pair", "seeds"], sort=False):
        main_ = g[g.space.isin(MAIN)]
        counts = {m: main_[f"v{m}"].value_counts().to_dict() for m in MARGINS}
        print(f"\n## {label}  seeds {seeds}  (main cells: {len(main_)}; all cells: {len(g)})")
        print("  main, margin 0.147:", counts[0.147], "| margin 0.33:", counts[0.33],
              f"| median delta {main_.delta.median():+.3f}")
        print(g[["space", "budget", "n_a", "n_b", "delta", "d_lo", "d_hi", "hl", "hl_lo", "hl_hi", "p",
                 "v0.147", "v0.33"]].round(4).to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
