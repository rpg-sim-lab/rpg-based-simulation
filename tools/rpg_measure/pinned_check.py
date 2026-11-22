"""The launchers' second heavy-process check: refuse to start while ANY other process is pinned to the measurement cpus (TCK-20261122-TRACE-KIT-CALENDAR-LOAD-WRITES-BYTECODE-INTO-A-FROZEN-TREE).

Why: the launchers' ``heavy_running`` matches the argv SHAPE of RPG-measure scripts only, so it cannot see another team's kit (perf's ``obs_cost_arm.py`` pinned to cpus 4-5 was not caught). What makes a second process unsafe is
the cpus it is pinned to, not its name: a measurement on cpus 4-5 is void if anything else runs there.

PINNED means the process's ``Cpus_allowed_list`` (``/proc/<pid>/status``) shares a cpu with the measurement set AND is not the whole machine (an unpinned process may run anywhere and is not a claim on those cpus). Skipped, so the check
never matches itself or its own launcher: this process, its whole ancestor chain (the launcher shell, the ``kitpy`` subshell), kernel threads (pid 2 and its children) and processes with an empty command line.

Usage: python pinned_check.py [--cpus 4-5]    exit 0 = nothing else is pinned there; exit 1 = prints one line per process (pid, allowed list, args).
Stdlib only; reads /proc only; writes nothing.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set


def parse_cpu_list(text: str) -> Set[int]:
    """'4-5' -> {4, 5}; '0-3,6' -> {0, 1, 2, 3, 6}; '' -> set()."""
    cpus: Set[int] = set()
    for part in text.strip().split(","):
        if not part:
            continue
        low, _, high = part.partition("-")
        cpus.update(range(int(low), int(high or low) + 1))
    return cpus


def online_cpus(proc_root: Path = Path("/proc")) -> Set[int]:
    sysfs = Path("/sys/devices/system/cpu/online")
    if proc_root == Path("/proc") and sysfs.exists():
        return parse_cpu_list(sysfs.read_text(encoding="utf-8"))
    return set(range(os.cpu_count() or 1))


def read_status(pid_dir: Path) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    for line in (pid_dir / "status").read_text(encoding="utf-8", errors="replace").splitlines():
        key, _, value = line.partition(":")
        fields[key] = value.strip()
    return fields


def ancestor_chain(pid: int, proc_root: Path = Path("/proc")) -> Set[int]:
    """``pid`` and every parent up to pid 1 (a loop-proof walk)."""
    chain: Set[int] = set()
    current: Optional[int] = pid
    while current and current > 1 and current not in chain:
        chain.add(current)
        try:
            current = int(read_status(proc_root / str(current)).get("PPid", "0"))
        except (OSError, ValueError):
            break
    return chain


def pinned_processes(cpus: Set[int], proc_root: Path = Path("/proc"), skip: Iterable[int] = (), everything: Optional[Set[int]] = None) -> List[Dict[str, object]]:
    """Every process other than the skipped ones and this one's ancestors that is pinned to a cpu in ``cpus``: [{pid, allowed, args}]."""
    machine = everything if everything is not None else online_cpus(proc_root)
    own = ancestor_chain(os.getpid(), proc_root) | set(skip)
    found: List[Dict[str, object]] = []
    for entry in sorted((p for p in proc_root.iterdir() if p.name.isdigit()), key=lambda p: int(p.name)):
        pid = int(entry.name)
        if pid in own or pid == 2:
            continue
        try:
            status = read_status(entry)
            args = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8", "replace").strip()
        except OSError:
            continue                      # the process ended while we looked
        if not args or status.get("PPid") == "2":
            continue                      # a kernel thread: it has no command line and hangs under kthreadd
        allowed = parse_cpu_list(status.get("Cpus_allowed_list", ""))
        if allowed and allowed != machine and allowed & cpus:
            found.append({"pid": pid, "allowed": status.get("Cpus_allowed_list", ""), "args": args[:200]})
    return found


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cpus", default="4-5")
    args = ap.parse_args(argv)
    found = pinned_processes(parse_cpu_list(args.cpus))
    for item in found:
        print(f"PINNED pid={item['pid']} cpus={item['allowed']} {item['args']}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
