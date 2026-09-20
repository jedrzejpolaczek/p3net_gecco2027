"""A stand-in for vendor/jahsbench-env/query_server.py, for tests.

Speaks the same protocol in both modes (stdin/stdout, and `--serve PORT_FILE`)
but answers from a formula instead of the 12 GB surrogate models, so the
shared-bridge machinery can be tested without the benchmark data or its
Python 3.10 environment."""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading


def answer(request: dict) -> dict:
    if request.get("command") == "shutdown":
        return {"shutdown": True}
    if request["dataset"] == "unknown_dataset":
        return {"error": "ValueError: unknown dataset"}
    base = float(sum(len(str(e)) for e in request["edges"]))
    return {
        "valid_acc": base + request["epochs"] / 100.0,
        "size_mb": base / 10.0,
        "train_acc": base + 1.0,
        "test_acc": base - 1.0,
        "runtime": base * 10.0,
        "pid": os.getpid(),
    }


def serve(port_file: str) -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(16)
    temporary = port_file + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        handle.write(f"{server.getsockname()[1]}\n{os.getpid()}\n")
    os.replace(temporary, port_file)

    def client(connection: socket.socket) -> None:
        with connection, connection.makefile("rw", encoding="utf-8", newline="\n") as stream:
            for line in stream:
                if not line.strip():
                    continue
                response = answer(json.loads(line))
                stream.write(json.dumps(response) + "\n")
                stream.flush()
                if response.get("shutdown"):
                    os.remove(port_file)
                    os._exit(0)

    while True:
        connection, _ = server.accept()
        threading.Thread(target=client, args=(connection,), daemon=True).start()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir")
    parser.add_argument("--serve", metavar="PORT_FILE", default=None)
    parser.add_argument("--max-datasets", type=int, default=8)
    parser.add_argument("--idle-timeout", type=float, default=3600.0)
    args = parser.parse_args()
    if args.serve:
        serve(args.serve)
        return
    # A line of library noise first: the real bridge's dependencies print to
    # stdout, and the caller must skip it rather than parse it (2026-09-20).
    print("[0. 0.]", flush=True)
    for line in sys.stdin:
        if line.strip():
            print(json.dumps(answer(json.loads(line))), flush=True)


if __name__ == "__main__":
    main()
