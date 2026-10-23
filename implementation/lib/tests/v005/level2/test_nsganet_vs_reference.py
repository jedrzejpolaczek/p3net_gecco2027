"""Level 2 (v005-level2-criteria.md): our NSGA-Net vs the authors' `search/nsganet.py`
(ianwhale/nsga-net @ 0ee6225, pymoo 0.3.0) on the shared problems (`_problems.py`),
pop_size = n_offspring = 20, 400 distinct evaluations. Criterion (fixed before the
test): median HV over 100 seeds within +-2 % of the reference median, and TOST with
margin +-2 % at alpha = 0.05.

The reference runs in vendor/nsganet-env (Python 3.8, numpy 1.23.5, pymoo 0.3.0); the
authors' repository has no licence, so it is not vendored -- point P3NET_NSGANET_REPO to
a clone at commit 0ee6225.
"""

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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _problems import PROBLEMS, hv, objective  # noqa: E402

HERE = Path(__file__).resolve().parent
ENV_PY = HERE.parents[3] / "experiments" / "vendor" / "nsganet-env" / ".venv" / "Scripts" / "python.exe"
REPO = os.environ.get("P3NET_NSGANET_REPO")
BUDGET = 400
SEEDS = 100  # protocol decision 2 (2026-10-19)

pytestmark = pytest.mark.skipif(not (REPO and ENV_PY.exists()), reason="needs vendor/nsganet-env and P3NET_NSGANET_REPO")


def _ours(name: str, seed: int) -> float:
    from p3net.harness.runner import Observation, RunState
    from p3net.problem.genotype import CategoricalDomain, SearchSpace
    from p3net.v005.baselines.nsga_net import NSGANet

    domains, f = PROBLEMS[name]["domains"], objective(name)
    space = SearchSpace(domains=tuple(CategoricalDomain(values=tuple(range(k))) for k in domains))
    m = NSGANet(space, BUDGET, random.Random(seed), pop_size=20, n_offspring=20)
    state, pts = RunState(), []
    while state.evaluations_used < BUDGET:
        props = m.propose(state)
        if not props:
            break
        new = [Observation(genotype=g, objectives=f(g.values)) for g in props]
        pts.extend(o.objectives for o in new)
        state.evaluations_used += len(new)
        m.update(state, new)
    return hv(pts, PROBLEMS[name]["ref"])


def _reference(name: str, tmp_path: Path) -> np.ndarray:
    out = tmp_path / f"ref_{name}.json"
    subprocess.run([str(ENV_PY), "-I", str(HERE / "nsganet_reference_runner.py"), REPO, name, str(BUDGET),
                    str(SEEDS), str(out)], check=True, capture_output=True)
    return np.array([r["hv"] for r in json.loads(out.read_text())])


@pytest.mark.parametrize("name", list(PROBLEMS))
def test_level2_nsganet_hv_equivalent_to_reference(name, tmp_path):
    ref = _reference(name, tmp_path)
    ours = np.array([_ours(name, s) for s in range(SEEDS)])
    med_ref = float(np.median(ref))
    margin = 0.02 * med_ref
    print(f"{name}: ours median {np.median(ours):.3f} mean {ours.mean():.3f}; "
          f"ref median {med_ref:.3f} mean {ref.mean():.3f}")
    assert abs(float(np.median(ours)) - med_ref) <= margin, (np.median(ours), med_ref)
    p_low = stats.ttest_ind(ours + margin, ref, equal_var=False, alternative="greater").pvalue
    p_high = stats.ttest_ind(ours - margin, ref, equal_var=False, alternative="less").pvalue
    assert max(p_low, p_high) < 0.05, (p_low, p_high, ours.mean(), ref.mean())
