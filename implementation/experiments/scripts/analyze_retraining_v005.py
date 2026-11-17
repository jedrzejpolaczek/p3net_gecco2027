"""K10 retraining (notes/archive/v005/plans/v005-preregistration.md §3 item 8, §8 item 4): descriptive comparison of the
retrained validation accuracy of each arm's knee point with the benchmark's value.

    uv run python scripts/analyze_retraining_v005.py

Reads results/retraining/knees_v005.json and results/retraining/runs/<train_key>.json (written by
scripts/retrain_v005.py); writes results/retraining/
  retraining_v005_arms.csv      one row per (arm, space): benchmark and retrained validation accuracy, difference,
                                retrained test accuracy
  retraining_v005_summary.csv   per space: n arms / unique trainings done, median and max |difference|, mean
                                difference, Spearman rho between benchmark and retrained accuracy over unique
                                trainings, P3Net's rank among arms by benchmark and by retrained accuracy
Descriptive only, as pre-registered. Works on partial results (counts what is done).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
DIR = EXPERIMENTS_ROOT / "results" / "retraining"
REF = "v005_p3net"


def arms_table() -> pd.DataFrame:
    knees = json.loads((DIR / "knees_v005.json").read_text(encoding="utf-8"))["knees"]
    rows = []
    for k in knees:
        path = DIR / "runs" / f"{k['train_key']}.json"
        r = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        bench = 100.0 - k["benchmark_f1"]
        rows.append(dict(method=k["method"], space=k["search_space"], budget=k["budget"], seed=k["seed"],
                         train_key=k["train_key"], benchmark_valid_acc=bench,
                         retrained_valid_acc=r.get("valid_acc"), retrained_test_acc=r.get("test_acc"),
                         difference=(r["valid_acc"] - bench) if r else np.nan,
                         loader=json.dumps(r.get("loader")) if r else None))
    return pd.DataFrame(rows)


def summary(arms: pd.DataFrame) -> pd.DataFrame:
    out = []
    for space, c in arms.groupby("space"):
        done = c.dropna(subset=["retrained_valid_acc"])
        uniq = done.drop_duplicates("train_key")
        rho = spearmanr(uniq.benchmark_valid_acc, uniq.retrained_valid_acc).statistic if len(uniq) >= 3 else np.nan
        row = dict(space=space, arms=len(c), arms_done=len(done), trainings=c.train_key.nunique(),
                   trainings_done=len(uniq), mean_difference=uniq.difference.mean(),
                   median_abs_difference=uniq.difference.abs().median(), max_abs_difference=uniq.difference.abs().max(),
                   spearman_benchmark_vs_retrained=rho)
        if REF in set(done.method) and len(done) == len(c):
            row["p3net_rank_benchmark"] = int(done.benchmark_valid_acc.rank(ascending=False, method="min")[
                done.method == REF].iloc[0])
            row["p3net_rank_retrained"] = int(done.retrained_valid_acc.rank(ascending=False, method="min")[
                done.method == REF].iloc[0])
        out.append(row)
    return pd.DataFrame(out)


def main() -> int:
    arms = arms_table()
    arms.to_csv(DIR / "retraining_v005_arms.csv", index=False)
    s = summary(arms)
    s.to_csv(DIR / "retraining_v005_summary.csv", index=False)
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(s.round(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
