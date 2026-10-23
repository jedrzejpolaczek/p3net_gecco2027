"""NB201 inference-energy table (card `benchmarks.md`, BM-2; interfaces §7, Q-32).

The table is built once from the measurement log of
`implementation/experiments/scripts/measure_nb201_energy.py` (`build_energy_table`) and
read by the NB201 substrate as f2. Values are drift-corrected: the energy of a cell
divided by the energy of the reference cell interpolated at its position in the
measurement order (pilot 2026-10-17/18), i.e. dimensionless; dominance and ranks do
not depend on the scale.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

from p3net.problem.genotype import Genotype

OPS = ("none", "skip_connect", "nor_conv_1x1", "nor_conv_3x3", "avg_pool_3x3")
DEFAULT_TABLE = (Path(__file__).resolve().parents[4] / "experiments" / "results" / "benchmark_tables"
                 / "nb201_energy.json")


def arch_str(g: Genotype) -> str:
    """NB201 arch string of a cell genotype -- values given as operation names or as
    indices into OPS (edges in the order (0,1), (0,2), (1,2), (0,3), (1,3), (2,3))."""
    o = [v if isinstance(v, str) else OPS[int(v)] for v in g.values[:6]]
    return f"|{o[0]}~0|+|{o[1]}~0|{o[2]}~1|+|{o[3]}~0|{o[4]}~1|{o[5]}~2|"


def _corrected(records: list[dict]) -> dict[str, float]:
    refs = sorted((r["seq"], r["energy_j"]) for r in records if r.get("reference"))
    out = {}
    for r in records:
        if r.get("reference"):
            continue
        s = r["seq"]
        lo = max((x for x in refs if x[0] < s), default=refs[0])
        hi = min((x for x in refs if x[0] > s), default=refs[-1])
        w = 0.0 if hi[0] == lo[0] else (s - lo[0]) / (hi[0] - lo[0])
        out[r["arch"]] = r["energy_j"] / (lo[1] + w * (hi[1] - lo[1]))
    return out


def build_energy_table(log_path: str | Path, out_path: str | Path = DEFAULT_TABLE, *, tag: str = "full",
                       qc_tags: tuple[str, str] | None = None) -> dict:
    """Collect the `tag` measurements into the table; `qc_tags` = (first, repeat) runs of
    the quality control (BM-2: >= 50 re-measured cells, Spearman >= 0.95, median
    relative difference <= 3 %)."""
    recs = [json.loads(line) for line in Path(log_path).read_text(encoding="utf-8").splitlines()]
    mine = [r for r in recs if r.get("tag") == tag]
    meta = next((r["metadata"] for r in mine if "metadata" in r), {})
    table = _corrected(mine)
    qc = None
    if qc_tags:
        a = _corrected([r for r in recs if r.get("tag") == qc_tags[0]])
        b = _corrected([r for r in recs if r.get("tag") == qc_tags[1]])
        common = sorted(set(a) & set(b))
        from scipy.stats import spearmanr

        qc = {"n_remeasured": len(common),
              "spearman": float(spearmanr([a[k] for k in common], [b[k] for k in common]).statistic),
              "median_rel_diff": statistics.median(abs(a[k] - b[k]) / ((a[k] + b[k]) / 2) for k in common)}
    temps = [t for r in mine if not r.get("reference") for t in r.get("temperature_c", [])]
    meta = {**meta, "quality_control": qc, "temperature_log": temps, "value": "energy / reference energy",
            "n_cells": len(table)}
    payload = {"metadata": meta, "energy": table}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(payload), encoding="utf-8")
    return payload


class NB201Energy:
    def __init__(self, path: str | Path = DEFAULT_TABLE):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"NB201 energy table not built yet: {path} (benchmarks.md BM-2)")
        data = json.loads(path.read_text(encoding="utf-8"))
        self._meta, self._energy = data["metadata"], data["energy"]

    def __len__(self) -> int:
        return len(self._energy)

    def metadata(self) -> dict:
        return dict(self._meta)

    def energy(self, g: Genotype) -> float:
        return float(self._energy[arch_str(g)])
