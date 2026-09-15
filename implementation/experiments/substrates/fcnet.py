"""FCNet adapter (Klein & Hutter, 2019): the second benchmark family, a fixed
lookup table like NAS-HPO-Bench-II (Category 1, exact oracle front).

Data
----
The original archive (ml4aad.org/wp-content/uploads/2019/01/
fcnet_tabular_benchmarks.tar.gz) is no longer online (HTTP 404, checked
2026-09-15). The data come from Syne Tune's public blackbox repository,
which holds the same table converted from the original HDF5 files by a
published script (syne-tune: syne_tune/blackbox_repository/
conversion_scripts/scripts/fcnet_import.py):
  https://huggingface.co/datasets/synetune/blackbox-repository, fcnet/
  objectives_evaluations.npy
    sha256 62091c9c878975846cfc7bac02ea28d8b59eada94806097a1e1836f0d1119e58
  hyperparameters.parquet
    sha256 9be9c2cb6353c058c12b6f997edc17670bac4f8ae0cc0eb0177805bf6351d027
Tensor shape (task, configuration, seed, epoch, metric) = (4, 62208, 4,
100, 5), float32; metrics valid_loss (= valid MSE), train_loss,
final_test_error (test MSE after training), n_params, elapsed_time.

Checked on the downloaded files, not assumed: both hashes; the shape; no
NaN; n_params of every row equals (d+1)*u1 + (u1+1)*u2 + (u2+1) with one
input dimension d per task (protein 9, naval 15, parkinsons 20, slice
380) -- so hyperparameter rows and result rows are aligned in every task.

Objectives (minimised)
----------------------
  f1 = validation MSE after `epochs` epochs, mean over the 4 training seeds;
  f2 = training time in seconds, mean over the 4 seeds -- the same kind of
       cost as NAS-HPO-Bench-II's f2.
Averaging over the seeds makes the benchmark deterministic, like
NAS-Bench-201's is_random=False (Substrate.deterministic).

Fidelity: 1-100 epochs, from the per-epoch validation curves. The table
records only the total training time, so the time up to epoch e is
runtime * e / 100 -- the linear interpolation of the FCNet benchmark code
and of Syne Tune's conversion.

The four per-task arrays actually used (about 60 MB each) are extracted
once from the 2 GB tensor into data/cache/fcnet/derived/<task>.npz.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from p3net.problem.genotype import Genotype

from search_spaces.fcnet_genotype import DIMENSIONS, decode_fcnet_genotype
from substrates.base import FidelityLevel, Substrate

FCNET_TASKS: tuple[str, ...] = (
    "protein_structure",
    "naval_propulsion",
    "parkinsons_telemonitoring",
    "slice_localization",
)
MAX_EPOCHS = 100
_METRICS = ("valid_loss", "train_loss", "final_test_error", "n_params", "elapsed_time")
DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "cache" / "fcnet"


def extract_task(data_dir: Path, task: str) -> Path:
    """Write derived/<task>.npz (seed means) atomically; returns its path."""
    out = data_dir / "derived" / f"{task}.npz"
    if out.exists():
        return out
    import pandas as pd

    tensor = np.load(data_dir / "objectives_evaluations.npy", mmap_mode="r")
    t = FCNET_TASKS.index(task)
    hyperparameters = pd.read_parquet(data_dir / "hyperparameters.parquet")
    columns = [f"hp_{name}" for name, _ in DIMENSIONS]
    keys = np.array(hyperparameters[columns].astype(str).agg("|".join, axis=1).tolist(), dtype=str)

    def seed_mean(metric: str, epochs=slice(None)) -> np.ndarray:
        # One metric at a time from the memory map (float32 -> float64 per slice).
        block = np.asarray(tensor[t, :, :, epochs, _METRICS.index(metric)], dtype=np.float64)
        return block.mean(axis=1)

    arrays = {
        "keys": keys,
        "valid_mse": seed_mean("valid_loss"),
        "train_mse": seed_mean("train_loss", -1),
        "test_mse": seed_mean("final_test_error", -1),
        "runtime": seed_mean("elapsed_time", -1),
        "n_params": np.asarray(tensor[t, :, 0, 0, _METRICS.index("n_params")], dtype=np.float64),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.stem + ".tmp.npz")
    np.savez(tmp, **arrays)
    os.replace(tmp, out)
    return out


def _key(genotype: Genotype) -> str:
    config = decode_fcnet_genotype(genotype)
    return "|".join(str(config.values[name]) for name, _ in DIMENSIONS)


@dataclass
class FCNetSubstrate(Substrate):
    task: str = "protein_structure"
    data_dir: str | Path = DEFAULT_DATA_DIR
    _arrays: dict[str, np.ndarray] | None = field(default=None, init=False, repr=False)
    _row: dict[str, int] | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.task not in FCNET_TASKS:
            raise ValueError(f"unknown FCNet task {self.task!r}, expected one of {FCNET_TASKS}")

    def _load(self) -> None:
        if self._arrays is None:
            with np.load(extract_task(Path(self.data_dir), self.task)) as data:
                self._arrays = {name: data[name] for name in data.files}
            self._row = {str(k): i for i, k in enumerate(self._arrays["keys"])}

    def _index(self, genotype: Genotype) -> int:
        self._load()
        return self._row[_key(genotype)]

    def fidelity_ladder(self) -> tuple[FidelityLevel, ...]:
        return (FidelityLevel(rank=0, config={"epochs": MAX_EPOCHS}),)

    def query_f1(self, genotype: Genotype, fidelity: FidelityLevel) -> float:
        epochs = int(fidelity.config.get("epochs", MAX_EPOCHS))
        if not 1 <= epochs <= MAX_EPOCHS:
            raise ValueError(f"FCNet records 1-{MAX_EPOCHS} epochs, requested {epochs}")
        return float(self._arrays_row("valid_mse", genotype)[epochs - 1])

    def analytic_f2(self, genotype: Genotype) -> float:
        # Like the other tabular benchmarks, read from the table, not analytic.
        return float(self._arrays_row("runtime", genotype))

    def training_seconds(self, genotype: Genotype, epochs: int) -> float:
        return self.analytic_f2(genotype) * epochs / MAX_EPOCHS

    def full_fidelity_metrics(self, genotype: Genotype) -> dict[str, float]:
        return {
            "train_mse": float(self._arrays_row("train_mse", genotype)),
            "valid_mse": self.query_f1(genotype, self.fidelity_ladder()[-1]),
            "test_mse": float(self._arrays_row("test_mse", genotype)),
            "training_seconds": self.analytic_f2(genotype),
            "n_params": float(self._arrays_row("n_params", genotype)),
        }

    def _arrays_row(self, name: str, genotype: Genotype):
        index = self._index(genotype)
        return self._arrays[name][index]

    def all_objectives(self) -> tuple[list[Genotype], np.ndarray]:
        """Every configuration with its (f1, f2) at full fidelity -- for the
        exact oracle front (scripts/build_oracle_front.py)."""
        self._load()
        genotypes = []
        for key in self._arrays["keys"]:
            parts = str(key).split("|")
            values = []
            for (name, domain), text in zip(DIMENSIONS, parts):
                values.append(next(v for v in domain if str(v) == text))
            genotypes.append(Genotype(values=tuple(values)))
        objectives = np.stack(
            [self._arrays["valid_mse"][:, MAX_EPOCHS - 1], self._arrays["runtime"]], axis=1
        )
        return genotypes, objectives
