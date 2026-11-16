"""The host's bounds for the Test phase, read from `registries/session_test_caps.yaml`.

One job: say whether this host has a cap entry and what it is. A host with no entry returns None and everything
downstream runs unwrapped, exactly as before. Env overrides (`RPG_TEST_CAP_*`) replace single numbers for one run.
TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS.
"""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from pathlib import Path

import yaml

CAPS_REL = Path("registries") / "session_test_caps.yaml"
PROJECT_REL = Path("registries") / "session_project.yaml"
_ENV = {
    "memory_max": "RPG_TEST_CAP_MEMORY_MAX",
    "memory_swap_max": "RPG_TEST_CAP_MEMORY_SWAP_MAX",
    "cpus": "RPG_TEST_CAP_CPUS",
    "mem_available_floor_gb": "RPG_TEST_CAP_MEM_AVAILABLE_FLOOR_GB",
    "max_tests_per_chunk": "RPG_TEST_CAP_MAX_TESTS_PER_CHUNK",
}
_REQUIRED = tuple(_ENV)


@dataclass(frozen=True)
class HostCap:
    host: str
    memory_max: str
    memory_swap_max: str
    cpus: str
    mem_available_floor_gb: float
    max_tests_per_chunk: int


def _load_yaml(path: Path) -> dict:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def host_tag(root: Path, hostname: str | None = None) -> str:
    """`host_names[hostname]` from registries/session_project.yaml, else the hostname itself."""
    name = hostname or socket.gethostname()
    names = _load_yaml(root / PROJECT_REL).get("host_names")
    return str(names.get(name, name)) if isinstance(names, dict) else name


def load_cap(root: Path, host: str | None = None, env: dict | None = None) -> HostCap | None:
    """This host's cap, or None when the host has no entry (or the entry is incomplete or malformed)."""
    env = os.environ if env is None else env
    tag = host or host_tag(root)
    hosts = _load_yaml(root / CAPS_REL).get("hosts")
    entry = hosts.get(tag) if isinstance(hosts, dict) else None
    if not isinstance(entry, dict):
        return None
    merged = {key: env.get(var, entry.get(key)) for key, var in _ENV.items()}
    if any(merged[key] is None for key in _REQUIRED):
        return None
    try:
        return HostCap(
            host=tag,
            memory_max=str(merged["memory_max"]),
            memory_swap_max=str(merged["memory_swap_max"]),
            cpus=str(merged["cpus"]),
            mem_available_floor_gb=float(merged["mem_available_floor_gb"]),
            max_tests_per_chunk=int(merged["max_tests_per_chunk"]),
        )
    except (TypeError, ValueError):
        return None


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    cap = load_cap(root)
    print(f"host={host_tag(root)} cap={'none (unwrapped)' if cap is None else cap}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
