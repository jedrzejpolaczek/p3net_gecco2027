"""Level 2 (v005-level2-criteria.md): REINFORCE and RegEvo vs the NAS-Bench-201
reference code (`exps/NAS-Bench-201-algos/reinforce.py`, `R_EA.py`, D-X-Y).

Reference side: the authors' loops copied below (Policy / ExponentialMovingAverage /
select_action / Adam; random_architecture, mutate_arch, regularized_evolution), minus
logging, CUDA and the time budget. Reward on both sides: cifar10-valid validation
accuracy after 12 epochs (hp="12", the reference's `train_and_eval`), deterministic
(mean over trial seeds), from `results/benchmark_tables/nb201_valid12_cifar10valid.json`.
Search space: the 6 NB201 edges x 5 operations as integers (no validity filter, like
the reference).

- REINFORCE: 100 policy steps per run on both sides (our duplicates also update the
  policy, W-R7); our reward is replaced by the raw accuracy, so the test checks the
  policy, baseline and update against the reference (the multi-objective reward and its
  online normalisation are tested at level 1).
- RegEvo: P = 10, S = 10 (reference config); 100 distinct evaluated architectures per run
  (#35: the reference's duplicate evaluations are skipped when counting).

Criterion (fixed before the test): median of the best accuracy per run over 100 runs
within +-2 % of the reference median, and TOST with margin +-2 % at alpha = 0.05.
"""

from __future__ import annotations

import collections
import json
import random
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

torch = pytest.importorskip("torch")

TABLE = (Path(__file__).resolve().parents[4] / "experiments" / "results" / "benchmark_tables"
         / "nb201_valid12_cifar10valid.json")
OPS = ("none", "skip_connect", "nor_conv_1x1", "nor_conv_3x3", "avg_pool_3x3")
STEPS = 100
RUNS = 100

pytestmark = pytest.mark.skipif(not TABLE.exists(), reason="run scripts/build_nb201_valid12_table.py first")


def _acc():
    table = json.loads(TABLE.read_text())["accuracy"]

    def acc(values) -> float:
        o = [OPS[int(v)] for v in values]
        return table[f"|{o[0]}~0|+|{o[1]}~0|{o[2]}~1|+|{o[3]}~0|{o[4]}~1|{o[5]}~2|"]

    return acc


def _space():
    from p3net.problem.genotype import CategoricalDomain, SearchSpace

    return SearchSpace(domains=tuple(CategoricalDomain(values=tuple(range(5))) for _ in range(6)))


# -- reference (D-X-Y, NAS-Bench-201) --------------------------------------------------
class _Policy(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.arch_parameters = torch.nn.Parameter(1e-3 * torch.randn(6, len(OPS)))

    def forward(self):
        return torch.nn.functional.softmax(self.arch_parameters, dim=-1)


class _EMA:
    def __init__(self, momentum):
        self._numerator, self._denominator, self._momentum = 0, 0, momentum

    def update(self, value):
        self._numerator = self._momentum * self._numerator + (1 - self._momentum) * value
        self._denominator = self._momentum * self._denominator + (1 - self._momentum)

    def value(self):
        return self._numerator / self._denominator


def _ref_reinforce(seed: int, acc) -> float:
    torch.manual_seed(seed)
    policy = _Policy()
    optimizer = torch.optim.Adam(policy.parameters(), lr=0.5)
    baseline = _EMA(0.9)
    trace = []
    for _ in range(STEPS):
        m = torch.distributions.Categorical(policy())
        action = m.sample()
        log_prob = m.log_prob(action)
        reward = acc(action.tolist())
        trace.append(reward)
        baseline.update(reward)
        policy_loss = (-log_prob * (reward - baseline.value())).sum()
        optimizer.zero_grad()
        policy_loss.backward()
        optimizer.step()
    return max(trace)


def _ref_rea(seed: int, acc, P: int = 10, S: int = 10) -> float:
    rnd = random.Random(seed)
    nodes = [[0], [1, 2], [3, 4, 5]]  # edges of nodes 1, 2, 3 (CellStructure order)

    def random_arch():
        return [rnd.choice(range(len(OPS))) for _ in range(6)]

    def mutate_arch(parent):  # node, then edge in the node, then a different op
        child = deepcopy(parent)
        node = rnd.randint(0, len(nodes) - 1)
        e = nodes[node][rnd.randint(0, len(nodes[node]) - 1)]
        xop = rnd.choice(range(len(OPS)))
        while xop == child[e]:
            xop = rnd.choice(range(len(OPS)))
        child[e] = xop
        return child

    population, seen = collections.deque(), {}
    while len(population) < P:
        a = random_arch()
        seen.setdefault(tuple(a), acc(a))
        population.append((a, acc(a)))
    while len(seen) < STEPS:
        sample = [rnd.choice(list(population)) for _ in range(S)]
        parent = max(sample, key=lambda m: m[1])
        child = mutate_arch(parent[0])
        seen.setdefault(tuple(child), acc(child))
        population.append((child, acc(child)))
        population.popleft()
    return max(list(seen.values())[:STEPS])


# -- ours -------------------------------------------------------------------------------
def _ours_reinforce(seed: int, acc) -> float:
    from p3net.harness.runner import Observation, RunState
    from p3net.v005.baselines.reinforce import Reinforce

    m = Reinforce(_space(), 10**6, random.Random(seed))
    m._reward = lambda g, f: acc(g.values)  # raw reward, as the reference
    state, best = RunState(), -np.inf
    while m.n_policy_updates < STEPS:
        props = m.propose(state)
        if not props:
            break
        a = acc(props[0].values)
        best = max(best, a)
        state.evaluations_used += 1
        m.update(state, [Observation(genotype=props[0], objectives=(100.0 - a, 0.0))])
    return best


def _ours_regevo(seed: int, acc) -> float:
    from p3net.harness.runner import Observation, RunState
    from p3net.v005.baselines.regevo import RegEvo

    m = RegEvo(_space(), STEPS, random.Random(seed), population_size=10, sample_size=10)
    state, best = RunState(), -np.inf
    while state.evaluations_used < STEPS:
        props = m.propose(state)
        if not props:
            break
        obs = []
        for g in props:
            a = acc(g.values)
            best = max(best, a)
            obs.append(Observation(genotype=g, objectives=(100.0 - a, 0.0)))
        state.evaluations_used += len(props)
        m.update(state, obs)
    return best


def _criterion(name, ours, ref):
    med = float(np.median(ref))
    margin = 0.02 * med
    p_low = stats.ttest_ind(ours + margin, ref, equal_var=False, alternative="greater").pvalue
    p_high = stats.ttest_ind(ours - margin, ref, equal_var=False, alternative="less").pvalue
    print(f"{name}: ours median {np.median(ours):.3f} mean {ours.mean():.3f}; ref median {med:.3f} "
          f"mean {ref.mean():.3f}; MWU p {stats.mannwhitneyu(ours, ref).pvalue:.3f}; TOST p {max(p_low, p_high):.2e}")
    assert abs(float(np.median(ours)) - med) <= margin
    assert max(p_low, p_high) < 0.05


def test_level2_reinforce_vs_nb201_reference():
    acc = _acc()
    ref = np.array([_ref_reinforce(s, acc) for s in range(RUNS)])
    ours = np.array([_ours_reinforce(s, acc) for s in range(RUNS)])
    _criterion("REINFORCE", ours, ref)


def test_level2_regevo_vs_nb201_reference():
    acc = _acc()
    ref = np.array([_ref_rea(s, acc) for s in range(RUNS)])
    ours = np.array([_ours_regevo(s, acc) for s in range(RUNS)])
    _criterion("RegEvo", ours, ref)


def test_regevo_mutation_edge_distribution_as_r_ea():
    """`R_EA.py` mutate_arch: a node uniformly, then one of its incoming edges: edge to node
    1 with 1/3, each edge to node 2 with 1/6, each edge to node 3 with 1/9 (O-RE3 b)."""
    from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace
    from p3net.v005.baselines.regevo import RegEvo

    space = SearchSpace(domains=tuple(CategoricalDomain(values=OPS) for _ in range(6)))
    m = RegEvo(space, 100, random.Random(0), population_size=10, sample_size=10)
    parent = Genotype(values=(3, 3, 3, 3, 3, 3))  # all nor_conv_3x3: every single change stays valid
    counts = np.zeros(6)
    n = 60_000
    for _ in range(n):
        child = m._mutate(parent)
        counts[[i for i in range(6) if child.values[i] != parent.values[i]][0]] += 1
    expected = np.array([1 / 3, 1 / 6, 1 / 6, 1 / 9, 1 / 9, 1 / 9])
    assert stats.chisquare(counts, expected * n).pvalue > 1e-3, counts / n
