"""Level 2 (v005-level2-criteria.md, "Pętle Bag of Baselines"): our SH-EMOA vs the
authors' `shemoa.py` run unchanged (`bob_reference_runner.py`) on the Flowers-shaped
synthetic problem. Point P3NET_BOB_REPO to a clone of automl/multi-obj-baselines.
Criterion: median HV over 100 runs within +-2 % of the reference, TOST +-2 %."""

from __future__ import annotations

import json
import os
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _problems import hv  # noqa: E402
from bob_reference_runner import DOMAINS, flowers_like  # noqa: E402

REPO = os.environ.get("P3NET_BOB_REPO")
BUDGET, RUNS, REF = 100, 100, (13.0, 17.0)

pytestmark = pytest.mark.skipif(not REPO, reason="needs P3NET_BOB_REPO")


def _ours_shemoa(seed: int) -> float:
    from p3net.harness.runner import Observation, RunState
    from p3net.problem.genotype import CategoricalDomain, SearchSpace
    from p3net.v005.baselines.bob import SHEMOA

    raw, _ = flowers_like()
    space = SearchSpace(domains=tuple(CategoricalDomain(values=tuple(range(k))) for k in DOMAINS))
    m = SHEMOA(space, BUDGET, random.Random(seed), population_size=20)
    state, pts = RunState(), []
    while state.evaluations_used < BUDGET:
        props = m.propose(state)
        if not props:
            break
        new = [Observation(genotype=g, objectives=raw(g.values)) for g in props]
        pts.extend(o.objectives for o in new)
        state.evaluations_used += len(new)
        m.update(state, new)
    return hv(pts, REF)


def _check(name, ours, ref):
    med = float(np.median(ref))
    margin = 0.02 * med
    p_low = stats.ttest_ind(ours + margin, ref, equal_var=False, alternative="greater").pvalue
    p_high = stats.ttest_ind(ours - margin, ref, equal_var=False, alternative="less").pvalue
    print(f"{name}: ours median {np.median(ours):.3f} mean {ours.mean():.3f}; ref median {med:.3f} mean "
          f"{ref.mean():.3f}; MWU p {stats.mannwhitneyu(ours, ref).pvalue:.3f}; TOST p {max(p_low, p_high):.2e}")
    assert abs(float(np.median(ours)) - med) <= margin
    assert max(p_low, p_high) < 0.05


def test_level2_shemoa_vs_bob(tmp_path):
    out = tmp_path / "ref.json"
    subprocess.run([sys.executable, "-W", "ignore", str(HERE / "bob_reference_runner.py"), REPO, "shemoa",
                    str(BUDGET), str(RUNS), str(out)], check=True)
    ref = np.array([hv(r["points"], REF) for r in json.loads(out.read_text())])
    ours = np.array([_ours_shemoa(s) for s in range(RUNS)])
    _check("SH-EMOA", ours, ref)


def _ours_mobananas(seed: int) -> float:
    from p3net.harness.runner import Observation, RunState
    from p3net.problem.genotype import CategoricalDomain, SearchSpace
    from p3net.v005.baselines.bob import MOBANANAS

    raw, _ = flowers_like()
    space = SearchSpace(domains=tuple(CategoricalDomain(values=tuple(range(k))) for k in DOMAINS))
    m = MOBANANAS(space, BUDGET, random.Random(seed))
    state, pts = RunState(), []
    while state.evaluations_used < BUDGET:
        props = m.propose(state)
        if not props:
            break
        new = [Observation(genotype=g, objectives=raw(g.values)) for g in props]
        pts.extend(o.objectives for o in new)
        state.evaluations_used += len(new)
        m.update(state, new)
    return hv(pts, REF)


def test_level2_mobananas_vs_bob(tmp_path):
    """The authors' `mobananas.py` needs three run-time shims (bob_reference_runner.py):
    the argument order of `Member(...)` in `BANANAS.__init__`, CPU only (cuda/cpu tensors
    mixed), numpy aliases np.float/np.int/np.bool."""
    from concurrent.futures import ProcessPoolExecutor

    procs, outs = [], []
    for k in range(10):
        out = tmp_path / f"ref_{k}.json"
        outs.append(out)
        procs.append(subprocess.Popen([sys.executable, "-W", "ignore", str(HERE / "bob_reference_runner.py"), REPO,
                                       "mobananas", str(BUDGET), f"{10 * k}:{10 * k + 10}", str(out)]))
    with ProcessPoolExecutor(6) as ex:
        ours = np.array(list(ex.map(_ours_mobananas, range(RUNS))))
    assert all(p.wait() == 0 for p in procs)
    ref = np.array([hv(r["points"], REF) for o in outs for r in json.loads(o.read_text())])
    _check("MO-BANANAS", ours, ref)
