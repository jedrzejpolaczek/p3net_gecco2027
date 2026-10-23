"""Level 2 (v005-level2-criteria.md, "NSGANetV2 — kryterium doprecyzowane przed testem"):
our NSGANetV2 predictors vs the authors' (`nsganetv2_reference_runner.py`, old env).

  python nsganetv2_vs_reference.py --repo NSGANETV2_REPO --work DIR [--datasets 100] [--workers 14]

Writes DIR/report.json; `test_nsganetv2_vs_reference.py` checks the criterion on it.
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _problems import PROBLEMS, objective  # noqa: E402

ENV_PY = HERE.parents[3] / "experiments" / "vendor" / "nsganetv2-env" / ".venv" / "Scripts" / "python.exe"
N_TRAIN, N_TEST = 50, 200


def datasets(n: int) -> list[dict]:
    f = objective("additive")
    domains = PROBLEMS["additive"]["domains"]
    out = []
    for s in range(n):
        rnd = random.Random(s)
        X = [[rnd.randrange(k) for k in domains] for _ in range(N_TRAIN + N_TEST)]
        y = [f(x)[0] for x in X]
        perm = list(range(N_TRAIN))
        rnd.shuffle(perm)
        out.append({"seed": s, "Xtr": X[:N_TRAIN], "ytr": y[:N_TRAIN], "Xte": X[N_TRAIN:], "yte": y[N_TRAIN:],
                    "perm": perm})
    return out


def _ours(d: dict) -> dict:
    from p3net.v005.baselines.nsganetv2 import _CART, _GP, _RBF

    Xtr, ytr, Xte = np.array(d["Xtr"], float), np.array(d["ytr"], float), np.array(d["Xte"], float)
    rng = random.Random(d["seed"])
    res = {"rbf": _RBF().fit(Xtr, ytr, rng).predict(Xte).tolist(),
           "gp": _GP().fit(Xtr, ytr, rng).predict(Xte).tolist(),
           "carts": _CART().fit(Xtr, ytr, rng).predict(Xte).tolist()}
    tau = np.full((10, 3), np.nan)
    perm = np.array(d["perm"])
    for i, tst in enumerate(np.array_split(perm, 10)):  # the authors' folds, to compare model choice only
        trn = np.setdiff1d(perm, tst, assume_unique=True)
        for j, cls in enumerate((_RBF, _GP, _CART)):
            p = cls().fit(Xtr[trn], ytr[trn], rng).predict(Xtr[tst])
            tau[i, j] = stats.kendalltau(p, ytr[tst]).statistic
    res["as_tau"] = tau.tolist()
    return res


def _winner(tau) -> int:
    tau = np.array(tau, float)
    return int(np.argmax(np.mean(tau, axis=0) - np.std(tau, axis=0)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--datasets", type=int, default=100)
    ap.add_argument("--workers", type=int, default=14)
    a = ap.parse_args()
    work = Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    data = datasets(a.datasets)
    chunks = [data[i::a.workers] for i in range(a.workers)]
    procs = []
    for i, ch in enumerate(chunks):
        (work / f"data_{i}.json").write_text(json.dumps(ch))
        procs.append(subprocess.Popen([str(ENV_PY), "-I", str(HERE / "nsganetv2_reference_runner.py"), a.repo,
                                       str(work / f"data_{i}.json"), str(work / f"ref_{i}.json")]))
    with ProcessPoolExecutor(a.workers) as ex:
        ours = list(ex.map(_ours, data))
    for p in procs:
        if p.wait() != 0:
            raise RuntimeError("reference runner failed")
    ref = [None] * len(data)
    for i, ch in enumerate(chunks):
        for d, r in zip(ch, json.loads((work / f"ref_{i}.json").read_text())):
            ref[d["seed"]] = r
    rep = {}
    for m in ("rbf", "gp", "carts"):
        t_or = [stats.kendalltau(o[m], r[m]).statistic for o, r in zip(ours, ref)]
        t_o = [stats.kendalltau(o[m], d["yte"]).statistic for o, d in zip(ours, data)]
        t_r = [stats.kendalltau(np.ravel(r[m]), d["yte"]).statistic for r, d in zip(ref, data)]
        rep[m] = {"median_tau_ours_ref": float(np.median(t_or)), "median_tau_ours_truth": float(np.median(t_o)),
                  "median_tau_ref_truth": float(np.median(t_r))}
    rep["carts"]["median_tau_ref_ref"] = float(np.median(
        [stats.kendalltau(r["carts"], r["carts2"]).statistic for r in ref]))
    rep["as_winner_agreement"] = float(np.mean([_winner(o["as_tau"]) == _winner(r["as_tau"]) for o, r in zip(ours, ref)]))
    rep["as_winners_ours"] = np.bincount([_winner(o["as_tau"]) for o in ours], minlength=3).tolist()
    rep["as_winners_ref"] = np.bincount([_winner(r["as_tau"]) for r in ref], minlength=3).tolist()
    (work / "report.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
