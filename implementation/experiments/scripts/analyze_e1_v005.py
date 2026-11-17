"""Exploratory addendum E1 (notes/archive/v005/plans/v005-preregistration.md §7a): the P3Net family at b = 1000.

    uv run python scripts/analyze_e1_v005.py            # results/runs/c674c91e-e1 -> .../analysis

Per primary space, exactly as fixed in §7a before the grid ran:
  e1_q2.csv     Q2 family (P3Net vs canonical P3, P3Net-gate, P3Net-nolink): two-sided Mann-Whitney U,
                Holm within the space, alpha = 0.05, Cliff's delta (positive = P3Net better)
  e1_tost.csv   TOST of the same pairs, m = 0.33 and 0.147 (90 % bootstrap CI, as §4 / K5)
  _generated_e1.tex (chapters/results/) LaTeX table of the above
  e1_descr.csv  per arm: median metric, IQR, median mixing steps, median surrogate share, share of runs
                identical to P3Net (same seed, same final metric value), delta vs random search (no test)
Reuses analysis_v005 (per_run, tests) unchanged; metrics as §3 (normalised HV on JAHS, IGD+ on NAS-HPO-II).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
if str(EXPERIMENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS_ROOT))

from analysis_v005 import per_run, spec, tests  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_v005_tex as rt  # noqa: E402

ROOT = EXPERIMENTS_ROOT / "results" / "runs" / "c674c91e-e1"
ARMS = [spec.REF, *spec.Q2, "v005_random_search"]


def descriptive(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for space, cell in df.groupby("space"):
        sign = spec.better_sign(cell.metric.iloc[0])
        ref = cell[cell.method == spec.REF].set_index("seed")
        rs = cell.loc[cell.method == "v005_random_search", "value"].dropna().to_numpy(float)
        for arm in ARMS:
            c = cell[cell.method == arm]
            v = c.value.dropna().to_numpy(float)
            same = c.set_index("seed").value.reindex(ref.index)
            rows.append(dict(
                space=space, method=arm, n=len(v), metric=cell.metric.iloc[0], median=np.median(v),
                iqr=np.subtract(*np.quantile(v, [.75, .25])),
                mixing_steps_median=c.mixing_steps.median(), surrogate_share_median=c.surrogate_share.median(),
                identical_to_p3net=float((same == ref.value).mean()) if arm != spec.REF else np.nan,
                delta_vs_random_search=tests.cliffs(sign * v, sign * rs) if arm != "v005_random_search" else np.nan,
                evaluations_used_min=c.evaluations_used.min()))
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)
    out = args.out or args.root / "analysis"
    out.mkdir(parents=True, exist_ok=True)

    df = per_run.per_run([args.root])
    df = df[df.group == "primary"]
    df.to_csv(out / "e1_per_run.csv", index=False)
    counts = df.groupby(["space", "method"]).size()
    print(f"runs: {len(df)}; per cell min {counts.min()} max {counts.max()}; duplicates {len(per_run.duplicates(df))}")

    q = tests.family_tests(df)
    q = q[q.family == "Q2"]
    q.to_csv(out / "e1_q2.csv", index=False)
    tests.tost(df).to_csv(out / "e1_tost.csv", index=False)
    descriptive(df).to_csv(out / "e1_descr.csv", index=False)
    print(f"wrote e1_per_run, e1_q2, e1_tost, e1_descr -> {out}")
    tex = render(q, pd.read_csv(out / "e1_tost.csv"), pd.read_csv(out / "e1_descr.csv"))
    (rt.OUT_DIR / "_generated_e1.tex").write_text(tex + "\n", encoding="utf-8")
    print(f"wrote {rt.OUT_DIR / '_generated_e1.tex'}")
    return 0


def render(q: pd.DataFrame, tost: pd.DataFrame, descr: pd.DataFrame) -> str:
    """LaTeX table of E1 in the style of the v005 Q2/Q3 table (render_v005_tex.q2_q3)."""
    body = []
    for s in rt.PRIMARY:
        d = descr[descr.space == s].set_index("method")
        cells = [f"{d.loc[spec.REF, 'mixing_steps_median']:.0f}"]
        for arm in spec.Q2:
            r = q[(q.space == s) & (q.arm == arm)].iloc[0]
            t = tost[(tost.space == s) & (tost.pair == f"{spec.REF} vs {arm}")].iloc[0]
            star = "^{*}" if r.significant else ""
            verdict = {"equivalent": "eq.", "inconclusive": "inc.", "different": "diff."}[t["verdict_0.33"]]
            cells += [f"${t.delta:+.2f}{star}$", f"$[{t.ci_lo:+.2f}, {t.ci_hi:+.2f}]$", verdict,
                      f"{100 * d.loc[arm, 'identical_to_p3net']:.0f}"]
        cells.append(f"${d.loc[spec.REF, 'delta_vs_random_search']:+.2f}$")
        body.append(f"{rt.SHORT[s]} & " + " & ".join(cells) + " \\\\")
    head = ["& & " + " & ".join(f"\\multicolumn{{4}}{{c}}{{P3Net vs.\\ {rt.NAMES[a]}}}" for a in spec.Q2)
            + " & \\\\",
            "".join(f"\\cmidrule(lr){{{3 + 4 * i}-{6 + 4 * i}}}" for i in range(3)),
            "\\textbf{Space} & steps & " + " & ".join(["$\\delta$ & 90\\,\\% CI & TOST & same\\,\\%"] * 3)
            + " & vs.\\ RS \\\\"]
    m_main, m_side = spec.TOST_MARGINS
    side = tost[f"verdict_{m_side}"].value_counts().to_dict()
    side_text = ", ".join(f"{v} {k}" for k, v in sorted(side.items()))
    n_sig = int(q.significant.sum())
    cap = ("Exploratory addendum E1 (budget $b = 1000$, seeds 92--121, 30 runs per arm and space): what the surrogate "
           "contributes when it has room to act. steps = median number of surrogate-screened P3Net mixing steps per "
           f"run. Cliff's $\\delta$ (positive favours P3Net; $^{{*}}$ = rejected after Holm within the space's Q2 "
           f"family; {n_sig} of {len(q)} comparisons are), its 90\\,\\% bootstrap CI and the TOST verdict at "
           f"$m={m_main}$ (at $m={m_side}$: {side_text} of {len(tost)}); same\\,\\% = share of seeds whose final "
           "metric value equals P3Net's. vs.\\ RS = $\\delta$ of P3Net vs.\\ random search (reference only, no test).")
    header = ["% GENERATED by implementation/experiments/scripts/analyze_e1_v005.py.", rt.HEADER[1], ""]
    return "\n".join(header + rt.table("table*", cap, "tab:v005-e1", "lr" + "rrrr" * 3 + "r", head, body))


if __name__ == "__main__":
    sys.exit(main())
