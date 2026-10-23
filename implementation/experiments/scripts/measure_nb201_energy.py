"""BM-2 (notes/plans/v005-sources/benchmarks.md): inference energy of NAS-Bench-201
cells on this machine's GPU, Bartnik's protocol (N_warmup = 3; N_samples = 5 since pilot 2, Bartnik used 3;
median of the NVML energy-counter deltas).

One "pass" = inference over 10 000 inputs of shape 3x32x32 (the size of the
CIFAR-10 test set) in fixed-size batches. Weights and inputs are random: the
energy of a forward pass depends on the architecture and tensor shapes, not on
the values (benchmarks.md, Limitations). Network: xautodl `infer.tiny`, C = 16,
N = 5, 10 classes -- the NAS-Bench-201 CIFAR-10 network.

Runs in vendor/energy-env/.venv. Output: one JSON line per architecture (keyed by
the NB201 arch string), appended, so an interrupted run resumes.

    vendor/energy-env/.venv/Scripts/python.exe scripts/measure_nb201_energy.py \
        --out results/energy/nb201_energy.jsonl --sample 100 --seed 0      # pilot
    vendor/energy-env/.venv/Scripts/python.exe scripts/measure_nb201_energy.py \
        --out results/energy/nb201_energy.jsonl --all                       # full table
"""

from __future__ import annotations

import argparse
import ctypes
import itertools
import json
import platform
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

import pynvml
import torch
from xautodl.models import get_cell_based_tiny_net

OPS = ("none", "skip_connect", "nor_conv_1x1", "nor_conv_3x3", "avg_pool_3x3")
N_INPUTS = 10_000
#: Fixed mid-cost cell measured every --ref-every cells. compare_energy_runs.py divides
#: each energy by the reference energy interpolated at its position, which cancels slow
#: drift of the laptop's power state (pilot 2026-10-17: two runs differed by a
#: near-constant 11 %).
REFERENCE = (3, 2, 1, 4, 3, 2)


def arch_str(ops: tuple[int, ...]) -> str:
    o = [OPS[i] for i in ops]
    return f"|{o[0]}~0|+|{o[1]}~0|{o[2]}~1|+|{o[3]}~0|{o[4]}~1|{o[5]}~2|"


def all_archs() -> list[tuple[int, ...]]:
    return list(itertools.product(range(len(OPS)), repeat=6))


def build(ops: tuple[int, ...], device: torch.device) -> torch.nn.Module:
    cfg = {"name": "infer.tiny", "C": 16, "N": 5, "arch_str": arch_str(ops), "num_classes": 10}
    return get_cell_based_tiny_net(_Dict(cfg)).to(device).eval()


class _Dict(dict):
    __getattr__ = dict.get


def one_pass(net: torch.nn.Module, batch: torch.Tensor) -> None:
    n_batches = -(-N_INPUTS // batch.shape[0])
    with torch.inference_mode():
        for _ in range(n_batches):
            net(batch)
    torch.cuda.synchronize()


class _PowerStatus(ctypes.Structure):
    _fields_ = [("ACLineStatus", ctypes.c_ubyte), ("BatteryFlag", ctypes.c_ubyte),
                ("BatteryLifePercent", ctypes.c_ubyte), ("SystemStatusFlag", ctypes.c_ubyte),
                ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]


class _FileTime(ctypes.Structure):
    _fields_ = [("lo", ctypes.c_ulong), ("hi", ctypes.c_ulong)]


def _cpu_times() -> tuple[int, int] | None:
    """(idle, total) 100-ns ticks since boot (Windows GetSystemTimes)."""
    if sys.platform != "win32":
        return None
    idle, kernel, user = _FileTime(), _FileTime(), _FileTime()
    ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user))
    v = lambda ft: (ft.hi << 32) | ft.lo  # noqa: E731
    return v(idle), v(kernel) + v(user)  # kernel time includes idle time


def power_plan() -> dict | None:
    """Active power scheme and the Windows 'power mode' overlay (the Settings slider,
    stored separately from the scheme)."""
    def run(cmd):
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return None

    return {
        "scheme": run(["powercfg", "/getactivescheme"]),
        "overlay_ac": run(["reg", "query", r"HKLM\SYSTEM\CurrentControlSet\Control\Power\User\PowerSchemes",
                           "/v", "ActiveOverlayAcPowerScheme"]),
    }


def session_state(handle, idle_s: float = 1.0) -> dict:
    """Conditions right before an architecture is measured (pilot 3: the second run of
    every pilot was noisier with a ~11 % higher reference energy; this records what can
    differ between sessions). The GPU is left idle for idle_s and its power read at the
    end; CPU utilisation is measured over the same window."""
    def safe(f):
        try:
            return f()
        except Exception as e:  # noqa: BLE001 -- best-effort probe, never stops a measurement
            return f"unavailable: {type(e).__name__}"

    c0 = _cpu_times()
    time.sleep(idle_s)
    c1 = _cpu_times()
    state = {
        "gpu_idle_power_w": safe(lambda: pynvml.nvmlDeviceGetPowerUsage(handle) / 1000),
        "gpu_temp_idle_c": safe(lambda: pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)),
        "gpu_pstate": safe(lambda: pynvml.nvmlDeviceGetPerformanceState(handle)),
        "gpu_clock_event_reasons": safe(lambda: pynvml.nvmlDeviceGetCurrentClocksEventReasons(handle)),
        "gpu_mem_clock_mhz": safe(lambda: pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)),
        "gpu_fan_pct": safe(lambda: pynvml.nvmlDeviceGetFanSpeed(handle)),
    }
    if c0 and c1:
        d_idle, d_total = c1[0] - c0[0], c1[1] - c0[1]
        state["cpu_util"] = round(1 - d_idle / d_total, 4) if d_total else None
    if sys.platform == "win32":
        ps = _PowerStatus()
        if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(ps)):
            state["ac_power"] = {0: False, 1: True}.get(ps.ACLineStatus)
            state["battery_pct"] = ps.BatteryLifePercent if ps.BatteryLifePercent != 255 else None
            state["battery_saver"] = bool(ps.SystemStatusFlag)
    return state


def _attempt(net, batch, handle, n_warmup: int, n_samples: int) -> dict:
    for _ in range(n_warmup):
        one_pass(net, batch)
    energies_j, seconds, temps = [], [], []
    for _ in range(n_samples):
        temps.append(pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU))
        e0, t0 = pynvml.nvmlDeviceGetTotalEnergyConsumption(handle), time.perf_counter()
        one_pass(net, batch)
        e1, t1 = pynvml.nvmlDeviceGetTotalEnergyConsumption(handle), time.perf_counter()
        energies_j.append((e1 - e0) / 1000.0)
        seconds.append(t1 - t0)
    med = statistics.median(energies_j)
    return {
        "energy_j": med,
        "spread": (max(energies_j) - min(energies_j)) / med,
        "energy_samples_j": energies_j,
        "seconds_samples": seconds,
        "temperature_c": temps,
        "graphics_clock_mhz": pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS),
        "clock_event_reasons_after": pynvml.nvmlDeviceGetCurrentClocksEventReasons(handle),
    }


def measure(net, batch, handle, n_warmup: int, n_samples: int, max_spread: float, max_retries: int) -> dict:
    """Median of n_samples passes; an attempt whose samples spread by more than
    max_spread (relative to their median) is repeated, up to max_retries times. The
    attempt with the smallest spread is used; all attempts are kept."""
    attempts = [_attempt(net, batch, handle, n_warmup, n_samples)]
    while attempts[-1]["spread"] > max_spread and len(attempts) <= max_retries:
        attempts.append(_attempt(net, batch, handle, n_warmup, n_samples))
    best = min(attempts, key=lambda a: a["spread"])
    return {**best, "n_attempts": len(attempts), "attempts": attempts if len(attempts) > 1 else None}


def metadata(handle, args) -> dict:
    def safe(f):
        try:
            return f()
        except pynvml.NVMLError as e:
            return f"unavailable: {e}"

    return {
        "gpu_model": pynvml.nvmlDeviceGetName(handle),
        "driver": pynvml.nvmlSystemGetDriverVersion(),
        "cuda": torch.version.cuda,
        "torch": torch.__version__,
        "power_limit_w": safe(lambda: pynvml.nvmlDeviceGetEnforcedPowerLimit(handle) / 1000),
        "clocks_locked": args.clocks_locked,
        "clock_lock_mhz": args.clock_lock_mhz,  # value given to nvidia-smi -lgc (BM-2: 1200)
        "energy_method": "counter",
        "n_warmup": args.n_warmup,
        "n_samples": args.n_samples,
        "max_spread": args.max_spread,
        "max_retries": args.max_retries,
        "aggregate": "median",
        "batch_size": args.batch_size,
        "n_inputs": N_INPUTS,
        "weights": "random (torch default init, seed per arch)",
        "host": platform.node(),
        "power_plan": power_plan(),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true")
    g.add_argument("--sample", type=int, help="number of random architectures (pilot)")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--batch-size", type=int, default=256)
    p.add_argument("--n-warmup", type=int, default=3)
    p.add_argument("--n-samples", type=int, default=5)
    p.add_argument("--max-spread", type=float, default=0.08, help="repeat an attempt whose samples spread more (relative)")
    p.add_argument("--max-retries", type=int, default=2)
    p.add_argument("--clocks-locked", action="store_true", help="set when nvidia-smi -lgc was applied (admin)")
    p.add_argument("--clock-lock-mhz", type=int, default=None, help="the frequency passed to nvidia-smi -lgc")
    p.add_argument("--tag", default="", help="free label, e.g. 'pilot-run1'")
    p.add_argument("--ref-every", type=int, default=5,
                   help="measure the reference cell before the first and after every N cells (drift correction)")
    args = p.parse_args()

    archs = all_archs()
    if args.sample:
        archs = random.Random(args.seed).sample(archs, args.sample)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            if rec.get("tag", "") == args.tag and not rec.get("reference"):
                done.add(rec["arch"])

    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    meta = metadata(handle, args)
    device = torch.device("cuda")
    gen = torch.Generator(device="cpu").manual_seed(args.seed)
    batch = torch.randn(args.batch_size, 3, 32, 32, generator=gen).to(device)

    t_start = time.time()
    meta_written = False
    seq = sum(1 for _ in out.open(encoding="utf-8")) if out.exists() else 0
    todo = [ops for ops in archs if arch_str(ops) not in done]

    def write(f, ops, reference: bool) -> dict:
        nonlocal meta_written, seq
        torch.manual_seed(sum(v * 5**k for k, v in enumerate(ops)))
        net = build(ops, device)
        rec = {"arch": arch_str(ops), "ops": list(ops), "tag": args.tag, "reference": reference, "seq": seq,
               "time": time.time(), "session": session_state(handle), **measure(net, batch, handle, args.n_warmup, args.n_samples, args.max_spread, args.max_retries)}
        if not meta_written:  # once per invocation: conditions can change between sessions
            rec["metadata"] = {**meta, "reference_arch": arch_str(REFERENCE), "ref_every": args.ref_every}
            meta_written = True
        f.write(json.dumps(rec) + "\n")
        f.flush()
        seq += 1
        del net
        return rec

    with out.open("a", encoding="utf-8") as f:
        if todo:
            write(f, REFERENCE, reference=True)
        for i, ops in enumerate(todo):
            rec = write(f, ops, reference=False)
            if (i + 1) % args.ref_every == 0 or i + 1 == len(todo):
                ref = write(f, REFERENCE, reference=True)
                el = time.time() - t_start
                print(f"{i + 1}/{len(todo)}  {el / (i + 1):.1f} s/arch  last {rec['energy_j']:.2f} J  "
                      f"ref {ref['energy_j']:.2f} J  T={rec['temperature_c'][-1]} C  "
                      f"clk {rec['graphics_clock_mhz']} MHz", flush=True)
    pynvml.nvmlShutdown()


if __name__ == "__main__":
    main()
