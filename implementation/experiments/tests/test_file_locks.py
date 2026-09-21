"""Tests for file_locks: the cross-process locks the pipeline and the shared
JAHS bridge rely on.

The regression these pin (2026-09-21): on Windows `unlink` refuses to delete
a file another thread has open, so releasing a lock raised PermissionError,
killed the releasing thread and left the lock file behind -- after which
every other process waited on a lock nobody held, for ever."""

from __future__ import annotations

import json
import os
import threading
import time

import psutil
import pytest

from file_locks import FileLock, lock_is_stale, release_lock, try_lock


def _dead_pid() -> int:
    pid = 999_999
    while psutil.pid_exists(pid):
        pid += 1
    return pid


def test_lock_is_exclusive(tmp_path):
    lock = tmp_path / "a.lock"
    assert try_lock(lock)
    assert not try_lock(lock)
    release_lock(lock)
    assert try_lock(lock)


def test_release_survives_a_concurrent_reader(tmp_path):
    """The Windows failure mode: a reader holds the file open while the owner
    releases it. The lock must still disappear, and no exception may escape."""
    lock = tmp_path / "b.lock"
    assert try_lock(lock)
    stop = threading.Event()

    def reader() -> None:
        while not stop.is_set():
            lock_is_stale(lock)  # opens the file for reading, repeatedly

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    try:
        release_lock(lock)
    finally:
        stop.set()
        thread.join(timeout=5)
    assert not lock.exists()


def test_many_threads_take_and_release_the_same_lock(tmp_path):
    """Four threads, as in the shared-bridge start path. Every critical
    section must be entered alone, and none may deadlock."""
    lock = tmp_path / "c.lock"
    inside = 0
    overlaps = 0
    rounds = 40
    guard = threading.Lock()

    def worker() -> None:
        nonlocal inside, overlaps
        for _ in range(rounds):
            with FileLock(lock, poll_seconds=0.001, timeout_seconds=60):
                with guard:
                    inside += 1
                    if inside > 1:
                        overlaps += 1
                time.sleep(0.001)
                with guard:
                    inside -= 1

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=120)
    assert not any(thread.is_alive() for thread in threads), "deadlock"
    assert overlaps == 0
    assert not lock.exists()


def test_waiting_for_an_orphaned_lock_times_out_and_names_the_holder(tmp_path):
    lock = tmp_path / "d.lock"
    # A live process on this host: never broken as stale, so the wait ends
    # only through the timeout.
    lock.write_text(json.dumps({"pid": os.getpid(), "host": __import__("platform").node()}))
    with pytest.raises(TimeoutError, match=str(os.getpid())):
        with FileLock(lock, poll_seconds=0.01, timeout_seconds=0.2):
            pass


def test_a_lock_of_a_dead_process_is_broken(tmp_path):
    lock = tmp_path / "e.lock"
    lock.write_text(json.dumps({"pid": _dead_pid(), "host": __import__("platform").node()}))
    assert lock_is_stale(lock)
    with FileLock(lock, timeout_seconds=5):
        pass
    assert not lock.exists()
