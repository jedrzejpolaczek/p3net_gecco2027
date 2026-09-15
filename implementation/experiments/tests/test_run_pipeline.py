"""Tests for scripts.run_pipeline -- crash safety and resumption.

Every test drives the real Pipeline against a fake substrate and real
run_single/persist_run, injecting failures where a real crash would
happen. What is pinned: nothing completed is recomputed; nothing
incomplete is accepted as done; failures are recorded and retried up to a
limit; a run root is never resumed with different code or configs."""

from __future__ import annotations

import json

import pytest

from scripts import run_experiment
from scripts import run_pipeline as rp
from substrates.base import FidelityLevel, Substrate


class FakeSubstrate(Substrate):
    closed = 0

    def fidelity_ladder(self):
        return (FidelityLevel(rank=0, config={"epochs": 1}),)

    def query_f1(self, genotype, fidelity):
        return float(sum(1 for v in genotype.values if v != "none"))

    def analytic_f2(self, genotype):
        return float(len(genotype.values))

    def close(self):
        FakeSubstrate.closed += 1


SPACE_CONFIG = {"search_space": "nas_genotype", "substrate": "fake"}


def _points(n_seeds=3, methods=("random_search",), budget=12):
    return [
        rp.Point("stage", m, "fake_space", budget, seed)
        for m in methods
        for seed in range(1, n_seeds + 1)
    ]


class CountingRunSingle:
    """Real run_single, counting calls and optionally raising on chosen calls."""

    def __init__(self, fail_on_calls=(), exc=RuntimeError("boom")):
        self.calls = 0
        self.fail_on_calls = set(fail_on_calls)
        self.exc = exc
        self.seen = []

    def __call__(self, method_config, space_config, budget, seed, *, substrate):
        self.calls += 1
        self.seen.append((method_config["method"], seed))
        if self.calls in self.fail_on_calls:
            raise self.exc
        return run_experiment.run_single(
            method_config, space_config, budget, seed, substrate=substrate
        )


def _pipeline(tmp_path, run_single, **kwargs):
    return rp.Pipeline(
        run_root=tmp_path / "run",
        run_single=run_single,
        load_method_config=lambda name: {"method": name, "params": {}},
        load_search_space_config=lambda name: SPACE_CONFIG,
        build_substrate=lambda cfg: FakeSubstrate(),
        log=lambda msg: None,
        **kwargs,
    )


def test_full_stage_writes_every_point(tmp_path):
    runner = CountingRunSingle()
    report = _pipeline(tmp_path, runner).run_stage("stage", _points())
    assert report.done and report.ran == 3
    assert len(list((tmp_path / "run" / "raw").glob("*.json"))) == 3
    assert not list((tmp_path / "run" / "raw").glob("*.tmp"))


def test_resume_after_crash_runs_only_what_is_missing(tmp_path):
    """A hard crash (here: KeyboardInterrupt, which the pipeline does not
    swallow) partway through; the rerun must not repeat completed points."""
    first = CountingRunSingle(fail_on_calls={3}, exc=KeyboardInterrupt())
    with pytest.raises(KeyboardInterrupt):
        _pipeline(tmp_path, first).run_stage("stage", _points(n_seeds=5))
    assert len(list((tmp_path / "run" / "raw").glob("*.json"))) == 2

    second = CountingRunSingle()
    report = _pipeline(tmp_path, second).run_stage("stage", _points(n_seeds=5))
    assert report.done
    assert second.calls == 3
    assert {seed for _, seed in second.seen} == {3, 4, 5}


def test_truncated_file_is_quarantined_and_rerun(tmp_path):
    runner = CountingRunSingle()
    _pipeline(tmp_path, runner).run_stage("stage", _points())
    victim = tmp_path / "run" / "raw" / _points()[1].filename
    victim.write_text(victim.read_text(encoding="utf-8")[:40], encoding="utf-8")

    again = CountingRunSingle()
    report = _pipeline(tmp_path, again).run_stage("stage", _points())
    assert report.done and report.quarantined == 1 and again.calls == 1
    assert len(list((tmp_path / "run" / "quarantine").glob("*.json"))) == 1
    assert rp.validate_run_file(victim, _points()[1]) is None


def test_file_for_the_wrong_point_is_not_accepted(tmp_path):
    runner = CountingRunSingle()
    _pipeline(tmp_path, runner).run_stage("stage", _points())
    a, b = _points()[0], _points()[1]
    raw = tmp_path / "run" / "raw"
    (raw / b.filename).write_text((raw / a.filename).read_text(encoding="utf-8"), encoding="utf-8")
    assert rp.validate_run_file(raw / b.filename, b) is not None


def test_leftover_temp_files_are_removed(tmp_path):
    pipeline = _pipeline(tmp_path, CountingRunSingle())
    raw = tmp_path / "run" / "raw"
    raw.mkdir(parents=True)
    (raw / "x__y__budget1__seed1.json.tmp").write_text("{", encoding="utf-8")
    assert pipeline.remove_temp_files() == 1
    assert not list(raw.glob("*.tmp"))


def test_failure_is_recorded_skipped_and_retried_next_time(tmp_path):
    FakeSubstrate.closed = 0
    runner = CountingRunSingle(fail_on_calls={2})
    report = _pipeline(tmp_path, runner).run_stage("stage", _points())
    assert report.failed_now == 1 and report.complete == 2 and not report.done
    ledger = (tmp_path / "run" / "failures.jsonl").read_text(encoding="utf-8").splitlines()
    record = json.loads(ledger[0])
    assert record["event"] == "failure" and "RuntimeError: boom" in record["error"]
    assert "Traceback" in record["traceback"]
    assert FakeSubstrate.closed >= 1  # substrate rebuilt after the failure

    retry = CountingRunSingle()
    report = _pipeline(tmp_path, retry).run_stage("stage", _points())
    assert report.done and retry.calls == 1


def test_point_is_given_up_after_max_retries_and_reset_by_retry_failed(tmp_path):
    points = _points(n_seeds=1)
    for _ in range(2):
        _pipeline(tmp_path, CountingRunSingle(fail_on_calls={1}), max_retries=2).run_stage(
            "stage", points
        )
    blocked = CountingRunSingle()
    report = _pipeline(tmp_path, blocked, max_retries=2).run_stage("stage", points)
    assert blocked.calls == 0 and report.given_up == 1 and not report.done

    reset = CountingRunSingle()
    report = _pipeline(tmp_path, reset, max_retries=2, retry_failed=True).run_stage("stage", points)
    assert reset.calls == 1 and report.done


def test_ledger_ignores_a_line_cut_short_by_a_crash(tmp_path):
    path = tmp_path / "failures.jsonl"
    path.write_text('{"event": "failure", "key": "a"}\n{"event": "fail', encoding="utf-8")
    assert rp.FailureLedger(path).attempts == {"a": 1}


def test_manifest_refuses_resume_with_changed_code_or_configs():
    base = {
        "plan_hash": "p",
        "git": {"commit": "c1", "diff_hash": None},
        "config_hashes": {"methods/p3net": "h1"},
    }
    assert rp.manifest_mismatches(base, base) == []
    assert rp.manifest_mismatches(base, base | {"plan_hash": "p2"})
    assert rp.manifest_mismatches(base, base | {"git": {"commit": "c2", "diff_hash": None}})
    assert rp.manifest_mismatches(base, base | {"git": {"commit": "c1", "diff_hash": "d"}})
    assert rp.manifest_mismatches(base, base | {"config_hashes": {"methods/p3net": "h2"}})


def test_persist_run_is_atomic_and_leaves_no_temp_file(tmp_path, monkeypatch):
    monkeypatch.setitem(run_experiment._SUBSTRATE_BUILDERS, "fake", lambda cfg: FakeSubstrate())
    result = run_experiment.run_single(
        {"method": "random_search", "params": {}}, SPACE_CONFIG, 10, 1
    )
    path = run_experiment.persist_run(
        result,
        method_name="random_search",
        search_space_name="s",
        budget=10,
        seed=1,
        out_dir=tmp_path,
    )
    assert path.exists() and not list(tmp_path.glob("*.tmp"))

    def exploding_replace(src, dst):
        raise OSError("disk yanked")

    monkeypatch.setattr(run_experiment.os, "replace", exploding_replace)
    with pytest.raises(OSError):
        run_experiment.persist_run(
            result,
            method_name="random_search",
            search_space_name="s",
            budget=10,
            seed=2,
            out_dir=tmp_path,
        )
    assert not (tmp_path / "random_search__s__budget10__seed2.json").exists()


def test_plan_expands_seed_ranges_and_every_stage_is_well_formed():
    plan = rp.load_plan(rp.DEFAULT_PLAN)
    stages = {s["name"]: s for s in plan["stages"]}
    heldout = rp.expand_stage(stages["s6_heldout_seeds"])
    assert {p.seed for p in heldout} == set(range(31, 61))
    headline = rp.expand_stage(stages["s1_headline"])
    comparison = plan["method_groups"]["comparison"]
    assert len(headline) == len(comparison) * 4 * 4 * 30
    # no grid point belongs to two stages (each writes one file per point)
    grid_keys = [
        p.key for s in plan["stages"] if s.get("kind") == "grid" for p in rp.expand_stage(s)
    ]
    assert len(grid_keys) == len(set(grid_keys))
    # confirmation covers every arm of the comparison, the final engine and
    # the multi-fidelity track (all arms, plan decision)
    groups = plan["method_groups"]
    assert set(rp.stage_methods(stages["s6_heldout_seeds"])) == set(
        groups["comparison"] + groups["final"] + groups["multi_fidelity"]
    )
    # D6: NAS-Bench-201 is P3Net diagnostics only
    assert "botorch_qnehvi" not in rp.stage_methods(stages["s5_nas_bench_201"])


def test_stage_methods_flattens_groups_and_removes_duplicates():
    stage = {"methods": [["a", "b"], "c", ["b", ["d"]]]}
    assert rp.stage_methods(stage) == ["a", "b", "c", "d"]


# ---------------------------------------------------------------------------
# Parallel workers: locks and resource slots
# ---------------------------------------------------------------------------


def _write_lock(path, pid, host=None):
    import platform

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"pid": pid, "host": host or platform.node(), "at": "x"}))


def _dead_pid():
    import psutil

    pid = 999_999
    while psutil.pid_exists(pid):
        pid += 1
    return pid


def test_lock_is_exclusive_and_released(tmp_path):
    lock = tmp_path / "locks" / "a.lock"
    assert rp.try_lock(lock)
    assert not rp.try_lock(lock)
    rp.release_lock(lock)
    assert rp.try_lock(lock)


def test_lock_of_a_dead_process_is_broken_but_a_live_or_remote_one_is_not(tmp_path):
    import os

    stale = tmp_path / "locks" / "stale.lock"
    _write_lock(stale, _dead_pid())
    assert rp.try_lock(stale)

    live = tmp_path / "locks" / "live.lock"
    _write_lock(live, os.getpid())
    assert not rp.try_lock(live)

    remote = tmp_path / "locks" / "remote.lock"
    _write_lock(remote, _dead_pid(), host="some-other-machine")
    assert not rp.try_lock(remote)


def test_point_held_by_another_worker_is_left_alone(tmp_path):
    import os

    runner = CountingRunSingle()
    pipeline = _pipeline(tmp_path, runner)
    points = _points(n_seeds=3)
    foreign = pipeline.lock_dir / f"{points[1].key}.lock"
    _write_lock(foreign, os.getpid())
    report = pipeline.run_stage("stage", points)
    assert report.ran == 2 and report.busy == 1
    assert not (pipeline.raw_dir / points[1].filename).exists()
    assert foreign.exists()


def test_slot_limits_how_many_points_of_a_method_run_at_once(tmp_path):
    import os

    runner = CountingRunSingle()
    pipeline = _pipeline(tmp_path, runner, slots={"gpu": {"capacity": 1, "methods": ["mo_ls"]}})
    points = _points(n_seeds=2, methods=("random_search", "mo_ls"))
    slot = pipeline.lock_dir / "slot-gpu-0.lock"
    _write_lock(slot, os.getpid())  # held by another worker's GPU run
    report = pipeline.run_stage("stage", points)
    assert {m for m, _ in runner.seen} == {"random_search"}
    assert report.busy == 2
    rp.release_lock(slot)
    report = pipeline.run_stage("stage", points)
    assert report.complete == 4
    assert not list(pipeline.lock_dir.glob("*.lock"))


def test_point_finished_by_another_worker_after_classification_is_not_rerun(tmp_path):
    runner = CountingRunSingle()
    pipeline = _pipeline(tmp_path, runner)
    points = _points(n_seeds=1)
    other = _pipeline(tmp_path, CountingRunSingle())
    original_claim = pipeline._claim

    def claim_after_other_finished(point):
        other.run_stage("stage", points)  # another worker completes it meanwhile
        return original_claim(point)

    pipeline._claim = claim_after_other_finished
    report = pipeline.run_stage("stage", points)
    assert runner.calls == 0 and report.complete == 1


def test_plan_parallel_section_is_well_formed():
    plan = rp.load_plan(rp.DEFAULT_PLAN)
    parallel = plan["parallel"]
    assert parallel["workers"] >= 1 and parallel["threads_per_run"] >= 1
    for spec in parallel["slots"].values():
        assert spec["capacity"] >= 1 and spec["methods"]
    timing = [s for s in plan["stages"] if s.get("kind") == "timing"]
    assert timing and all(rp.expand_stage(s) for s in timing)
