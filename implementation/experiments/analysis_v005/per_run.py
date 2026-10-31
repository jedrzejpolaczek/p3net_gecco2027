"""K3 (pre-registration §3, §5.3, §5.5, §5.7): one row per run record of the given run roots, plus the
list of pre-registered grid points without a record (§4: missing runs are reported, never imputed)."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from analysis_v005 import fronts, spec
from analysis_v005.metrics import IGDPlus, hv_jahs

EXPERIMENTS = Path(__file__).resolve().parent.parent


def records(roots: Iterable[Path]) -> Iterator[dict]:
    for root in roots:
        for path in sorted((Path(root) / "raw").glob("v005_*.json")):
            d = json.loads(path.read_text(encoding="utf-8"))
            d["_path"] = str(path)
            yield d


def points(rec: dict) -> list[tuple[float, float]]:
    """Full-fidelity points of the run (main track: every evaluation; MF: history = trained to E)."""
    return [tuple(map(float, h["objectives"])) for h in rec["history"]]


class Scorer:
    def __init__(self):
        self.igd = {s: IGDPlus(fronts.load_oracle(s)) for s in spec.ORACLE_SPACES
                    if (fronts.FRONT_DIR / f"oracle__{s}.json").exists()}
        self.bounds = fronts.load_jahs_bounds() if fronts.JAHS_BOUNDS.exists() else {}

    def __call__(self, space: str, pts, ref: float = spec.HV_REF) -> float:
        if not pts:
            return float("nan")
        if spec.SPACES[space][1] == "hv":
            return hv_jahs(pts, self.bounds[space], ref)
        return self.igd[space](pts)


def _row(rec: dict, score: Scorer) -> dict:
    space = rec["search_space"]
    dg = rec.get("diagnostics", {})
    res, top = dg.get("resources", {}), rec.get("resources", {})
    l4 = dg.get("level4", {})
    v5 = dg.get("v005", {})
    share = (l4.get("surrogate_share", {}).get("detail") or {})
    pts = points(rec)
    em = rec.get("evaluation_metrics", {})
    return dict(
        method=rec["method"], space=space, group=spec.SPACES[space][0], metric=spec.SPACES[space][1],
        budget=rec["budget"], seed=rec["seed"], value=score(space, pts),
        n_full=len(pts), evaluations_used=rec.get("evaluations_used"), cost_used=dg.get("cost_used"),
        duplication_rate=dg.get("duplication_rate"), stop_reason=v5.get("stop_reason"),
        level4_ok=all(c.get("ok") is not False for c in l4.values()) if l4 else None,
        level4_failed=",".join(k for k, c in l4.items() if c.get("ok") is False),
        surrogate_share=share.get("surrogate_share") if isinstance(share, dict) else None,
        mixing_steps=share.get("mixing_steps") if isinstance(share, dict) else None,
        method_wall_seconds=top.get("method_wall_seconds"), wall_seconds=res.get("wall_seconds"),
        peak_memory_process_mb=top.get("peak_memory_process_mb"),
        peak_memory_process_scope=top.get("peak_memory_process_scope"),
        peak_memory_server_mb=top.get("peak_memory_server_mb"),
        peak_memory_server_method=top.get("peak_memory_server_method"),
        peak_memory_gpu_mb=top.get("peak_memory_gpu_mb"), surrogate_load_seconds=top.get("surrogate_load_seconds"),
        simulated_training_seconds=res.get("simulated_training_seconds"),
        has_evaluation_metrics=bool(em), path=rec["_path"],
    )


def per_run(roots: Iterable[Path]) -> pd.DataFrame:
    score = Scorer()
    return pd.DataFrame([_row(r, score) for r in records(roots) if r["search_space"] in spec.SPACES])


def expected_points(plans: Iterable[Path]) -> pd.DataFrame:
    """Grid points of the pre-registered plans (configs/pipeline/v005*.yaml)."""
    rows = []
    for plan in plans:
        d = yaml.safe_load(Path(plan).read_text(encoding="utf-8"))
        groups = d.get("method_groups", {})
        for st in d["stages"]:
            if st.get("kind") != "grid":
                continue
            methods = [m for x in st["methods"] for m in (x if isinstance(x, list) else groups.get(x, [x]))]
            seeds = st["seeds"]
            seeds = range(seeds["from"], seeds["to"] + 1) if isinstance(seeds, dict) else seeds
            for m in methods:
                for s in st["search_spaces"]:
                    for b in st["budgets"]:
                        for seed in seeds:
                            rows.append(dict(stage=st["name"], method=m, space=s, budget=b, seed=seed))
    return pd.DataFrame(rows)


def duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Grid points with more than one record across the run roots (must be empty in v005: one record per
    point; a non-empty table is an alarm for the post-run control)."""
    key = ["method", "space", "budget", "seed"]
    return df[df.duplicated(key, keep=False)].sort_values(key)[key + ["path"]] if len(df) else df


def missing(df: pd.DataFrame, expected: pd.DataFrame) -> pd.DataFrame:
    key = ["method", "space", "budget", "seed"]
    have = set(map(tuple, df[key].itertuples(index=False))) if len(df) else set()
    mask = np.array([tuple(r) not in have for r in expected[key].itertuples(index=False)], bool)
    return expected[mask].reset_index(drop=True)
