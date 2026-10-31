"""K1, K2 (pre-registration §3, §7): built once, before the run, from the benchmark tables only.

K1: exact oracle front of every oracle space for the **v005 objectives**, computed through the same
    substrate the methods query (`objectives(g)` of the v005 search-space config), over every valid
    configuration -> results/reference_fronts/oracle__<space>.json.
K2: JAHS bounds of the normalised HV: f1 in [0, 100], f2 in [min, max] of the task's parameter-count
    table -> results/reference_fronts/jahs_bounds_v005.json.
"""

from __future__ import annotations

import itertools
import json
import time
from pathlib import Path

from p3net.problem.decoding import is_valid
from p3net.problem.genotype import Genotype

from analysis_v005 import spec

EXPERIMENTS = Path(__file__).resolve().parent.parent
FRONT_DIR = EXPERIMENTS / "results" / "reference_fronts"
JAHS_BOUNDS = FRONT_DIR / "jahs_bounds_v005.json"
PARAM_TABLE = EXPERIMENTS / "results" / "benchmark_tables" / "jahs_param_counts.json"


def nondominated(points):
    """2-D non-dominated set (minimisation), duplicates collapsed, sorted by f1."""
    out, best = [], float("inf")
    for p in sorted(set(map(tuple, points))):
        if p[1] < best:
            out.append(p)
            best = p[1]
    return out


def _all_objectives(space: str):
    from scripts import run_experiment

    cfg = run_experiment.load_search_space_config(space)
    sub = run_experiment.build_substrate(cfg)
    if space.startswith("fcnet_"):
        genotypes, objectives = sub.all_objectives()
        # the fast path must agree with what the methods see
        for i in range(0, len(genotypes), max(1, len(genotypes) // 50)):
            a, b = tuple(map(float, objectives[i])), tuple(map(float, sub.objectives(genotypes[i])))
            if a != b:
                raise ValueError(f"{space}: all_objectives {a} != objectives {b} at {genotypes[i]}")
        return [tuple(map(float, o)) for o in objectives], len(genotypes), len(genotypes)
    search_space, validity = run_experiment.build_search_space(cfg)
    points, n_all, n_valid = [], 0, 0
    for combo in itertools.product(*(d.values for d in search_space.domains)):
        n_all += 1
        g = Genotype(values=tuple(combo))
        if not is_valid(g, validity):
            continue
        n_valid += 1
        points.append(tuple(map(float, sub.objectives(g))))
    return points, n_all, n_valid


def build_oracle(space: str) -> Path:
    started = time.time()
    points, n_all, n_valid = _all_objectives(space)
    front = nondominated(points)
    path = FRONT_DIR / f"oracle__{space}.json"
    path.write_text(json.dumps({
        "search_space": space, "front": [list(p) for p in front], "n_enumerated": n_all, "n_valid": n_valid,
        "objectives": "v005 search-space config, substrate.objectives(g) (analysis_v005/fronts.py, K1)",
        "seconds": round(time.time() - started, 1)}, indent=1), encoding="utf-8")
    return path


def load_oracle(space: str) -> list[tuple[float, float]]:
    return [tuple(p) for p in json.loads((FRONT_DIR / f"oracle__{space}.json").read_text(encoding="utf-8"))["front"]]


def build_jahs_bounds() -> Path:
    params = json.loads(PARAM_TABLE.read_text(encoding="utf-8"))["params"]
    out = {}
    for space in spec.JAHS_SPACES:
        task = spec.SPACES[space][3]
        vals = [cell[task] for cell in params.values()]
        out[space] = {"f1": [0.0, 100.0], "f2": [float(min(vals)), float(max(vals))], "task": task}
    JAHS_BOUNDS.write_text(json.dumps(
        {"bounds": out, "reference_point": spec.HV_REF,
         "rule": "f1/100, (f2-min)/(max-min); HV with reference (r, r) divided by r^2 (decision R5 b1)",
         "source": str(PARAM_TABLE.relative_to(EXPERIMENTS))}, indent=1), encoding="utf-8")
    return JAHS_BOUNDS


def load_jahs_bounds() -> dict:
    return json.loads(JAHS_BOUNDS.read_text(encoding="utf-8"))["bounds"]
