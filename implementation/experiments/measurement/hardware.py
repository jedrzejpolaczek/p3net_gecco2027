"""Hardware and software manifest, for the paper's hardware table and for
reading the timing measurements.

Recorded by scripts/run_pipeline.py at the start of every session
(sessions.jsonl in the run root): timings from sessions on different
machines, power settings, or thermal states are not comparable, so each
session's conditions are kept next to its results.

Every probe is best-effort: a probe that fails records None, never stops a
run.
"""

from __future__ import annotations

import datetime as dt
import importlib.metadata
import os
import platform
import subprocess
import sys
from typing import Any

import psutil

LIBRARIES = (
    "p3net",
    "numpy",
    "scipy",
    "scikit-learn",
    "torch",
    "botorch",
    "gpytorch",
    "optuna",
    "smac",
    "pymoo",
    "hpbandster",
    "google-vizier",
    "jax",
    "nashpobench2api",
    "nats_bench",
)


def _run(args: list[str], timeout: float = 20.0) -> str | None:
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="oem" if sys.platform == "win32" else None,
            errors="replace",
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def cpu_name() -> str | None:
    if sys.platform == "win32":
        out = _run(
            ["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"]
        )
        if out:
            return out.splitlines()[0].strip()
    return platform.processor() or None


def gpus() -> list[dict[str, Any]] | None:
    out = _run(
        [
            "nvidia-smi",
            "--query-gpu=name,driver_version,memory.total,temperature.gpu,power.draw",
            "--format=csv,noheader,nounits",
        ]
    )
    if out is None:
        return None
    result = []
    for line in out.splitlines():
        name, driver, memory, temperature, power = [p.strip() for p in line.split(",")]
        result.append(
            {
                "name": name,
                "driver": driver,
                "memory_mb": _number(memory),
                "temperature_c": _number(temperature),
                "power_draw_w": _number(power),
            }
        )
    return result


def _number(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:
        return None


def power_plan() -> str | None:
    if sys.platform != "win32":
        return None
    return _run(["powercfg", "/getactivescheme"])


def battery() -> dict[str, Any] | None:
    try:
        state = psutil.sensors_battery()
    except (AttributeError, NotImplementedError):
        return None
    if state is None:
        return None
    return {"percent": state.percent, "plugged_in": state.power_plugged}


def torch_info() -> dict[str, Any] | None:
    try:
        import torch
    except ImportError:
        return None
    return {
        "version": torch.__version__,
        "cuda_build": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "cudnn": torch.backends.cudnn.version() if torch.cuda.is_available() else None,
    }


def library_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in LIBRARIES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def manifest() -> dict[str, Any]:
    memory = psutil.virtual_memory()
    return {
        "recorded_at": dt.datetime.now().isoformat(timespec="seconds"),
        "host": platform.node(),
        "os": platform.platform(),
        "python": sys.version.split()[0],
        "cpu": cpu_name(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "ram_gb": round(memory.total / 2**30, 1),
        "ram_available_gb": round(memory.available / 2**30, 1),
        "gpus": gpus(),
        "torch": torch_info(),
        "power_plan": power_plan(),
        "battery": battery(),
        "cpu_percent_at_start": psutil.cpu_percent(interval=1.0),
        "pid": os.getpid(),
        "libraries": library_versions(),
    }
