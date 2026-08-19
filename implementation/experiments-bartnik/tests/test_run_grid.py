"""Tests for scripts.run_grid -- grid enumeration and skip-cached
dispatch. (Gap in the original task list -- adding it.)"""

import json

from scripts import run_experiment, run_grid
from substrates.base import FidelityLevel, Substrate


class FakeSubstrate(Substrate):
    def fidelity_ladder(self):
        return (FidelityLevel(rank=0, config={"epochs": 1}),)

    def query_f1(self, genotype, fidelity):
        return float(sum(1 for v in genotype.values if v != "none"))

    def analytic_f2(self, genotype):
        return float(len(genotype.values))


def test_enumerate_grid_is_the_full_cross_product(monkeypatch):
    monkeypatch.setattr(
        run_grid, "load_budgets_config", lambda: {"budget_tiers": [10, 20], "seeds": [1, 2, 3]}
    )
    points = run_grid.enumerate_grid(
        methods=["p3net", "random_search"], search_spaces=["jahs_bench_201"]
    )
    assert len(points) == 2 * 1 * 2 * 3
    assert all(p.search_space == "jahs_bench_201" for p in points)


def test_enumerate_grid_defaults_to_every_config_file_on_disk():
    points = run_grid.enumerate_grid()
    method_names = {p.method for p in points}
    space_names = {p.search_space for p in points}
    assert "p3net" in method_names
    assert "random_search" in method_names
    # All four of JAHS-Bench-201's own dataset variants (cifar10 plus the
    # colorectal-histology/fashion-mnist robustness checks) are in scope by
    # default alongside NAS-HPO-Bench-II, per the 2026-08-16 decision to
    # extend the main comparison grid across JAHS-Bench-201's built-in
    # dataset family (chapters/v003/conclusions/main.tex, Limitations).
    assert space_names == {
        "jahs_bench_201",
        "jahs_bench_201_colorectal",
        "jahs_bench_201_fashion",
        "nas_hpo_bench_ii",
    }


def test_enumerate_grid_excludes_not_yet_implemented_methods_by_default():
    points = run_grid.enumerate_grid()
    assert "nsganetv2_continuous" not in {p.method for p in points}
    # explicitly requesting it is still honoured -- the exclusion is only
    # a default, not a hard block, since a caller might still want to
    # exercise the documented-placeholder error path deliberately.
    explicit = run_grid.enumerate_grid(
        methods=["nsganetv2_continuous"], search_spaces=["jahs_bench_201"]
    )
    assert {p.method for p in explicit} == {"nsganetv2_continuous"}


def test_enumerate_grid_excludes_default_grid_false_search_spaces_by_default():
    """glimmering-swimming-book.md, Faza 3: nas_bench_201 is a genuinely
    separate, single-axis isolation experiment (Conclusions, "Why the
    results are what they are"), not part of the main comparison grid --
    same `default_grid: false` mechanism configs/methods/*.yaml already
    uses, now also honoured for configs/search_spaces/*.yaml so a plain
    `run_grid.py` with no flags doesn't silently try to query real
    NATS-Bench data most environments won't have downloaded."""
    points = run_grid.enumerate_grid()
    assert "nas_bench_201" not in {p.search_space for p in points}
    # explicit request still honoured, same as the methods-side exclusion.
    explicit = run_grid.enumerate_grid(methods=["p3net"], search_spaces=["nas_bench_201"])
    assert {p.search_space for p in explicit} == {"nas_bench_201"}


def test_enumerate_grid_budgets_defaults_to_the_full_tier_list(monkeypatch):
    monkeypatch.setattr(
        run_grid, "load_budgets_config", lambda: {"budget_tiers": [10, 20, 30], "seeds": [1]}
    )
    points = run_grid.enumerate_grid(methods=["p3net"], search_spaces=["jahs_bench_201"])
    assert {p.budget for p in points} == {10, 20, 30}


def test_enumerate_grid_budgets_can_be_restricted_to_a_subset(monkeypatch):
    monkeypatch.setattr(
        run_grid, "load_budgets_config", lambda: {"budget_tiers": [10, 20, 30], "seeds": [1]}
    )
    points = run_grid.enumerate_grid(
        methods=["p3net"], search_spaces=["jahs_bench_201"], budgets=[10, 30]
    )
    assert {p.budget for p in points} == {10, 30}


def test_run_grid_writes_one_file_per_point_and_skips_on_rerun(tmp_path, monkeypatch):
    monkeypatch.setitem(run_experiment._SUBSTRATE_BUILDERS, "fake", lambda cfg: FakeSubstrate())
    monkeypatch.setattr(run_experiment, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(
        run_grid,
        "load_search_space_config",
        lambda name: {"search_space": "nas_genotype", "substrate": "fake"},
    )
    monkeypatch.setattr(
        run_grid, "load_method_config", lambda name: {"method": "random_search", "params": {}}
    )

    points = [
        run_grid.GridPoint(method="random_search", search_space="fake_space", budget=5, seed=seed)
        for seed in (1, 2)
    ]
    written, skipped = run_grid.run_grid(points)
    assert len(written) == 2
    assert len(skipped) == 0
    for path in written:
        payload = json.loads(path.read_text())
        assert payload["evaluations_used"] == 5

    written_again, skipped_again = run_grid.run_grid(points)
    assert len(written_again) == 0
    assert len(skipped_again) == 2


def test_run_grid_does_not_skip_when_told_not_to(tmp_path, monkeypatch):
    monkeypatch.setitem(run_experiment._SUBSTRATE_BUILDERS, "fake", lambda cfg: FakeSubstrate())
    monkeypatch.setattr(run_experiment, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(
        run_grid,
        "load_search_space_config",
        lambda name: {"search_space": "nas_genotype", "substrate": "fake"},
    )
    monkeypatch.setattr(
        run_grid, "load_method_config", lambda name: {"method": "random_search", "params": {}}
    )

    points = [
        run_grid.GridPoint(method="random_search", search_space="fake_space", budget=5, seed=1)
    ]
    run_grid.run_grid(points)
    written_again, skipped_again = run_grid.run_grid(points, skip_cached=False)
    assert len(written_again) == 1
    assert len(skipped_again) == 0


def test_format_duration_renders_seconds_minutes_and_hours():
    assert run_grid._format_duration(0) == "0s"
    assert run_grid._format_duration(45) == "45s"
    assert run_grid._format_duration(90) == "1m30s"
    assert run_grid._format_duration(3661) == "1h01m01s"


def test_run_grid_prints_nothing_by_default(tmp_path, monkeypatch, capsys):
    monkeypatch.setitem(run_experiment._SUBSTRATE_BUILDERS, "fake", lambda cfg: FakeSubstrate())
    monkeypatch.setattr(run_experiment, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(
        run_grid,
        "load_search_space_config",
        lambda name: {"search_space": "nas_genotype", "substrate": "fake"},
    )
    monkeypatch.setattr(
        run_grid, "load_method_config", lambda name: {"method": "random_search", "params": {}}
    )

    points = [
        run_grid.GridPoint(method="random_search", search_space="fake_space", budget=5, seed=1)
    ]
    run_grid.run_grid(points)
    assert capsys.readouterr().out == ""


def test_run_grid_show_progress_prints_a_progress_bar(tmp_path, monkeypatch, capsys):
    monkeypatch.setitem(run_experiment._SUBSTRATE_BUILDERS, "fake", lambda cfg: FakeSubstrate())
    monkeypatch.setattr(run_experiment, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(
        run_grid,
        "load_search_space_config",
        lambda name: {"search_space": "nas_genotype", "substrate": "fake"},
    )
    monkeypatch.setattr(
        run_grid, "load_method_config", lambda name: {"method": "random_search", "params": {}}
    )

    points = [
        run_grid.GridPoint(method="random_search", search_space="fake_space", budget=5, seed=seed)
        for seed in (1, 2)
    ]
    run_grid.run_grid(points, show_progress=True)
    out = capsys.readouterr().out
    assert "2/2" in out
    assert "100%" in out
    assert "random_search/fake_space" in out


class CountingClosableFakeSubstrate(FakeSubstrate):
    """Tracks how many instances get built and whether each was closed --
    the thing that would catch a regression back to "one Substrate per
    grid point" (see run_grid.py's module docstring: rebuilding
    JAHS-Bench-201's real Substrate per point would pay its several-minute
    subprocess-startup cost hundreds of times over)."""

    instances: list["CountingClosableFakeSubstrate"] = []

    def __init__(self):
        self.closed = False
        CountingClosableFakeSubstrate.instances.append(self)

    def close(self):
        self.closed = True


def test_run_grid_reuses_one_substrate_per_search_space_and_closes_it(tmp_path, monkeypatch):
    CountingClosableFakeSubstrate.instances = []
    monkeypatch.setitem(
        run_experiment._SUBSTRATE_BUILDERS,
        "fake",
        lambda cfg: CountingClosableFakeSubstrate(),
    )
    monkeypatch.setattr(run_experiment, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(
        run_grid,
        "load_search_space_config",
        lambda name: {"search_space": "nas_genotype", "substrate": "fake"},
    )
    monkeypatch.setattr(
        run_grid, "load_method_config", lambda name: {"method": "random_search", "params": {}}
    )

    # 3 points, all the same search_space, different seeds -- should
    # share exactly one Substrate instance, not build one each.
    points = [
        run_grid.GridPoint(method="random_search", search_space="fake_space", budget=5, seed=seed)
        for seed in (1, 2, 3)
    ]
    written, _skipped = run_grid.run_grid(points)
    assert len(written) == 3
    assert len(CountingClosableFakeSubstrate.instances) == 1
    assert CountingClosableFakeSubstrate.instances[0].closed is True


def test_run_grid_builds_one_substrate_per_distinct_search_space(tmp_path, monkeypatch):
    CountingClosableFakeSubstrate.instances = []
    monkeypatch.setitem(
        run_experiment._SUBSTRATE_BUILDERS,
        "fake",
        lambda cfg: CountingClosableFakeSubstrate(),
    )
    monkeypatch.setattr(run_experiment, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(
        run_grid,
        "load_search_space_config",
        lambda name: {"search_space": "nas_genotype", "substrate": "fake"},
    )
    monkeypatch.setattr(
        run_grid, "load_method_config", lambda name: {"method": "random_search", "params": {}}
    )

    points = [
        run_grid.GridPoint(method="random_search", search_space="space_a", budget=5, seed=1),
        run_grid.GridPoint(method="random_search", search_space="space_b", budget=5, seed=1),
    ]
    written, _skipped = run_grid.run_grid(points)
    assert len(written) == 2
    assert len(CountingClosableFakeSubstrate.instances) == 2
    assert all(i.closed for i in CountingClosableFakeSubstrate.instances)
