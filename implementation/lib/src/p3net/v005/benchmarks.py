"""NB201 inference-energy table (card `benchmarks.md`, BM-2; interfaces §7, Q-32).

v005 (decision P1 a, 2026-10-31): the table is built once from HW-NAS-Bench
(Li et al., ICLR 2021; MIT) by `build_energy_table_hwnasbench` -- `edgegpu_energy`,
Jetson TX2, TensorRT, batch 1, CIFAR-10, mJ per image -- and read by the NB201
substrate as f2.

`build_energy_table` (own laptop measurement, pilots 1-5, 2026-10-17...29) is kept
as the record of the abandoned measurement: drift-corrected, dimensionless values.
"""

from __future__ import annotations

import hashlib
import json
import pickle
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


#: HW-NAS-Bench-v1_0.pickle from github.com/GATECH-EIC/HW-NAS-Bench (checked 2026-10-30,
#: notes/plans/v005-hwnasbench-check.md).
HWNASBENCH_SHA256 = "57f92c2d7b88814fa337d00f4597c8ca30d507c5a855c18d6fac57e5ad872700"
HWNASBENCH_METRIC = "edgegpu_energy"


class _NumpyOnlyUnpickler(pickle.Unpickler):
    """The pickle holds only dicts, lists, str, floats and numpy arrays; anything else
    is refused, so loading cannot run foreign code."""

    _ALLOWED = {("numpy.core.multiarray", "_reconstruct"), ("numpy._core.multiarray", "_reconstruct"),
                ("numpy", "ndarray"), ("numpy", "dtype")}

    def find_class(self, module, name):
        if (module, name) not in self._ALLOWED:
            raise pickle.UnpicklingError(f"HW-NAS-Bench pickle: class {module}.{name} not allowed")
        if module == "numpy.core.multiarray":
            import numpy

            if int(numpy.__version__.split(".")[0]) >= 2:
                module = "numpy._core.multiarray"
        return super().find_class(module, name)


def build_energy_table_hwnasbench(pickle_path: str | Path, out_path: str | Path = DEFAULT_TABLE, *,
                                  dataset: str = "cifar10", nats_index=None) -> dict:
    """f2 table from HW-NAS-Bench (BM-2, decision P1 a): `edgegpu_energy` [mJ/image] keyed
    by the NB201 arch string of each entry's `config`. `nats_index` (optional, e.g.
    `api.query_index_by_arch` of nats_bench) is used to check that the HW-NAS-Bench index
    of every entry is the NATS-Bench index of its arch string; the count of mismatches
    goes to the metadata."""
    raw = Path(pickle_path).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != HWNASBENCH_SHA256:
        raise ValueError(f"HW-NAS-Bench pickle sha256 {sha} != expected {HWNASBENCH_SHA256}")
    import io

    data = _NumpyOnlyUnpickler(io.BytesIO(raw)).load()["nasbench201"][dataset]
    configs, values = data["config"], data[HWNASBENCH_METRIC]
    net_keys = ("name", "C", "N", "num_classes")
    if len({tuple(c[k] for k in net_keys) for c in configs}) != 1:
        raise ValueError("HW-NAS-Bench entries describe different macro networks")
    table = {}
    for cfg, v in zip(configs, values, strict=True):
        a = cfg["arch_str"]
        if a in table:
            raise ValueError(f"duplicate arch_str in HW-NAS-Bench: {a}")
        table[a] = float(v)
    mismatches = None
    if nats_index is not None:
        mismatches = sum(int(nats_index(cfg["arch_str"])) != i for i, cfg in enumerate(configs))
    meta = {
        "source": "HW-NAS-Bench v1.0 (Li et al., ICLR 2021), github.com/GATECH-EIC/HW-NAS-Bench, MIT",
        "source_file": "HW-NAS-Bench-v1_0.pickle",
        "source_sha256": sha,
        "metric": HWNASBENCH_METRIC,
        "dataset": dataset,
        "device": "NVIDIA Jetson TX2 (edge GPU)",
        "runtime": "TensorRT",
        "batch_size": 1,
        "input_resolution": 32,
        "unit": "mJ per image",
        "value": "energy as published (not measured by us)",
        "network": {k: configs[0][k] for k in net_keys},
        "index_mismatches_vs_nats": mismatches,
        "decision": "benchmarks.md BM-2, v005-todo.md P1 a (2026-10-31)",
        "n_cells": len(table),
    }
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
