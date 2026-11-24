"""The per-tick replay digest's memo gives the same digest as the old build, on real worlds and on hand-made states
(TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK).

The reference is `canonical_reference.py`: `EntityState.to_canonical_dict` as it was on origin/main, with the strategic and social blocks inline and no memo of any kind. Every case
compares the digest, the compact JSON, the pretty JSON and the data dict with it. Real worlds: `frontier_living_world` (bonds on 293 of 300 ticks) and `crowded_frontier` (bonds on 287,
trust_history on 181); no world produced a betrayal, a nemesis or a marriage in 300 ticks, so those fields are exercised by hand-made components.
"""
from __future__ import annotations

import dataclasses
import json
import pickle
import shutil
from pathlib import Path
from typing import Any, List
from unittest.mock import patch

import pytest

from src.core.protocol_validator import ProtocolViolationError
from src.core.death_cause import DeathCause, DeathRecord
from src.core.grief_triggers import pending_grief_triggers
from src.core.models.social import BetrayalRecord, SocialBond
from src.core.strategic import ProjectState
from src.core.state import AuthoritativeState, strategic_canonical_dict, social_canonical_dict
from src.engine.checkpoint_schema import _SchemaPickler, class_key
from src.engine.scenario_checkpoint import ScenarioCheckpointer
from src.scenarios.schema import SimulationScenarioDefinition
from tests.named_run_dirs import remove_restored_run_dirs  # noqa: F401
from tests.unit.engine.checkpoint_helpers import write_checkpoint
from src.engine.checkpoint import CanonicalFragmentMemo, CanonicalHashScheduler, CanonicalStateHasher, DigestStatus
from tests.unit.engine.canonical_reference import reference_canonical_data, reference_digest, reference_json
from tests.unit.engine.test_proof_digest_contract import _cached_objects, audit_cached_canonical_dicts
from tools.test_architecture.rpg_gate_run import build_kernel

WORLDS = ["frontier_living_world", "crowded_frontier"]
TICKS = 70


def _run_dir(run_id: str) -> Path:
    return Path("data") / "runs" / run_id


class _Run:
    """A real kernel run that keeps the kernel until `close`: the per-tick digest memo is the kernel's own."""

    def __init__(self, world: str, seed: int = 42, **extra_flags: Any) -> None:
        self.run_id = f"digest_memo_{world}_{seed}_{id(self)}"
        self.kernel = build_kernel(world, seed, self.run_id)
        if extra_flags:
            self.kernel._force_full_scan = bool(extra_flags.get("force_full_scan", False))

    def close(self) -> None:
        self.kernel.shutdown()
        shutil.rmtree(_run_dir(self.run_id), ignore_errors=True)


def _clear_memos(state: AuthoritativeState) -> List[Any]:
    holders = _cached_objects(state)
    saved = [(h, h._canonical_cache) for h in holders]
    for h, _ in saved:
        object.__setattr__(h, "_canonical_cache", None)
    return saved


def _restore_memos(saved: List[Any]) -> None:
    for h, cached in saved:
        object.__setattr__(h, "_canonical_cache", cached)


def _assert_equals_reference(state: AuthoritativeState, memo: CanonicalFragmentMemo, *, deep: bool = True) -> None:
    expected = reference_digest(state)
    assert CanonicalStateHasher.get_hash(state) == expected
    assert CanonicalStateHasher.get_hash(state, memo) == expected
    if deep:
        assert CanonicalStateHasher.to_canonical_json(state) == reference_json(state)
        assert CanonicalStateHasher.to_canonical_json(state, memo=memo) == reference_json(state)
        assert CanonicalStateHasher.to_canonical_json(state, pretty=True) == reference_json(state, pretty=True)
        assert CanonicalStateHasher.to_canonical_data(state, memo) == reference_canonical_data(state)


@pytest.fixture(scope="module", params=WORLDS)
def world_run(request):
    run = _Run(request.param)
    try:
        yield run
    finally:
        run.close()


# ---------------------------------------------------------------------------
# E1 / E2 / E3 / E4: real worlds, every tick
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("world", WORLDS)
def test_every_tick_of_a_real_world_digests_to_the_reference_warm_and_cold(world: str):
    run = _Run(world)
    kernel, bonds_ticks, trust_ticks = run.kernel, 0, 0
    try:
        for tick in range(TICKS):
            kernel.tick_once()
            state = kernel.state
            memo = kernel._canonical_memo
            _assert_equals_reference(state, memo, deep=(tick % 10 == 0))
            if tick % 17 == 0:  # the same state with every memo cleared (components and entities): a cold build gives the same digest
                saved = _clear_memos(state)
                try:
                    fresh = CanonicalFragmentMemo()
                    assert CanonicalStateHasher.get_hash(state, fresh) == reference_digest(state)
                finally:
                    _restore_memos(saved)
            assert len(memo) <= 2 * len(state.entities), "the memo outgrew one state"
            assert memo.audit() == []
            bonds_ticks += any(e.social.bonds for e in state.entities.values())
            trust_ticks += any(e.social.trust_history for e in state.entities.values())
        assert memo.hits > memo.misses, "the memo hardly hit: the social/strategic components should be reused across ticks"
        assert bonds_ticks > TICKS * 0.5, f"{world}: the social memo was barely exercised ({bonds_ticks} ticks with bonds)"
    finally:
        run.close()


def test_the_kernels_own_tick_end_digest_is_the_reference_digest():
    run = _Run("frontier_living_world")
    kernel, seen = run.kernel, []
    try:
        with patch.object(kernel._replay, "emit", side_effect=lambda event, policy: seen.append((event.payload, reference_digest(kernel.state)))):
            for _ in range(12):
                kernel.tick_once()
        digests = [(p, ref) for p, ref in seen if isinstance(p, dict) and "digest_status" in p]
        assert len(digests) == 12
        for payload, ref in digests:
            assert payload["digest_status"] == DigestStatus.COMPUTED.value
            assert payload["hash"] == ref
        assert kernel._canonical_memo.hits > 0
    finally:
        run.close()


def test_force_full_scan_and_the_certification_path_digest_to_the_reference():
    run = _Run("frontier_living_world", force_full_scan=True)
    kernel = run.kernel
    try:
        for _ in range(25):
            kernel.tick_once()
        state = kernel.state
        sched = CanonicalHashScheduler()
        assert sched.compute_digest(state, state.tick, reason="certification").require_value() == reference_digest(state)
        assert sched.compute_digest(state, state.tick, reason="replay", memo=kernel._canonical_memo).require_value() == reference_digest(state)
        assert CanonicalHashScheduler(state.tick).compute_digest(state, state.tick).require_value() == reference_digest(state)  # the final digest: no memo
    finally:
        run.close()


# ---------------------------------------------------------------------------
# E5 / E6: spawn, death, insert, delete on a real state
# ---------------------------------------------------------------------------

def test_spawn_death_insert_and_delete_digest_to_the_reference(world_run):
    kernel = world_run.kernel
    for _ in range(30):
        kernel.tick_once()
    state, memo = kernel.state, kernel._canonical_memo
    ids = sorted(state.entities)
    _assert_equals_reference(state, memo)
    without = {k: v for k, v in state.entities.items() if k != ids[0]}  # a death (an entity removed)
    s_dead = dataclasses.replace(state, entities=without)
    _assert_equals_reference(s_dead, memo)
    assert len(memo) <= 2 * len(s_dead.entities)  # the prune dropped the removed entity's components
    clone = dataclasses.replace(state.entities[ids[1]], id=max(ids) + 1)  # a spawn (same components under a new id)
    s_spawn = dataclasses.replace(state, entities={**state.entities, clone.id: clone})
    _assert_equals_reference(s_spawn, memo)
    s_groups = dataclasses.replace(state, groups={})  # a keyed collection emptied
    _assert_equals_reference(s_groups, memo)
    s_events = dataclasses.replace(state, recent_world_events=tuple(state.recent_world_events)[:-1])
    _assert_equals_reference(s_events, memo)


# ---------------------------------------------------------------------------
# E7 / E8: components with every container filled; encoder-sensitive values
# ---------------------------------------------------------------------------

def _rich(state: AuthoritativeState) -> AuthoritativeState:
    """The entity with the most filled strategic containers, with every social container filled by hand."""
    def filled(e):
        return sum(bool(getattr(e.strategic, f.name)) for f in dataclasses.fields(e.strategic) if isinstance(getattr(e.strategic, f.name), (dict, list, tuple)))
    eid = max(state.entities, key=lambda i: filled(state.entities[i]))
    ent = state.entities[eid]
    social = dataclasses.replace(
        ent.social,
        trust_history={3: 0.5, 10: 0.25, 2: 1.0}, familiarity_history={1: 1e-05, 11: 1e16}, debt_history={4: -0.0}, fear_history={5: 0.1}, grudge_history={6: 0.3},
        combat_loss_counts={7: 2}, salience_history={8: 0.75}, bonds={9: SocialBond(target_id=9, familiarity=0.5, sentiment=-0.25), 12: SocialBond(target_id=12)},
        nemesis_ids={6, 2, 11}, place_attachment={"r_b": 0.5, "r_a": 1.0}, regional_reputation={"r_a": 1.5}, betrayal_count=1,
        betrayal_records=[BetrayalRecord(contract_id="c1", betrayer_id=9, victim_id=eid, severity=0.5, tick=3)], public_reputation=0.5, heroism_score=1.5,
        notoriety_score=2.5, last_offer_tick=4, rejection_count={13: 2, 2: 1},
    )
    strategic = dataclasses.replace(ent.strategic, boredom={"z_kind": 1e-05, "a_kind": 3.0}, home_region_id="ünïcode-région")
    return dataclasses.replace(state, entities={**state.entities, eid: dataclasses.replace(ent, strategic=strategic, social=social)})


def test_a_component_with_every_container_filled_equals_the_old_inline_build(world_run):
    kernel = world_run.kernel
    for _ in range(40):
        kernel.tick_once()
    state = _rich(kernel.state)
    memo = CanonicalFragmentMemo()
    _assert_equals_reference(state, memo)
    ent = max(state.entities.values(), key=lambda e: len(e.social.nemesis_ids))
    assert ent.social.nemesis_ids and ent.social.betrayal_records
    assert strategic_canonical_dict(ent.strategic) == reference_canonical_data(state)["entities"][str(ent.id)]["strategic"]
    assert social_canonical_dict(ent.social) == reference_canonical_data(state)["entities"][str(ent.id)]["social"]
    assert "ü" not in CanonicalStateHasher.to_canonical_json(state)  # ensure_ascii: the escape, not the character
    assert "\\u00fc" in CanonicalStateHasher.to_canonical_json(state)


# ---------------------------------------------------------------------------
# E9 / E10 / E11: the audit sees an in-place write, a poisoned entry and a caller that edits the returned dict
# ---------------------------------------------------------------------------

def _warm(world_run):
    kernel = world_run.kernel
    for _ in range(12):
        kernel.tick_once()
    return kernel.state, kernel._canonical_memo


def test_an_in_place_write_into_a_memoized_component_is_found_by_the_audit(world_run):
    state, memo = _warm(world_run)
    assert memo.audit() == []
    victim = next(e for e in state.entities.values() if memo._strategic.get(id(e.strategic)))
    victim.strategic.boredom["__planted__"] = 9.0  # frontier: a plain dict, nothing stops it
    try:
        assert any("strategic" in m for m in memo.audit())
        assert CanonicalStateHasher.get_hash(state, memo) != reference_digest(state) or CanonicalStateHasher.get_hash(state) != reference_digest(state)  # the stated limit
    finally:
        del victim.strategic.boredom["__planted__"]
    assert memo.audit() == []


def test_a_poisoned_memo_entry_and_a_caller_editing_the_returned_dict_are_found(world_run):
    state, memo = _warm(world_run)
    strat = next(e.strategic for e in state.entities.values() if memo._strategic.get(id(e.strategic)))
    social = next(e.social for e in state.entities.values() if memo._social.get(id(e.social)))
    returned = memo.strategic(strat)  # the shared dict a caller receives
    returned["__caller_edit__"] = 1
    memo.social(social)["bonds"]["__poison__"] = {}
    try:
        found = memo.audit()
        assert any("strategic" in m for m in found) and any("social" in m for m in found)
        assert audit_cached_canonical_dicts(state), "the entity memo embeds the shared dict, so the existing audit also sees the edit"
    finally:
        returned.pop("__caller_edit__")
        memo.social(social)["bonds"].pop("__poison__")
    assert memo.audit() == []
    assert audit_cached_canonical_dicts(state) == []


# ---------------------------------------------------------------------------
# E10 (replace), E14 (no persistence, bounded), E12 (replay form untouched)
# ---------------------------------------------------------------------------

def test_a_replaced_component_is_a_new_key_and_the_old_entry_is_pruned(world_run):
    state, memo = _warm(world_run)
    ent = next(iter(state.entities.values()))
    memo.strategic(ent.strategic)
    twin = dataclasses.replace(ent.strategic)  # same values, a new object
    misses = memo.misses
    d_old, d_new = memo.strategic(ent.strategic), memo.strategic(twin)
    assert memo.misses == misses + 1 and d_old == d_new and d_old is not d_new
    memo.prune(state)
    assert id(twin) not in memo._strategic


def test_the_memo_is_not_state_and_a_restored_state_digests_the_same_cold_or_warm(world_run):
    state, memo = _warm(world_run)
    assert not hasattr(state, "_canonical_memo")
    blob = pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)
    assert b"CanonicalFragmentMemo" not in blob
    restored = pickle.loads(blob)
    cold = CanonicalStateHasher.get_hash(restored, CanonicalFragmentMemo())
    warm = CanonicalStateHasher.get_hash(restored, memo)
    assert cold == warm == reference_digest(restored) == reference_digest(state)
    assert len(CanonicalFragmentMemo()) == 0


def test_a_new_kernel_starts_with_an_empty_memo_and_the_memo_is_per_kernel():
    a, b = _Run("frontier_living_world"), _Run("frontier_living_world")
    try:
        assert a.kernel._canonical_memo is not b.kernel._canonical_memo
        assert len(a.kernel._canonical_memo) == 0 and len(b.kernel._canonical_memo) == 0
        a.kernel.tick_once()
        assert len(a.kernel._canonical_memo) > 0 and len(b.kernel._canonical_memo) == 0
    finally:
        a.close()
        b.close()


def test_the_replay_form_and_the_fingerprint_do_not_depend_on_the_memo(world_run):
    state, memo = _warm(world_run)
    before = state.fingerprint()
    CanonicalStateHasher.get_hash(state, memo)
    assert state.fingerprint() == before
    payload = {"hash": reference_digest(state), "scheme": "flat-sha256-v5", "digest_status": DigestStatus.COMPUTED.value}
    assert json.dumps(payload, sort_keys=True) == json.dumps({"hash": CanonicalStateHasher.get_hash(state, memo), "scheme": "flat-sha256-v5", "digest_status": "computed"}, sort_keys=True)


def test_without_a_memo_the_old_path_is_unchanged_and_the_hasher_signature_defaults_to_none():
    import inspect
    for fn in (CanonicalStateHasher.get_hash, CanonicalStateHasher.to_canonical_data, CanonicalStateHasher.to_canonical_json, CanonicalHashScheduler.compute_digest):
        assert inspect.signature(fn).parameters["memo"].default is None


# ---------------------------------------------------------------------------
# E16: a checkpoint that predates a strategic field is filled before any memo exists, and a restored kernel starts empty
# ---------------------------------------------------------------------------

_PRE_FIELDS = ("cleared_since", "suspended_since", "ended_tick")  # the three trailing ProjectState fields that have FIELD_RULES rows


def _rebuild_old_project(cls, old_values):
    obj = cls.__new__(cls)
    cls.__setstate__(obj, old_values)  # positional, as an old pickle loads: the record is three values short
    return obj


class _OldProjectPickler(_SchemaPickler):
    """Writes every ProjectState as an OLD-shape record (without the three trailing fields) and fingerprints it that way."""

    def reducer_override(self, obj):
        if type(obj) is ProjectState:
            names = [f.name for f in dataclasses.fields(ProjectState)]
            old = [n for n in names if n not in _PRE_FIELDS]
            self.schema[class_key(ProjectState)] = old
            return _rebuild_old_project, (ProjectState, tuple(getattr(obj, n) for n in old))
        return super().reducer_override(obj)


@pytest.mark.usefixtures("remove_restored_run_dirs")
def test_a_restore_that_fills_a_strategic_field_starts_with_an_empty_memo_and_digests_to_the_reference(tmp_path):
    import io
    run_a = _Run("frontier_living_world")
    kernel_a = run_a.kernel
    try:
        for _ in range(60):
            kernel_a.tick_once()
            if any(e.strategic.projects for e in kernel_a.state.entities.values()):
                break
        for _ in range(8):
            kernel_a.tick_once()
        state_a = kernel_a.state
        projects = [p for e in state_a.entities.values() for p in e.strategic.projects.values() if type(p) is ProjectState]
        assert projects, "no entity held a plain ProjectState: the fill rows would not be exercised"
        assert len(kernel_a._canonical_memo) > 0  # A's memo is warm and A (with its strong references) stays alive for the whole test
        buf = io.BytesIO()
        pickler = _OldProjectPickler(buf, protocol=pickle.HIGHEST_PROTOCOL)
        pickler.dump(state_a)
        schema = {k: list(v) for k, v in pickler.schema.items()}
        path = write_checkpoint(tmp_path / "old.bin", buf.getvalue(), "s", schema, tick=state_a.tick)
        spec = SimulationScenarioDefinition(id="s", world_composition="frontier_living_world", perspective="hero_guild_perspective")
        svc = ScenarioCheckpointer.restore(path, spec)
        kernel_b = svc._kernel
        try:
            restored = [p for e in kernel_b.state.entities.values() for p in e.strategic.projects.values() if type(p) is ProjectState]
            assert len(restored) == len(projects)
            assert all(getattr(p, f) is None for p in restored for f in _PRE_FIELDS), "the fill rows did not run on the restored projects"
            assert len(kernel_b._canonical_memo) == 0 and kernel_b._canonical_memo is not kernel_a._canonical_memo
            before_a = len(kernel_a._canonical_memo)
            kernel_b.tick_once()
            state_b = kernel_b.state
            assert CanonicalStateHasher.get_hash(state_b, kernel_b._canonical_memo) == reference_digest(state_b)
            assert CanonicalStateHasher.get_hash(state_b, CanonicalFragmentMemo()) == reference_digest(state_b)
            assert len(kernel_a._canonical_memo) == before_a, "kernel B must not touch kernel A's memo"
            assert kernel_a._canonical_memo.audit() == []
        finally:
            kernel_b.shutdown()
    finally:
        run_a.close()


# ---------------------------------------------------------------------------
# E17: a live kernel with a warm memo reassigns its state through apply_generation; the teardown flush is the second site
# ---------------------------------------------------------------------------

def test_the_grief_flush_on_a_warm_kernel_digests_to_the_reference():
    run = _Run("frontier_living_world")
    kernel = run.kernel
    try:
        for _ in range(25):
            kernel.tick_once()
        memo = kernel._canonical_memo
        assert len(memo) > 0
        st = kernel.state
        ids = sorted(e for e, ent in st.entities.items() if ent.lifecycle.active)
        dead_id, griever_id = ids[0], ids[1]
        dead = st.entities[dead_id]
        griever = st.entities[griever_id]
        dead = dataclasses.replace(dead, lifecycle=dataclasses.replace(dead.lifecycle, active=False, death_record=DeathRecord(cause=DeathCause.COMBAT, tick=st.tick - 1)))
        griever = dataclasses.replace(griever, social=dataclasses.replace(griever.social, trust_history={**griever.social.trust_history, dead_id: 0.9}))
        planted = dataclasses.replace(st, entities={**st.entities, dead_id: dead, griever_id: griever})
        kernel._state = planted
        assert pending_grief_triggers(planted), "the planted death owes a grief trigger"
        assert CanonicalStateHasher.get_hash(planted, memo) == reference_digest(planted)  # warm memo, the planted state
        kernel.drain_pending_triggers_at_teardown()  # the apply_generation site that does not advance the tick
        after = kernel.state
        assert after is not planted and after.grief_drained_tick != planted.grief_drained_tick
        assert f"grief_ally_{dead_id}" in after.entities[griever_id].strategic.concerns or after.entities[griever_id].strategic.concerns != planted.entities[griever_id].strategic.concerns
        assert CanonicalStateHasher.get_hash(after, memo) == reference_digest(after)
        assert memo.audit() == []
        kernel.tick_once()
        assert CanonicalStateHasher.get_hash(kernel.state, memo) == reference_digest(kernel.state)
    finally:
        run.close()


# ---------------------------------------------------------------------------
# The periodic memo audit (audit_mode only, every CANONICAL_MEMO_AUDIT_PERIOD ticks)
# ---------------------------------------------------------------------------

def _plant(kernel):
    """An in-place write into a memoized strategic component; returns an undo."""
    state, memo = kernel.state, kernel._canonical_memo
    victim = next(e for e in state.entities.values() if memo._strategic.get(id(e.strategic)))
    victim.strategic.boredom["__planted__"] = 9.0
    return lambda: victim.strategic.boredom.pop("__planted__", None)


def test_the_audit_period_is_a_named_constant_and_the_cadence_is_the_tick():
    import src.engine.kernel as kernel_module
    assert kernel_module.CANONICAL_MEMO_AUDIT_PERIOD == 100


def test_a_planted_in_place_write_raises_on_an_audit_tick_under_audit_mode(monkeypatch):
    import src.engine.kernel as kernel_module
    run = _Run("frontier_living_world")
    kernel = run.kernel
    try:
        for _ in range(8):
            kernel.tick_once()
        assert kernel._audit_mode is True
        undo = _plant(kernel)
        monkeypatch.setattr(kernel_module, "CANONICAL_MEMO_AUDIT_PERIOD", kernel.state.tick)  # this tick is an audit tick
        with pytest.raises(ProtocolViolationError, match="Canonical digest memo is stale"):
            kernel._phase_persistence()
        undo()
        kernel._phase_persistence()  # clean again: the audit passes
    finally:
        run.close()


def test_the_same_plant_without_audit_mode_raises_nothing_and_that_is_the_stated_limit(monkeypatch):
    import src.engine.kernel as kernel_module
    run = _Run("frontier_living_world")
    kernel = run.kernel
    try:
        for _ in range(8):
            kernel.tick_once()
        kernel._audit_mode = False
        undo = _plant(kernel)
        monkeypatch.setattr(kernel_module, "CANONICAL_MEMO_AUDIT_PERIOD", kernel.state.tick)
        kernel._phase_persistence()  # no audit: nothing raised
        undo()
    finally:
        run.close()


def test_a_clean_audit_mode_run_digests_the_same_with_and_without_the_audit(monkeypatch):
    import src.engine.kernel as kernel_module

    def digests(period: int):
        monkeypatch.setattr(kernel_module, "CANONICAL_MEMO_AUDIT_PERIOD", period)
        run = _Run("frontier_living_world")
        seen = []
        try:
            with patch.object(run.kernel._replay, "emit", side_effect=lambda event, policy: seen.append(event.payload.get("hash") if isinstance(event.payload, dict) else None)):
                for _ in range(14):
                    run.kernel.tick_once()
        finally:
            run.close()
        return seen

    with_audit, without = digests(3), digests(10 ** 9)
    assert len(with_audit) >= 14 and with_audit == without


def test_a_tick_that_is_not_a_multiple_of_the_period_runs_no_audit_and_the_audit_changes_nothing(monkeypatch):
    import src.engine.kernel as kernel_module
    calls = []
    real = CanonicalFragmentMemo.audit
    monkeypatch.setattr(CanonicalFragmentMemo, "audit", lambda self: (calls.append(1), real(self))[1])
    monkeypatch.setattr(kernel_module, "CANONICAL_MEMO_AUDIT_PERIOD", 4)
    run = _Run("frontier_living_world")
    kernel, ticks = run.kernel, []
    try:
        for _ in range(9):
            before = len(calls)
            kernel.tick_once()
            ticks.append((kernel.state.tick, len(calls) - before))
        assert [t for t, n in ticks if n] == [t for t, _ in ticks if t % 4 == 0]
        assert all(n in (0, 1) for _, n in ticks)
        memo = kernel._canonical_memo
        before_tables = ({k: v[1] for k, v in memo._strategic.items()}, {k: v[1] for k, v in memo._social.items()})
        digest = CanonicalStateHasher.get_hash(kernel.state, memo)
        memo.audit()
        assert ({k: v[1] for k, v in memo._strategic.items()}, {k: v[1] for k, v in memo._social.items()}) == before_tables
        assert CanonicalStateHasher.get_hash(kernel.state, memo) == digest == reference_digest(kernel.state)
    finally:
        run.close()
