"""Reference side of the Bag-of-Baselines loop test (v005-level2-criteria.md): the
authors' `shemoa.py` / `member.py` (automl/multi-obj-baselines) run unchanged on a
synthetic Flowers-shaped problem. Ax is replaced by a stub module providing only what
the loops use (`Experiment.new_trial`, `eval_trial`, `GeneratorRun`, `Arm`, `Data.df`).

The problem (`flowers_like` below): 13 variables (11 x 8 values + `batch_norm` and
`global_avg_pooling` with 2 values, the keys `Member.fitness` expects); objectives of the
additive problem, mapped into the code's Flowers conventions -- `num_params` plays
log10(#params) in (0, 8), `val_acc_1` is minus accuracy in (-100, 0) -- because the
code hard-codes the tournament key (15 - f0) * f1 and the HV reference point [8, 0].

  python bob_reference_runner.py REPO shemoa|mobananas BUDGET RUNS|START:STOP OUT_JSON
"""

from __future__ import annotations

import json
import random
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

# the code uses np.float / np.int / np.bool (aliases of the builtins, removed in numpy >= 1.24)
for _name, _t in (("float", float), ("int", int), ("bool", bool)):
    setattr(np, _name, _t)

KEYS = ([f"x{i}" for i in range(5)] + [f"n_conv_{i}" for i in range(3)] + [f"n_fc_{i}" for i in range(3)]
        + ["batch_norm", "global_avg_pooling"])  # Flowers key names: the code pads missing n_conv/n_fc keys
DOMAINS = [8] * 11 + [2, 2]


def flowers_like():
    rng = random.Random(0)
    w1 = [[rng.random() for _ in range(k)] for k in DOMAINS]
    w2 = [[1.0 - x + 0.3 * rng.random() for x in row] for row in w1]

    def raw(values):
        values = [int(v) for v in values]
        return (sum(w1[i][v] for i, v in enumerate(values)), sum(w2[i][v] for i, v in enumerate(values)))

    def mapped(values):
        a, b = raw(values)  # a in ~[1.5, 11.5], b in ~[2, 16]
        return {"num_params": 0.45 * b, "val_acc_1": -(100.0 - 8.0 * a)}

    return raw, mapped


def _install_ax_stub(mapped, log):
    ax = types.ModuleType("ax")

    class Arm:
        def __init__(self, parameters, name=None):
            self.parameters, self.name = parameters, name

    class GeneratorRun:
        def __init__(self, arms):
            self.arms = arms

    class _Frame:
        """The two operations `Member.fitness` applies to `data.df`
        (`df[df['metric_name'] == name]['mean']`, then float()), as pandas < 2 did:
        float() of a one-element selection."""

        def __init__(self, cols):
            self.cols = {k: np.asarray(v) for k, v in cols.items()}

        def __getitem__(self, key):
            if isinstance(key, str):
                return _Column(self.cols[key])
            mask = key.values if isinstance(key, _Column) else key
            return _Frame({k: v[mask] for k, v in self.cols.items()})

    class _Column:
        def __init__(self, values):
            self.values = values

        def __eq__(self, other):
            return _Column(self.values == other)

        def __float__(self):
            (x,) = self.values  # pandas < 2: float() of a one-element Series
            return float(x)

    class Data:
        def __init__(self, df):
            self.df = _Frame({c: df[c].to_list() for c in df.columns})

    class Experiment:
        def new_trial(self, generator_run):
            return generator_run.arms[0]

        def eval_trial(self, arm):
            values = tuple(int(arm.parameters[k]) for k in KEYS)
            m = mapped(values)
            log.append(values)
            return Data(pd.DataFrame({"metric_name": list(m), "mean": list(m.values())}))

    ax.Arm, ax.GeneratorRun, ax.Data, ax.Experiment = Arm, GeneratorRun, Data, Experiment
    sys.modules["ax"] = ax
    return Experiment


def _install_baselines_package(repo: str) -> None:
    """`baselines/__init__.py` pulls in Ax's SimpleExperiment; the loops only need
    `nDS` and `computeHV2D` from `baselines/core/pareto.py`, so the package is set up
    without running its `__init__`."""
    import importlib.util

    root = Path(repo) / "baselines"
    pkg = types.ModuleType("baselines")
    pkg.__path__ = [str(root)]
    spec = importlib.util.spec_from_file_location("baselines.core.pareto", root / "core" / "pareto.py")
    pareto = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pareto)
    pkg.nDS, pkg.computeHV2D, pkg.nDS_index, pkg.crowdingDist = (pareto.nDS, pareto.computeHV2D, pareto.nDS_index,
                                                                 pareto.crowdingDist)
    sys.modules["baselines"] = pkg


class _Config(dict):
    def get_dictionary(self):
        return dict(self)


class SearchSpace:
    """What `Member` uses of the Flowers `CustomSearchSpace`."""

    def sample_configuration(self):
        return _Config({k: int(np.random.randint(d)) for k, d in zip(KEYS, DOMAINS)})

    def sample_hyperparameter(self, hp):
        return int(np.random.randint(DOMAINS[KEYS.index(hp)]))

    def is_mutable_hyperparameter(self, hp):
        return True

    def get_hyperparameters_dict(self):
        """MO-BANANAS `return_train_data` / `mutate`: categorical hyperparameters (no
        .upper -> the `except` branches: value / max(choices), re-sampled on mutation)."""
        return {k: types.SimpleNamespace(choices=list(range(d))) for k, d in zip(KEYS, DOMAINS)}


def run_mobananas(repo: str, budget: int, seeds):
    log: list = []
    raw, mapped = flowers_like()
    Experiment = _install_ax_stub(mapped, log)
    _install_baselines_package(repo)
    import torch

    torch.cuda.is_available = lambda: False  # neural_predictor.py mixes cuda and cpu tensors when a GPU exists

    if "torchvision" not in sys.modules:  # imported by neural_predictor.py, never used
        tv = types.ModuleType("torchvision")
        tv.transforms = types.ModuleType("torchvision.transforms")
        sys.modules["torchvision"], sys.modules["torchvision.transforms"] = tv, tv.transforms
    from baselines.methods.mobananas import mobananas as mb
    from baselines.methods.mobananas.member import Member, Mutation

    # As published, BANANAS.__init__ calls Member(space, target_function, mutation_type, budget,
    # experiment=...) while Member takes (space, mutation, budget, experiment, x) -> TypeError.
    # Minimal fix of the argument order only (target_function is never used by Member).
    def _member(space, *args, **kw):
        if len(args) == 3 and "experiment" in kw:
            _target, mutation, budget = args
            return Member(space, mutation, budget, kw["experiment"])
        return Member(space, *args, **kw)

    mb.Member = _member
    BANANAS = mb.BANANAS
    from baselines.methods.mobananas.neural_predictor import Neural_Predictor

    out = []
    for seed in seeds:
        torch.manual_seed(seed)
        log.clear()
        # get_MOBANANAS defaults: 80 epochs, 5 nets, initial 20, num_arch 8, select 4; BANANAS.__init__
        # calls np.random.seed(0) itself -- reseeded below so the runs differ
        orig_seed = np.random.seed
        np.random.seed = lambda s, _o=orig_seed, _seed=seed: _o(_seed)
        try:
            b = BANANAS(Neural_Predictor(num_epochs=80, num_ensamble_nets=5), None, Experiment(), SearchSpace(),
                        20, 8, 25, 4, 3 * budget, mutation_type=Mutation.GAUSSIAN)
            import contextlib
            import io

            with contextlib.redirect_stdout(io.StringIO()):
                b.steps()
        finally:
            np.random.seed = orig_seed
        distinct = list(dict.fromkeys(log))[:budget]
        out.append({"seed": seed, "points": [raw(v) for v in distinct], "n_distinct": len(set(log)), "n_evals": len(log)})
    return out


def run_shemoa(repo: str, budget: int, seeds):
    log: list = []
    raw, mapped = flowers_like()
    Experiment = _install_ax_stub(mapped, log)
    _install_baselines_package(repo)
    from baselines.methods.shemoa import SHEMOA, Mutation, ParentSelection, Recombination

    out = []
    for seed in seeds:
        np.random.seed(seed)
        log.clear()
        ea = SHEMOA(SearchSpace(), Experiment(), population_size=20, budget_min=24, budget_max=25,
                    mutation_type=Mutation.UNIFORM, recombination_type=Recombination.UNIFORM,
                    selection_type=ParentSelection.TOURNAMENT, total_number_of_function_evaluations=6 * budget)
        import contextlib
        import io

        with contextlib.redirect_stdout(io.StringIO()):
            try:
                ea.optimize()
            except Warning:
                pass
        distinct = list(dict.fromkeys(log))[:budget]
        out.append({"seed": seed, "points": [raw(v) for v in distinct], "n_distinct": len(set(log)), "n_evals": len(log)})
    return out


if __name__ == "__main__":
    repo, method, budget, runs, out_path = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
    seeds = range(*map(int, runs.split(":"))) if ":" in runs else range(int(runs))
    res = {"shemoa": run_shemoa, "mobananas": run_mobananas}[method](repo, budget, seeds)
    Path(out_path).write_text(json.dumps(res))
