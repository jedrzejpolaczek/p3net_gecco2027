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


@pytest.mark.benchmark_data
def test_WBM2_nb201_f2_from_complete_energy_table():
    """W-BM2 (BM-2, #28; interfaces §7 Q-32): f2 = value from the energy
    table; the table covers all 15 625 architectures and records the
    hardware and measurement settings (power limit, clock locking, energy
    method, batch size, temperature log)."""
    from p3net.v005 import benchmarks

    table = benchmarks.NB201Energy()
    assert len(table) == 15625
    meta = table.metadata()
    for key in ("gpu_model", "driver", "cuda", "torch"):
        assert meta.get(key), f"missing hardware metadata {key}"
    for key in ("power_limit_w", "clocks_locked", "energy_method", "batch_size", "temperature_log"):
        assert key in meta and meta[key] is not None, f"missing measurement metadata {key}"
    assert meta["energy_method"] in ("counter", "power_integral")
    assert isinstance(meta["clocks_locked"], bool)
    assert float(meta["power_limit_w"]) > 0
    assert int(meta["batch_size"]) > 0
    assert len(meta["temperature_log"]) > 0
    sub = _substrate("NASBench201Substrate", "substrates.nas_bench_201")
    g = _cell_space("NB201").sample_uniform(random.Random(1))
    assert sub.objectives(g)[1] == table.energy(g)


@pytest.mark.benchmark_data
def test_WBM3_energy_measurement_protocol_and_quality():
    """W-BM3 (BM-2; Bartnik Tab. 6.2-6.3, final settings after pilot 4,
    2026-10-17: 3 warm-up + 5 measured passes, median; Q-47): N_warmup = 3,
    N_samples = 5, median; clocks locked at 1200 MHz, drift correction by the
    reference cell (3, 2, 1, 4, 3, 2) every 5 architectures, re-measure at
    spread > 8 % at most twice; quality control: Spearman >= 0.95 and median
    relative difference <= 3 % on 50 re-measured architectures."""
    from p3net.v005 import benchmarks

    meta = benchmarks.NB201Energy().metadata()
    assert meta["n_warmup"] == 3 and meta["n_samples"] == 5 and meta["aggregate"] == "median"
    qc = meta["quality_control"]
    assert qc["n_remeasured"] >= 50
    assert qc["spearman"] >= 0.95
    assert qc["median_rel_diff"] <= 0.03
    # settings fixed after the pilots (card BM-2, interfaces supplement 2026-10-21, Q-47)
    assert meta["clocks_locked"] is True
    assert meta["clock_lock_mhz"] == 1200
    mod = _exp("search_spaces.nas_bench_201_genotype")
    ops = list(mod.nas_bench_201_search_space().domains[0].values)
    assert meta["reference_arch"] == mod.genotype_to_arch_str(
        tuple(ops[i] for i in (3, 2, 1, 4, 3, 2))
    )
    assert meta["ref_every"] == 5
    assert meta["max_spread"] == 0.08
    assert meta["max_retries"] == 2


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
    Space from `rec["search_space"]`; JAHS iff it starts with "jahs" (Q-50)."""
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
        if str(rec["search_space"]).lower().startswith("jahs"):
            for f in ("peak_memory_server_mb", "surrogate_load_seconds"):
                assert not _empty(res.get(f)), f"{p.name}: empty JAHS resource field {f}"


def _empty(v) -> bool:
    """A resource field is empty when missing, None, "" or []; 0 / 0.0 is a value."""
    return v is None or (isinstance(v, (str, list)) and len(v) == 0)


def test_WBM7_zero_is_not_an_empty_resource_field():
    """W-BM7 helper guard (round 7): 0.0 (e.g. surrogate_load_seconds when the
    JAHS bridge was loaded by an earlier run) counts as recorded."""
    assert not _empty(0.0) and not _empty(0)
    assert _empty(None) and _empty("") and _empty([])
