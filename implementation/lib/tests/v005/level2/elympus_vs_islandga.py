"""Level 2 (v005-level2-criteria.md): P3-eLyMPuS and canonical P3 vs the authors' code
(OLyMPuS `IslandGA.exe`, built from source; settings `settings_P3_LSur1nth_*` and
`settings_P3standard_*` of `exp_POLiNoMok`) on concatenated deceptive functions.

Single-objective reference vs our two-objective methods: the objective is duplicated
(f2 = f1), so Pareto dominance reduces to improvement of f1 and both eLyMPuS memories
learn the same VIG. Both sides run until the optimum is found.

Measured per run: FFE to the optimum -- ours counted twice: unique evaluations (our
budget, #35) and all evaluation requests including repeats answered from the cache
(the reference keeps no evaluation cache) -- and, for eLyMPuS, the discovered VIG
edges (true / false, ordered pairs, as in the reference `_VIGquality_` log).

Usage:
  python elympus_vs_islandga.py ours  --problem DIR --method elympus|p3 --runs 100 --out FILE
  python elympus_vs_islandga.py ref   --problem DIR --method elympus|p3 --runs 100 --exe EXE --work DIR --out FILE
  python elympus_vs_islandga.py compare FILE_OURS FILE_REF
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

SETTINGS = {"elympus": "P3_LSur1nth", "p3": "P3standard", "p3goldman": "P3standard"}
# "p3goldman": the authors' P3standard settings with opt_at_init 1 (Goldman's own FIHC, LOC_OPT_FIHC)
# instead of 5 (FIHC run through the limited-surrogate class, strategy FIHCstandard)
OVERRIDES = {"p3goldman": {b"opt_at_init": b"1"}}


# -- problem (binary_deceptive_concatenation) ------------------------------------
def read_problem(problem_dir: Path) -> dict:
    f = next(problem_dir.glob("dec_*.txt"), None) or next(
        p for p in problem_dir.glob("*.txt") if not p.name.startswith(("settings_", "z_serie")))
    lines = [ln.split("\\\\")[0].strip() for ln in f.read_text().splitlines()]
    overlap, blocks, _, k = int(lines[0]), int(lines[1]), lines[2], int(lines[3])
    table = [float(x) for x in lines[4].split()]
    if overlap != 0:
        raise NotImplementedError("overlapping (cyclic) traps are not ported")
    return {"file": f.name, "blocks": blocks, "k": k, "table": table, "n": blocks * k,
            "optimum": blocks * max(table)}


def make_f(p: dict):
    k, table, opt = p["k"], p["table"], p["optimum"]

    def F(x) -> float:
        return sum(table[sum(x[b * k:(b + 1) * k])] for b in range(p["blocks"]))

    return F, opt


# -- ours -----------------------------------------------------------------------
def _one_ours(args) -> dict:
    problem_dir, method, seed, max_evals = args
    from p3net.harness.runner import Observation, RunState
    from p3net.problem.genotype import CategoricalDomain, SearchSpace
    from p3net.v005.elympus import P3ELyMPuS
    from p3net.v005.methods import P3Canonical

    p = read_problem(Path(problem_dir))
    F, opt = make_f(p)
    space = SearchSpace(domains=tuple(CategoricalDomain(values=(0, 1)) for _ in range(p["n"])))
    cls = P3ELyMPuS if method == "elympus" else P3Canonical  # p3 and p3goldman: same ours
    m = cls(space, max_evals, random.Random(seed))
    hits = [0]
    get = m.cache.get

    def counting_get(g):
        r = get(g)
        if r is not None:
            hits[0] += 1
        return r

    m.cache.get = counting_get
    self_hits = [0]
    if method == "elympus":
        # requests for the solution itself inside a pair computation (x with var := x[var]):
        # the reference already holds f(x) there and does not evaluate it
        from p3net.v005 import elympus as el

        def _compute(self, x, var, _orig=el.ELyMPuS._compute):
            gen, msg = _orig(self, x, var), None
            try:
                g = next(gen)
                while True:
                    if tuple(g.values) == tuple(x) and m.cache.get.__wrapped__(g) is not None:
                        self_hits[0] += 1
                    msg = yield g
                    g = gen.send(msg)
            except StopIteration as stop:
                return stop.value

        el.ELyMPuS._compute = _compute
        counting_get.__wrapped__ = get
    state = RunState()
    t0, solved = time.perf_counter(), False
    while state.evaluations_used < max_evals:
        props = m.propose(state)
        if not props:
            break
        g = props[0]
        Fv = F(g.values)
        cost = opt + 1.0 - Fv  # minimised, positive
        state.evaluations_used += 1
        m.update(state, [Observation(genotype=g, objectives=(cost, cost))])
        if Fv >= opt:
            solved = True
            break
    out = {"seed": seed, "solved": solved, "ffe_unique": state.evaluations_used,
           "ffe_requests": state.evaluations_used + hits[0],
           "ffe_requests_no_self": state.evaluations_used + hits[0] - self_hits[0], "seconds": time.perf_counter() - t0,
           "stop_reason": m.stop_reason}
    if method == "elympus":
        k = p["k"]
        vig = m.elympus[0].vig
        true = sum(1 for i, js in vig.items() for j in js if i // k == j // k)
        false = sum(1 for i, js in vig.items() for j in js if i // k != j // k)
        out.update(dep_true=true, dep_false=false, dep_total=p["blocks"] * k * (k - 1))
    return out


def run_ours(a) -> None:
    jobs = [(a.problem, a.method, s, a.max_evals) for s in range(a.runs)]
    with ProcessPoolExecutor(a.workers) as ex:
        res = list(ex.map(_one_ours, jobs))
    Path(a.out).write_text(json.dumps({"side": "ours", "method": a.method, "problem": a.problem, "runs": res}))
    print(summary(res))


# -- reference --------------------------------------------------------------------
def _one_ref(args) -> dict:
    problem_dir, method, i, exe, work = args
    problem_dir, work = Path(problem_dir), Path(work) / f"run_{i:03d}"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    st = next(problem_dir.glob(f"settings_{SETTINGS[method]}____*.txt"))
    for f in [st, problem_dir / "default.cfg", problem_dir / "zobristkey", problem_dir / read_problem(problem_dir)["file"]]:
        shutil.copy(f, work)
    shutil.copy(exe, work)
    # without the optional `random_seed` line IslandGA seeds from the clock in seconds, so
    # runs started in the same second are identical; insert it right after `mode`
    lines = (work / st.name).read_bytes().split(b"\r\n")
    at = next(j for j, ln in enumerate(lines) if ln.endswith(b"\\\\mode")) + 1
    lines.insert(at, f"{i + 1}\\\\random_seed".encode())
    for key, val in OVERRIDES.get(method, {}).items():
        lines = [val + b"\\\\" + ln.split(b"\\\\", 1)[1] if b"\\\\" + key in ln else ln for ln in lines]
    (work / st.name).write_bytes(b"\r\n".join(lines))
    (work / "1_entry.txt").write_bytes(st.name.encode() + b"\r\n")
    t0 = time.perf_counter()
    subprocess.run([str(work / Path(exe).name), "1"], cwd=work, stdin=subprocess.DEVNULL,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3600)
    cells = (work / "1_out.txt").read_text().split("\t")
    kv = {cells[j].strip("{}"): cells[j + 1] for j in range(0, len(cells) - 1) if cells[j].startswith("{")}
    out = {"run": i, "solved": float(kv["BestVal"]) >= float(kv["OptValue"]), "ffe": int(kv["BestFFE"]),
           "seconds": time.perf_counter() - t0}
    # the reference's own cost breakdown (mixing = OMstats_cost; FIHC = regular + missing-
    # linkage detection (verification) + dependency discovery)
    for key in ("OMstats_cost", "LimitedNonMonoSurrogate_FIHCcost_FFEtotal", "LimitedNonMonoSurrogate_FIHCcost_FFEregular",
                "LimitedNonMonoSurrogate_FIHCcost_FFEmissLinkDetection", "LimitedNonMonoSurrogate_FIHCcost_FFEdepDiscovery"):
        if key in kv:
            out["cost_" + key.split("_")[-1]] = int(float(kv[key]))
    vig = list(work.glob("*_VIGquality_.txt"))
    if vig:
        last = vig[0].read_text().strip().splitlines()[-1]
        nums = last.split("true/missing/false:")[1].split("FFE:")[0].split()
        out.update(dep_true=int(nums[0]), dep_missing=int(nums[1]), dep_false=int(nums[2]))
    if not (work / "error_0000.log").exists():
        shutil.rmtree(work)
    return out


def run_ref(a) -> None:
    jobs = [(a.problem, a.method, i, a.exe, a.work) for i in range(a.runs)]
    with ProcessPoolExecutor(a.workers) as ex:
        res = list(ex.map(_one_ref, jobs))
    Path(a.out).write_text(json.dumps({"side": "ref", "method": a.method, "problem": a.problem, "runs": res}))
    print(summary(res))


# -- comparison -------------------------------------------------------------------
def summary(res: list[dict]) -> str:
    keys = [k for k in ("ffe", "ffe_unique", "ffe_requests", "ffe_requests_no_self", "dep_true", "dep_false") if k in res[0]]
    s = {k: float(np.median([r[k] for r in res])) for k in keys}
    return f"n={len(res)} solved={sum(r['solved'] for r in res)} medians={s}"


def tost(x, y, margin) -> float:
    from scipy import stats

    p_low = stats.ttest_ind(x + margin, y, equal_var=False, alternative="greater").pvalue
    p_high = stats.ttest_ind(x - margin, y, equal_var=False, alternative="less").pvalue
    return float(max(p_low, p_high))


def compare(ours_file: str, ref_file: str) -> dict:
    o, r = json.loads(Path(ours_file).read_text())["runs"], json.loads(Path(ref_file).read_text())["runs"]
    ref_ffe = np.array([x["ffe"] for x in r], float)
    out = {"ref_median_ffe": float(np.median(ref_ffe)), "ref_solved": sum(x["solved"] for x in r),
           "ours_solved": sum(x["solved"] for x in o)}
    for key in ("ffe_unique", "ffe_requests"):
        ours = np.array([x[key] for x in o], float)
        med = float(np.median(ref_ffe))
        out[key] = {"median": float(np.median(ours)), "rel_diff": float(np.median(ours) / med - 1),
                    "within_2pct": bool(abs(np.median(ours) - med) <= 0.02 * med),
                    "tost_p": tost(ours, ref_ffe, 0.02 * med)}
    if "dep_true" in r[0] and "dep_true" in o[0]:
        rt = np.array([x["dep_true"] / (x["dep_true"] + x["dep_missing"]) for x in r])
        ot = np.array([x["dep_true"] / x["dep_total"] for x in o])
        out["dep_share"] = {"ref_median": float(np.median(rt)), "ours_median": float(np.median(ot)),
                            "abs_diff": float(np.median(ot) - np.median(rt)),
                            "tost_p": tost(ot, rt, 0.02 * float(np.median(rt))),
                            "ref_false_median": float(np.median([x["dep_false"] for x in r])),
                            "ours_false_median": float(np.median([x["dep_false"] for x in o]))}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("ours", "ref"):
        s = sub.add_parser(name)
        s.add_argument("--problem", required=True)
        s.add_argument("--method", choices=list(SETTINGS), required=True)
        s.add_argument("--runs", type=int, default=100)
        s.add_argument("--workers", type=int, default=8)
        s.add_argument("--out", required=True)
        if name == "ours":
            s.add_argument("--max-evals", type=int, default=2_000_000)
        else:
            s.add_argument("--exe", required=True)
            s.add_argument("--work", required=True)
    c = sub.add_parser("compare")
    c.add_argument("ours")
    c.add_argument("ref")
    a = ap.parse_args()
    if a.cmd == "ours":
        run_ours(a)
    elif a.cmd == "ref":
        run_ref(a)
    else:
        print(json.dumps(compare(a.ours, a.ref), indent=1))


if __name__ == "__main__":
    sys.exit(main())
