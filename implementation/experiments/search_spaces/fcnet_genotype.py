"""
FCNet search space (Klein & Hutter, 2019, "Tabular Benchmarks for Joint
Architecture and Hyperparameter Optimization", arXiv:1905.04970).

A two-layer fully connected regression network, trained on four UCI
datasets (substrates/fcnet.py). Nine categorical dimensions, every
combination tabulated -- 6 * 6 * 2 * 2 * 3 * 3 * 6 * 2 * 4 = 62,208
configurations:

  architecture:    n_units_1, n_units_2 in {16, 32, 64, 128, 256, 512}
                   activation_fn_1, activation_fn_2 in {tanh, relu}
                   dropout_1, dropout_2 in {0.0, 0.3, 0.6}
  hyperparameters: init_lr in {5e-4, 1e-3, 5e-3, 1e-2, 5e-2, 1e-1}
                   lr_schedule in {cosine, const}
                   batch_size in {8, 16, 32, 64}

Verified against the downloaded table (data/cache/fcnet/
hyperparameters.parquet: 62,208 rows, exactly these values per column).
Every combination was trained, so there is no validity constraint -- unlike
the cell-based spaces, whose disconnected cells are infeasible.

The architecture part is small (a fixed two-layer topology); the paper
states this as a limitation of the benchmark.
"""

from __future__ import annotations

from dataclasses import dataclass

from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace

UNITS: tuple[int, ...] = (16, 32, 64, 128, 256, 512)
ACTIVATIONS: tuple[str, ...] = ("tanh", "relu")
DROPOUTS: tuple[float, ...] = (0.0, 0.3, 0.6)
INIT_LRS: tuple[float, ...] = (0.0005, 0.001, 0.005, 0.01, 0.05, 0.1)
LR_SCHEDULES: tuple[str, ...] = ("cosine", "const")
BATCH_SIZES: tuple[int, ...] = (8, 16, 32, 64)

#: Genotype coordinate order; also the column names of the benchmark table
#: (with an "hp_" prefix).
DIMENSIONS: tuple[tuple[str, tuple], ...] = (
    ("n_units_1", UNITS),
    ("n_units_2", UNITS),
    ("activation_fn_1", ACTIVATIONS),
    ("activation_fn_2", ACTIVATIONS),
    ("dropout_1", DROPOUTS),
    ("dropout_2", DROPOUTS),
    ("init_lr", INIT_LRS),
    ("lr_schedule", LR_SCHEDULES),
    ("batch_size", BATCH_SIZES),
)
N_ARCHITECTURE_DIMENSIONS = 6


def fcnet_search_space() -> SearchSpace:
    return SearchSpace(domains=tuple(CategoricalDomain(values=values) for _, values in DIMENSIONS))


def fcnet_validity(genotype: Genotype) -> float:
    """Every configuration is tabulated: always feasible."""
    return -1.0


@dataclass(frozen=True)
class FCNetConfiguration:
    values: dict

    @property
    def key(self) -> tuple:
        return tuple(self.values[name] for name, _ in DIMENSIONS)


def decode_fcnet_genotype(genotype: Genotype) -> FCNetConfiguration:
    if len(genotype.values) != len(DIMENSIONS):
        raise ValueError(f"FCNet genotype has {len(DIMENSIONS)} coordinates, got {len(genotype)}")
    for (name, values), value in zip(DIMENSIONS, genotype.values):
        if value not in values:
            raise ValueError(f"{name}={value!r} is not in the FCNet grid {values}")
    return FCNetConfiguration(values={name: v for (name, _), v in zip(DIMENSIONS, genotype.values)})
