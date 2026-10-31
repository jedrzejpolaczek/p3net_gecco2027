"""Level-1 tests for benchmarks and objectives (card
`notes/plans/v005-sources/benchmarks.md`, W-BM1-W-BM7).

Sources: NAS-Bench-201 (`cifar10-valid`, Dong & Yang 2020), JAHS-Bench-201,
NAS-HPO-Bench-II, FCNet; energy methodology of Bartnik 2026 §6.2 (pyNVML,
N_warmup = N_samples = 3, median). Card decisions BM-1 a, BM-2, BM-3, BM-4,
BM-5; #27, #28, #33.

Tests that need benchmark files are marked `benchmark_data` and skipped
when the data directory is absent. Substrate constructors and the energy
table API follow interfaces §7 (Q-32).
"""

from __future__ import annotations

import importlib
import itertools
import math
import random
import re
import sys
from pathlib import Path

import pytest

from p3net.problem.genotype import Genotype

from ._support import G

REPO = Path(__file__).resolve().parents[5]
EXP = REPO / "implementation" / "experiments"


def _exp(module: str):
    if str(EXP) not in sys.path:
        sys.path.insert(0, str(EXP))
    try:
        return importlib.import_module(module)
    except ImportError as e:  # experiments dependencies missing in this environment
        pytest.skip(f"cannot import {module}: {e}")


CELL_SPACES = {
    "JAHS": ("search_spaces.nas_genotype", "nas_search_space"),
    "NAS-HPO-II": ("search_spaces.nas_hpo_bench_ii_genotype", "nas_hpo_bench_ii_search_space"),
    "NB201": ("search_spaces.nas_bench_201_genotype", "nas_bench_201_search_space"),
}


def _cell_space(name):
    mod, fn = CELL_SPACES[name]
    return getattr(_exp(mod), fn)()


def _none_and_op(domain_values):
    vals = list(domain_values)
    none = vals.index("none")
    op = next(i for i, v in enumerate(vals) if v != "none")
    return none, op


def _mask_genotype(space, mask):
    """Edges 0..5 (card §2a: the first 6 coordinates are cell edges): True =
    a non-'none' operation, False = 'none'; other coordinates at index 0."""
    idx = []
    for i, d in enumerate(space.domains):
        if i < 6:
            none, op = _none_and_op(d.values)
            idx.append(op if mask[i] else none)
        else:
            idx.append(0)
    return G(*idx)


@pytest.mark.parametrize("name", list(CELL_SPACES))
def test_WBM6_validity_rejects_cells_without_path(name):
    """W-BM6 (#33): a cell with every edge 'none' is invalid; a cell with
    every edge an operation is valid."""
    from p3net.v005.common import is_valid

    space = _cell_space(name)
    assert is_valid(space, _mask_genotype(space, [False] * 6)) is False
    assert is_valid(space, _mask_genotype(space, [True] * 6)) is True


def test_WBM6_validity_same_rule_on_all_cell_spaces():
    """W-BM6 (#33: one rule for all): the number of valid none-patterns among
    the 2^6 edge masks is the same on JAHS, NAS-HPO-II and NB201 (a
    statistic independent of how each benchmark orders its edges), and the
    validity of a pattern does not depend on which operation is used."""
    from p3net.v005.common import is_valid

    counts = {}
    for name in CELL_SPACES:
        space = _cell_space(name)
        counts[name] = sum(
            is_valid(space, _mask_genotype(space, list(m)))
            for m in itertools.product([False, True], repeat=6)
        )
        rng = random.Random(0)
        for _ in range(100):
            mask = [rng.random() < 0.5 for _ in range(6)]
            base = is_valid(space, _mask_genotype(space, mask))
            idx = list(_mask_genotype(space, mask).values)
            for i in range(6):
                if mask[i]:
                    none, _ = _none_and_op(space.domains[i].values)
                    idx[i] = rng.choice(
                        [j for j in range(len(space.domains[i].values)) if j != none]
                    )
            assert is_valid(space, G(*idx)) == base
    assert len(set(counts.values())) == 1, counts
    assert 0 < next(iter(counts.values())) < 64


def test_WBM1_no_method_code_reads_the_test_split():
    """W-BM1 (#27): no v005 method code refers to the test split (static scan
    of `p3net/v005` for test-accuracy keys)."""
    import p3net

    root = Path(p3net.__file__).parent / "v005"
    assert root.is_dir(), "p3net.v005 does not exist yet"
    pat = re.compile(r"test[_-]?acc|ori-test|x-test|test_error|test-error", re.IGNORECASE)
    hits = [
        f"{p.relative_to(root)}:{i + 1}"
        for p in root.rglob("*.py")
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines())
        if pat.search(line)
    ]
    assert not hits, f"test split referenced in method code: {hits}"


def _substrate(cls_name, module):
    mod = _exp(module)
    try:
        return getattr(mod, cls_name)()
    except Exception as e:  # missing data or constructor arguments (Q-32)
        pytest.skip(f"cannot construct {cls_name}: {e}")


@pytest.mark.benchmark_data
def test_WBM1_nb201_f1_is_validation_error_mean_over_seeds():
    """W-BM1 (BM-1 a): NB201 f1 = 100 - validation accuracy of
    `cifar10-valid` (mean over seeds), never the test error."""
    sub = _substrate("NASBench201Substrate", "substrates.nas_bench_201")
    assert sub.f1_split() == "valid"
    space = _cell_space("NB201")
    rng = random.Random(0)
    for _ in range(20):
        g = space.sample_uniform(rng)
        m = sub.full_fidelity_metrics(g)
        f1 = sub.objectives(g)[0]
        assert abs(f1 - (100.0 - m["valid_acc"])) < 1e-9
        if abs(m["valid_acc"] - m["test_acc"]) > 1e-6:
            assert abs(f1 - (100.0 - m["test_acc"])) > 1e-9


HWNAS_SHA256_CARD = "57f92c2d7b88814fa337d00f4597c8ca30d507c5a855c18d6fac57e5ad872700"
HWNAS_PICKLE = EXP / "data" / "cache" / "hw_nas_bench" / "HW-NAS-Bench-v1_0.pickle"


@pytest.mark.benchmark_data
def test_WBM2_nb201_f2_from_complete_energy_table():
    """W-BM2 (BM-2, decision P1 a of 2026-10-31; interfaces supplement round
    8): f2 = value from the energy table built from HW-NAS-Bench
    `edgegpu_energy` (Jetson TX2, batch 1, CIFAR-10, mJ per image); the table
    covers all 15 625 cells and records its source."""
    from p3net.v005 import benchmarks

    table = benchmarks.NB201Energy()
    assert len(table) == 15625
    meta = table.metadata()
    for key in (
        "source",
        "source_file",
        "source_sha256",
        "metric",
        "dataset",
        "device",
        "runtime",
        "batch_size",
        "input_resolution",
        "unit",
        "network",
        "index_mismatches_vs_nats",
        "n_cells",
    ):
        assert key in meta and meta[key] is not None, f"missing source metadata {key}"
    assert meta["source_file"] == "HW-NAS-Bench-v1_0.pickle"
    assert meta["metric"] == "edgegpu_energy"
    assert meta["dataset"] == "cifar10"
    assert meta["batch_size"] == 1
    assert meta["input_resolution"] == 32
    assert meta["unit"] == "mJ per image"
    assert meta["n_cells"] == 15625
    assert {"name", "C", "N", "num_classes"} <= set(meta["network"])
    sub = _substrate("NASBench201Substrate", "substrates.nas_bench_201")
    g = _cell_space("NB201").sample_uniform(random.Random(1))
    assert sub.objectives(g)[1] == table.energy(g)


def _arch_to_genotype(arch_str):
    """'|op~0|+|op~0|op~1|+|...|' -> Genotype of op names in arch-string
    order (the NB201 coordinate order, checked by round trip)."""
    ops = tuple(
        tok.split("~")[0] for seg in arch_str.split("+") for tok in seg.strip("|").split("|")
    )
    mod = _exp("search_spaces.nas_bench_201_genotype")
    assert mod.genotype_to_arch_str(ops) == arch_str
    return Genotype(values=ops)


@pytest.mark.benchmark_data
def test_WBM3_energy_table_matches_hwnasbench_source():
    """W-BM3 (decision P1 a of 2026-10-31; replaces the laptop protocol):
    source file sha256 = 57f92c2d...ad872700 (= HWNASBENCH_SHA256 and the
    table's `source_sha256`); 0 index mismatches with NATS; for a sample of
    cells the table value = `["nasbench201"]["cifar10"]["edgegpu_energy"][i]`
    of the file, keyed by `config[i]["arch_str"]`."""
    import hashlib
    import pickle

    from p3net.v005 import benchmarks

    assert benchmarks.HWNASBENCH_SHA256 == HWNAS_SHA256_CARD
    table = benchmarks.NB201Energy()
    meta = table.metadata()
    assert meta["source_sha256"] == benchmarks.HWNASBENCH_SHA256
    assert meta["index_mismatches_vs_nats"] == 0
    if not HWNAS_PICKLE.is_file():
        pytest.skip(f"{HWNAS_PICKLE} not present")
    raw = HWNAS_PICKLE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == HWNAS_SHA256_CARD
    data = pickle.loads(raw)["nasbench201"]["cifar10"]  # noqa: S301 -- sha256 verified above
    configs, energy = data["config"], data["edgegpu_energy"]
    assert len(configs) == 15625
    rng = random.Random(0)
    for i in rng.sample(range(len(configs)), 300):
        g = _arch_to_genotype(configs[i]["arch_str"])
        assert math.isclose(table.energy(g), float(energy[i]), rel_tol=1e-9, abs_tol=1e-12), i


_PICKLE_LOADED = []


def _mark_loaded():
    """Called only if a test pickle is actually unpickled."""
    _PICKLE_LOADED.append(True)
    return None


class _Trap:
    def __reduce__(self):
        return (_mark_loaded, ())


def test_WBM3_wrong_sha256_rejected_before_unpickling(tmp_path):
    """W-BM3 (BM-2, interfaces round 8): a file whose sha256 is not
    HWNASBENCH_SHA256 raises ValueError and is never unpickled (the file is a
    pickle whose loading would record itself)."""
    import pickle

    from p3net.v005 import benchmarks

    bad = tmp_path / "HW-NAS-Bench-v1_0.pickle"
    bad.write_bytes(pickle.dumps({"nasbench201": _Trap()}))
    _PICKLE_LOADED.clear()
    with pytest.raises(ValueError):
        benchmarks.build_energy_table_hwnasbench(bad, out_path=tmp_path / "out.json")
    assert not _PICKLE_LOADED, "the file was unpickled before the sha256 check"
    assert not (tmp_path / "out.json").exists()


@pytest.mark.benchmark_data
def test_WBM4_jahs_f2_follows_bm3_check():
    """W-BM4 (BM-3, #26): the JAHS size check is recorded in
    implementation/experiments/results/checks/
    and f2 follows its rule: size_MB constant per cell -> f2 = size_MB;
    otherwise f2 = analytic parameter count (constant per cell)."""
    checks = list((EXP / "results" / "checks").glob("*jahs*size*"))
    assert checks, "BM-3 check result missing in implementation/experiments/results/checks/"
    sub = _substrate("JAHSBench201Substrate", "substrates.jahs_bench_201")
    space = _cell_space("JAHS")
    rng = random.Random(0)
    # substrates take genotypes with domain VALUES (as sample_uniform gives),
    # not the index genotypes of the v005 methods (Q-49a)
    g = list(space.sample_uniform(rng).values)
    f2 = set()
    for _ in range(10):
        for i in range(6, len(g)):
            g[i] = rng.choice(space.domains[i].values)
        f2.add(round(sub.objectives(Genotype(values=tuple(g)))[1], 9))
    assert len(f2) == 1, "JAHS f2 depends on hyperparameters at a fixed cell"


@pytest.mark.benchmark_data
@pytest.mark.parametrize(
    "cls_name,module,space_fn",
    [
        ("NASHPOBenchIISubstrate", "substrates.nas_hpo_bench_ii", "NAS-HPO-II"),
    ],
)
def test_WBM5_f1_validation_and_f2_low_fidelity(cls_name, module, space_fn):
    """W-BM5 (BM-4, MF-1 a): f1 from the validation split; f2 at e < E is the
    e-epoch observation (NAS-HPO-II: time recorded for e epochs), not the
    full-training value."""
    sub = _substrate(cls_name, module)
    assert sub.f1_split() == "valid"
    space = _cell_space(space_fn)
    g = space.sample_uniform(random.Random(2))
    E = sub.max_epochs()
    f2_full = sub.objectives(g)[1]
    f2_low = sub.objectives_at_epochs(g, max(1, E // 3))[1]
    assert f2_low < f2_full
    assert abs(f2_low - sub.training_seconds(g, max(1, E // 3))) < 1e-9


@pytest.mark.benchmark_data
def test_WBM5_fcnet_f2_scaled_by_epochs():
    """W-BM5 (MF-1 a): FCNet records only full-training time -> f2 at e
    epochs = time * e / E."""
    sub = _substrate("FCNetSubstrate", "substrates.fcnet")
    space = getattr(_exp("search_spaces.fcnet_genotype"), "fcnet_search_space")()
    g = space.sample_uniform(random.Random(3))
    E = sub.max_epochs()
    full = sub.objectives(g)[1]
    assert abs(sub.objectives_at_epochs(g, 25)[1] - full * 25 / E) < 1e-9 * max(1.0, full)
    assert sub.f1_split() == "valid"


@pytest.mark.benchmark_data
def test_WBM7_resource_fields_present_in_every_run_record():
    """W-BM7 (BM-5, #29; record schema of round 6, Q-49b/Q-50): every v005
    run record (`results/runs/*/raw/v005_*.json`) has top-level
    `resources` with non-empty `method_wall_seconds` and
    `peak_memory_process_mb`; on JAHS also non-empty `peak_memory_server_mb`
    and `surrogate_load_seconds` (#29: the JAHS bridge's memory and load time
    must be recorded; 0.0 is valid -- bridge already loaded by another run,
    round 7); `peak_memory_gpu_mb` may be None (no GPU on the target server).
    Space from `rec["search_space"]`; JAHS iff it starts with "jahs" (Q-50).
    Round 8 (P3 (2a)): `peak_memory_process_scope` in {"run", "process"};
    `peak_memory_server_method` in {"pss_sum", "rss_sum"} on JAHS, None
    elsewhere."""
    import json

    runs = list((EXP / "results" / "runs").glob("*/raw/v005_*.json"))
    if not runs:
        pytest.skip("no v005 run records yet")
    for p in runs:
        rec = json.loads(p.read_text(encoding="utf-8"))
        res = rec["resources"]
        for f in ("method_wall_seconds", "peak_memory_process_mb"):
            assert not _empty(res.get(f)), f"{p.name}: empty resource field {f}"
        assert "peak_memory_gpu_mb" in res, f"{p.name}: peak_memory_gpu_mb not recorded"
        assert res.get("peak_memory_process_scope") in ("run", "process"), p.name
        if str(rec["search_space"]).lower().startswith("jahs"):
            for f in ("peak_memory_server_mb", "surrogate_load_seconds"):
                assert not _empty(res.get(f)), f"{p.name}: empty JAHS resource field {f}"
            assert res.get("peak_memory_server_method") in ("pss_sum", "rss_sum"), p.name
        else:
            assert res.get("peak_memory_server_method") is None, p.name


def _empty(v) -> bool:
    """A resource field is empty when missing, None, "" or []; 0 / 0.0 is a value."""
    return v is None or (isinstance(v, (str, list)) and len(v) == 0)


def test_WBM7_zero_is_not_an_empty_resource_field():
    """W-BM7 helper guard (round 7): 0.0 (e.g. surrogate_load_seconds when the
    JAHS bridge was loaded by an earlier run) counts as recorded."""
    assert not _empty(0.0) and not _empty(0)
    assert _empty(None) and _empty("") and _empty([])


class _FakeSubstrate:
    def objectives(self, genotype):
        return (1.0, 1.0)


def _touch(n_mb):
    buf = bytearray(n_mb * 2**20)
    for i in range(0, len(buf), 4096):
        buf[i] = 1
    return buf


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="per-run peak reset is Linux-only")
def test_WBM7_run_peak_excludes_earlier_run_in_same_process():
    """W-BM7 (BM-5 supplement 2026-10-31, P3 (2a)): on Linux the process peak
    of a run is reset at its start (scope "run"), so a run that allocates
    ~10 MB after a run that allocated ~400 MB in the same process reports a
    clearly smaller peak."""
    resources = _exp("measurement.resources")

    def measure(n_mb):
        with resources.ResourceMeter(resources.TimedSubstrate(_FakeSubstrate())) as m:
            buf = _touch(n_mb)
            del buf
        return m.as_dict()

    big = measure(400)
    small = measure(10)
    assert big["process_peak_scope"] == "run" and small["process_peak_scope"] == "run"
    assert small["process_peak_rss_mb"] < big["process_peak_rss_mb"] - 200, (big, small)
