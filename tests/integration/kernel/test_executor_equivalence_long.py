"""The sequential and the concurrent executor must give the same world on the same seed, over a horizon long enough to reach the seeds that split late.

Law: docs/engine/matrices/full_certification_test_matrix.md (``test_local_vs_concurrent_identical``) and docs/engine/contracts/bounded_concurrency_contract.md.
TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS: on crowded s45 the executors agreed to t2050 and differed by t2100 on main, and on the
#828 arm they differed from t601 (a seeded wander target read the per-packet seed; the packet had no feature flags, so combat learning was skipped).

What is compared, every 100 ticks, for each (world, seed): the canonical state hash, the full content of every entity field and every top-level state field (hashed or
not, so the cognition contents are included), with ``timeline`` and ``_canonical_cache`` left out (``timeline`` carries a wall-clock timestamp and a uuid per event, so it
differs between two runs of the SAME executor). The first mismatch fails the test and names the tick and the field. The count of worker FAILURE no-ops must be zero on
both arms (a worker failure is a split: bounded_concurrency_contract section 4).

Strength is limited by the digest: the canonical hash omits fields decisions read (TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ), which is why the
field-by-field content comparison is made here as well; a field outside both is not covered.

Each test stands alone and runs both arms live (no recorded hash). Governor pinned, audit mode, worker count pinned by the profile (PROD_SMALL: 2 workers).
Horizon: 2200 ticks on crowded s45 (the base that split at t2051-2100), 2000 ticks on the others (crowded s42 splits at t1974 without the packet's blocked_tiles).
"""
import dataclasses
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

import src.engine.worker_manager as worker_manager
from src.config.profiles import PROD_SMALL
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository
from tests.helpers.kernel_pinning import PinnedNormalGovernor

SAMPLE_EVERY = 100
WORLDS_DIR = str(Path(__file__).resolve().parents[3] / "data" / "worlds")  # anchored to the repo root, not the working directory
_SKIP_ENTITY_FIELDS = frozenset({"timeline"})
# Derived caches and indexes on the state, rebuilt per state object (a dropped one only costs a new search): not world content. ``route_plans`` and ``movement_cache`` are
# such caches (a cache hit equals recomputation); the claim that they are not world content is owned by TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ.
_DERIVED_STATE_FIELDS = frozenset({"entities", "route_plans", "movement_cache", "occupancy_snapshot", "occupancy_map", "spatial_grid", "building_map",
                                   "world_indexes", "semantic_entity_indexes"})


def _skipped(name: str, skip: frozenset) -> bool:
    return name in skip or name.startswith("_")  # leading underscore: a cache attribute (_canonical_cache, _spatial_grid_cache, ...)


def _canonical(value):
    """JSON-ready form of a field value. A dict with a key JSON cannot carry (the state's ``terrain`` is keyed by (x, y) tuples) becomes a sorted list of
    [key, value] pairs, recursively; tuples and sets become lists (sets sorted)."""
    if isinstance(value, dict):
        if all(isinstance(k, (str, int, float, bool)) or k is None for k in value):
            return {k: _canonical(v) for k, v in value.items()}
        return sorted(([_canonical(k), _canonical(v)] for k, v in value.items()), key=lambda pair: json.dumps(pair[0], sort_keys=True, default=str))
    if isinstance(value, (set, frozenset)):
        return sorted((_canonical(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True, default=str))
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    return value


def _md5(value, unserialisable: list = None, name: str = "") -> str:
    """Content digest of one field. A value that cannot be serialised is recorded by name in ``unserialisable`` (the test fails naming it) and digested by its type."""
    try:
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            value = dataclasses.asdict(value)
        text = json.dumps(_canonical(value), sort_keys=True, default=str)
    except Exception as exc:  # noqa: BLE001 - a field that cannot be serialised is named, not silently compared by its error text
        if unserialisable is not None:
            unserialisable.append(name)
        text = f"UNSERIALISABLE {type(value).__name__} {exc!r}"
    return hashlib.md5(text.encode()).hexdigest()[:12]


def _digest(state) -> dict:
    """Every entity field and every top-level state field by content (not only the canonical subset); ``unserialisable`` names any field that could not be digested."""
    bad: list = []
    fields = {f.name: _md5(getattr(state, f.name, None), bad, f"state.{f.name}") for f in dataclasses.fields(state) if not _skipped(f.name, _DERIVED_STATE_FIELDS)}
    entities = {str(eid): {f.name: _md5(getattr(e, f.name, None), bad, f"entity.{f.name}") for f in dataclasses.fields(e) if not _skipped(f.name, _SKIP_ENTITY_FIELDS)}
                for eid, e in state.entities.items()}
    return {"state": fields, "entities": entities, "unserialisable": sorted(set(bad))}


def _kernel(world: str, seed: int, concurrent: bool, run_id: str) -> Kernel:
    spec, context = WorldRepository(WORLDS_DIR).load_world_with_context(world)
    state, _report = WorldCompiler.compile(spec, seed, context=context)
    extra = {} if concurrent else {"executor": LocalSequentialExecutor()}  # no executor given: PROD_SMALL has 2 workers, so the kernel builds ConcurrentExecutionAdapter
    return Kernel(PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state, DeterministicRNG(seed), governor=PinnedNormalGovernor(),
                  flags={"audit_mode": True, "no_frame_pacing": True}, run_id=run_id, **extra)


def snapshots(world: str, seed: int, ticks: int, concurrent: bool, run_id: str, monkeypatch) -> tuple:
    """Run one arm live; return ({tick: (hash, digest)}, the number of worker FAILURE no-ops)."""
    failures = []
    real = worker_manager.failure_no_op
    monkeypatch.setattr(worker_manager, "failure_no_op", lambda packet: (failures.append(packet.packet_id), real(packet))[1])
    kernel = _kernel(world, seed, concurrent, run_id)
    if concurrent:
        pool = getattr(getattr(kernel, "_executor", None), "_worker_manager", None)
        pool = getattr(pool, "_pool", None)
        assert isinstance(pool, ThreadPoolExecutor), (
            f"the concurrent arm's pool is {type(pool).__name__}, not a ThreadPoolExecutor: the worker failure count is taken by patching "
            "worker_manager.failure_no_op in this process, which only holds on threads (a process pool would count nothing and pass vacuously)")
    out = {}
    try:
        for tick in range(1, ticks + 1):
            kernel.tick_once()
            if tick % SAMPLE_EVERY == 0 or tick == ticks:
                out[tick] = (CanonicalStateHasher.get_hash(kernel.state), _digest(kernel.state))
    finally:
        kernel.shutdown()
    return out, len(failures)


def first_mismatch(a: dict, b: dict):
    """The first sampled tick at which the two arms differ, with what differs, or None."""
    for tick in sorted(set(a) & set(b)):
        if a[tick][0] != b[tick][0]:
            return tick, "canonical state hash"
        da, db = a[tick][1], b[tick][1]
        for name in sorted(set(da["state"]) | set(db["state"])):
            if da["state"].get(name) != db["state"].get(name):
                return tick, f"state field {name}"
        for eid in sorted(set(da["entities"]) | set(db["entities"]), key=int):
            ea, eb = da["entities"].get(eid, {}), db["entities"].get(eid, {})
            for name in sorted(set(ea) | set(eb)):
                if ea.get(name) != eb.get(name):
                    return tick, f"entity {eid} field {name}"
    return None


# (world, seed, ticks), picked from the evidence run (15 cases, 3 worlds x seeds 42-46; the pre-fix concurrent arm split in all 15 within 100-300 ticks, the fixed arm
# equalled sequential in all 15): crowded s45 is the world and seed that split at t2051-2100 on main and carries the seed cause; crowded s42 split at t1974 with the seed and
# flag causes fixed (the blocked_tiles cause, a late split); urban s42 is the cheapest world and a different cognition path (pre-fix first mismatch t300); frontier s44 is the
# cheapest frontier case.
CASES = [("crowded_frontier", 45, 2200), ("crowded_frontier", 42, 2000), ("urban_political", 42, 2000), ("frontier_living_world", 44, 2000)]


@pytest.mark.extra_slow
@pytest.mark.parametrize("world,seed,ticks", CASES, ids=[f"{w}-s{s}-{t}t" for w, s, t in CASES])
def test_the_sequential_and_the_concurrent_executor_give_the_same_world(world, seed, ticks, monkeypatch):
    sequential, seq_failures = snapshots(world, seed, ticks, False, f"eqlong_seq_{world}_{seed}", monkeypatch)
    concurrent, con_failures = snapshots(world, seed, ticks, True, f"eqlong_con_{world}_{seed}", monkeypatch)
    assert (seq_failures, con_failures) == (0, 0), "a worker FAILURE no-op happened: a worker failure is a split (contract section 4)"
    named = sorted({n for snaps in (sequential, concurrent) for _hash, digest in snaps.values() for n in digest["unserialisable"]})
    assert named == [], f"fields the digest could not serialise (compared by their error text, not by content): {named}"
    mismatch = first_mismatch(sequential, concurrent)
    assert mismatch is None, f"{world} seed {seed}: the executors first differ at tick {mismatch[0]} ({mismatch[1]})"


@pytest.mark.extra_slow
def test_the_concurrent_executor_repeats_itself(monkeypatch):
    """Concurrent against concurrent decides whether a difference is stable (a cause) or a race (kind flaky)."""
    first, f1 = snapshots("crowded_frontier", 45, 2000, True, "eqlong_con_a", monkeypatch)
    second, f2 = snapshots("crowded_frontier", 45, 2000, True, "eqlong_con_b", monkeypatch)
    assert (f1, f2) == (0, 0)
    named = sorted({n for snaps in (first, second) for _hash, digest in snaps.values() for n in digest["unserialisable"]})
    assert named == [], f"fields the digest could not serialise: {named}"
    mismatch = first_mismatch(first, second)
    assert mismatch is None, f"two concurrent runs of the same seed first differ at tick {mismatch[0]} ({mismatch[1]})"
