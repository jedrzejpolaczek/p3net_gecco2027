"""Exclusive file locks shared between processes on one machine.

A lock is a file created with os.O_EXCL (atomic on the same filesystem)
holding the owner's PID and host name. A lock whose owner no longer exists
on this host is stale and is broken by the next process that wants it, so a
crashed or killed process never blocks the others. Used by
scripts/run_pipeline.py (per-run and resource-slot locks) and by
substrates/jahs_bench_201.py (one benchmark load at a time).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import platform
import time
from pathlib import Path

import psutil


def try_lock(path: Path) -> bool:
    """Create `path` exclusively; True if this process now holds it. A lock
    held by a process that no longer exists on this host is broken first."""
    path.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if lock_is_stale(path):
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
                continue
            return False
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "pid": os.getpid(),
                    "host": platform.node(),
                    "at": dt.datetime.now().isoformat(timespec="seconds"),
                },
                handle,
            )
        return True
    return False


def lock_is_stale(path: Path, grace_seconds: float = 60.0) -> bool:
    try:
        holder = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False
    except (OSError, ValueError):
        # Created but not yet written, or cut short by a crash.
        try:
            return time.time() - path.stat().st_mtime > grace_seconds
        except FileNotFoundError:
            return False
    if holder.get("host") != platform.node():
        return False  # another machine's process; never broken from here
    return not psutil.pid_exists(int(holder.get("pid", -1)))


def release_lock(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


class FileLock:
    """Blocking mutual exclusion for short critical sections."""

    def __init__(self, path: Path, poll_seconds: float = 0.05) -> None:
        self.path = path
        self.poll_seconds = poll_seconds

    def __enter__(self) -> FileLock:
        while not try_lock(self.path):
            time.sleep(self.poll_seconds)
        return self

    def __exit__(self, *exc) -> None:
        release_lock(self.path)
