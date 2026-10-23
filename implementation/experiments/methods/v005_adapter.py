"""Adapter between the production harness (scripts/run_experiment.py) and the v005
methods of `p3net.v005` (decision 2026-10-22: one runner for v004 and v005, the v004
methods and configs untouched).

Two translations:
- genotypes: the harness holds domain *values* (operation names, hyperparameter
  values); the v005 methods hold value *indices* (`p3net.v005.common`). The adapter maps
  proposals index -> value and observations value -> index.
- multi-fidelity protocol: `MultiFidelityRunner` asks one query at a time
  (`propose_query` / `observe`); the v005 MF methods propose batches of
  (genotype, epochs) and take their objectives in one `update`.

Method kinds are `v005_<name>` (configs/methods/v005/*.yaml); `V005_METHODS` maps each
to its class and whether it is multi-fidelity.
"""

from __future__ import annotations

import importlib
import inspect
import json
import random
from collections import Counter
from typing import Any

from p3net.harness.runner import Observation, RunState
from p3net.problem.genotype import Genotype, SearchSpace

# kind -> (module, class, multi-fidelity)
V005_METHODS: dict[str, tuple[str, str, bool]] = {
    "v005_p3net": ("p3net.v005.methods", "P3Net", False),
    "v005_p3net_gate": ("p3net.v005.methods", "P3NetGate", False),
    "v005_p3net_nolink": ("p3net.v005.methods", "P3NetNoLink", False),
    "v005_p3_canonical": ("p3net.v005.methods", "P3Canonical", False),
    "v005_p3_elympus": ("p3net.v005.elympus", "P3ELyMPuS", False),
    "v005_mo_dsa": ("p3net.v005.bartnik", "MODSA", False),
    "v005_mo_psa": ("p3net.v005.bartnik", "MOPSA", False),
    "v005_nsga_net": ("p3net.v005.baselines.nsga_net", "NSGANet", False),
    "v005_nsganetv2": ("p3net.v005.baselines.nsganetv2", "NSGANetV2", False),
    "v005_reinforce": ("p3net.v005.baselines.reinforce", "Reinforce", False),
    "v005_regevo": ("p3net.v005.baselines.regevo", "RegEvo", False),
    "v005_mo_ls": ("p3net.v005.baselines.mo_ls", "MOLS", False),
    "v005_shemoa": ("p3net.v005.baselines.bob", "SHEMOA", False),
    "v005_mobananas": ("p3net.v005.baselines.bob", "MOBANANAS", False),
    "v005_motpe": ("p3net.v005.baselines.library", "MOTPE", False),
    "v005_nsga3": ("p3net.v005.baselines.library", "NSGA3", False),
    "v005_smac3_parego": ("p3net.v005.baselines.library", "SMAC3ParEGO", False),
    "v005_vizier": ("p3net.v005.baselines.library", "Vizier", False),
    "v005_qnehvi": ("p3net.v005.baselines.library", "QNEHVI", False),
    "v005_qparego": ("p3net.v005.baselines.library", "QParEGO", False),
    "v005_moead": ("p3net.v005.baselines.library", "MOEAD", False),
    "v005_random_search": ("p3net.v005.baselines.library", "RandomSearch", False),
    "v005_hyperband": ("p3net.v005.mf", "HyperbandMO", True),
    "v005_asha": ("p3net.v005.mf", "ASHAMO", True),
    "v005_shemoa_mf": ("p3net.v005.mf", "SHEMOAMF", True),
    "v005_mosh_bananas": ("p3net.v005.mf", "MOSHBANANAS", True),
    "v005_mo_bohb": ("p3net.v005.mf", "MOBOHB", True),
}


class _Codec:
    def __init__(self, space: SearchSpace):
        self.values = [tuple(d.values) for d in space.domains]
        self.index = [{v: i for i, v in enumerate(vals)} for vals in self.values]

    def to_values(self, g: Genotype) -> Genotype:
        return Genotype(values=tuple(self.values[i][k] for i, k in enumerate(g.values)))

    def to_indices(self, g: Genotype) -> Genotype:
        return Genotype(values=tuple(self.index[i][v] for i, v in enumerate(g.values)))


def _jsonable(x):
    """config()/diagnostics() may hold library objects (a ConfigSpace, a gamma function):
    keep JSON values, stringify the rest."""
    try:
        json.dumps(x)
        return x
    except TypeError:
        if isinstance(x, dict):
            return {str(k): _jsonable(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [_jsonable(v) for v in x]
        return repr(x)


class _EventCounter:
    """Observer counting the events of methods that accept one (level 4)."""

    def __init__(self):
        self.counts: Counter = Counter()

    def __call__(self, kind: str, payload: dict | None = None) -> None:
        self.counts[kind] += 1
        if kind == "cluster_step" and payload and payload.get("changed"):
            self.counts["cluster_step_changed"] += 1


def _info(method, events: _EventCounter | None = None) -> dict[str, Any]:
    info: dict[str, Any] = {"class": type(method).__name__}
    for name in ("config", "diagnostics"):
        fn = getattr(method, name, None)
        if callable(fn):
            try:
                info[name] = fn()
            except Exception as exc:  # noqa: BLE001 -- diagnostics must not break a run
                info[name] = f"unavailable: {exc!r}"
    info["stop_reason"] = getattr(method, "stop_reason", None)
    if events is not None:
        info["events"] = dict(events.counts)
    return _jsonable(info)


class V005Method:
    """`p3net.harness.runner.Method` around a v005 single-fidelity method."""

    multi_fidelity = False

    def __init__(self, method, space: SearchSpace, events: _EventCounter | None = None):
        self.method, self.codec, self.events = method, _Codec(space), events
        self._state = RunState()

    def propose(self, state: RunState) -> list[Genotype]:
        self._state.evaluations_used = state.evaluations_used
        return [self.codec.to_values(g) for g in self.method.propose(self._state)]

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        obs = [Observation(genotype=self.codec.to_indices(o.genotype), objectives=o.objectives)
               for o in new_observations]
        self._state.history.extend(obs)
        self._state.evaluations_used = state.evaluations_used
        self.method.update(self._state, obs)

    @property
    def v005_info(self) -> dict[str, Any]:
        return _info(self.method, self.events)


class V005MultiFidelityMethod:
    """`methods.multi_fidelity.MultiFidelityMethod` around a v005 MF method."""

    multi_fidelity = True

    def __init__(self, method, space: SearchSpace, events: _EventCounter | None = None):
        self.method, self.codec, self.events = method, _Codec(space), events
        self._state = RunState()
        self._batch: list[tuple[Genotype, int]] = []
        self._next = 0
        self._answers: list[Observation] = []

    def propose_query(self):
        if self._next >= len(self._batch):
            if self._batch:  # the whole batch has been answered: hand it back in one update
                self.method.update(self._state, self._answers)
            self._batch, self._next, self._answers = list(self.method.propose(self._state)), 0, []
            if not self._batch:
                return None
        g, e = self._batch[self._next]
        return self.codec.to_values(g), int(e)

    def observe(self, genotype: Genotype, epochs: int, objectives) -> None:
        g, e = self._batch[self._next]
        assert self.codec.to_indices(genotype) == g and int(epochs) == int(e)
        self._answers.append(Observation(genotype=g, objectives=tuple(objectives)))
        self._next += 1

    @property
    def v005_info(self) -> dict[str, Any]:
        return _info(self.method, self.events)


def build_v005_method(kind: str, params: dict[str, Any], *, search_space: SearchSpace, budget: int, seed: int,
                      substrate=None):
    try:
        module, cls_name, mf = V005_METHODS[kind]
    except KeyError:
        raise ValueError(f"unknown v005 method {kind!r}") from None
    cls = getattr(importlib.import_module(module), cls_name)
    params = dict(params)
    if mf:
        if substrate is None:
            raise ValueError(f"{kind} needs the substrate (max_epochs)")
        params.setdefault("max_epochs", substrate.max_epochs())
    events = None
    if "observer" in inspect.signature(cls).parameters:
        events = params.setdefault("observer", _EventCounter())
    method = cls(search_space, budget, random.Random(seed), **params)
    wrapper = (V005MultiFidelityMethod if mf else V005Method)(method, search_space, events)
    wrapper.kind = kind
    return wrapper
