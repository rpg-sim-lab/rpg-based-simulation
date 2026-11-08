"""
Integration tests for ScenarioRuntimeService objective FSM and stall detector.

Ticket: TCK-20260619-E31B-OBJECTIVE-FSM
AC coverage:
  AC1 — tick_limit victory condition → OBJECTIVE_MET at correct tick
  AC2 — entity_count failure condition → OBJECTIVE_FAILED
  AC3 — stall detector fires STALLED after STALL_THRESHOLD ticks with zero events
  AC4 — no victory conditions → stays RUNNING
  AC5 — step() on terminal state raises RuntimeError
"""
from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock


# ── helpers ───────────────────────────────────────────────────────────────────


def _make_spec(**kwargs):
    from src.scenarios.schema import SimulationScenarioDefinition
    defaults = {
        "id": "test_scenario",
        "world_composition": "frontier_living_world",
        "perspective": "hero_guild_perspective",
    }
    defaults.update(kwargs)
    return SimulationScenarioDefinition(**defaults)


def _make_service(**spec_kwargs):
    from src.engine.scenario_runtime import ScenarioRuntimeService
    return ScenarioRuntimeService(_make_spec(**spec_kwargs))


def _make_mock_kernel(*, tick: int = 0, entities: dict | None = None, event_count: int = 0):
    """Return a MagicMock kernel whose state matches the given parameters.

    tick_once() increments kernel.state.tick by 1 each call so that
    ObjectiveEvaluator sees a moving tick value.
    """
    mock_kernel = MagicMock()
    mock_kernel._current_tick_event_count = event_count

    state = MagicMock()
    state.tick = tick
    state.entities = entities if entities is not None else {}
    mock_kernel.state = state

    # Simulate tick_once() advancing state.tick
    def _tick_once():
        mock_kernel.state.tick += 1

    mock_kernel.tick_once.side_effect = _tick_once
    return mock_kernel


# ── AC1: tick_limit → OBJECTIVE_MET ──────────────────────────────────────────


class TestObjectiveMet:
    @pytest.mark.slow
    def test_scenario_reaches_objective_met(self):
        """Scenario with tick_limit:50 reaches OBJECTIVE_MET at tick 50 (real kernel)."""
        from src.engine.scenario_runtime import ScenarioObjectiveState
        svc = _make_service(victory_conditions=[{"kind": "tick_limit", "value": 50}])
        try:
            svc.start(tick_limit=100)
            assert svc.objective_state == ScenarioObjectiveState.OBJECTIVE_MET
            assert svc.tick == 50
        finally:
            svc.abort()

    def test_tick_limit_not_yet_reached_stays_running(self):
        """tick_limit:100, start(50) → still RUNNING at tick 50."""
        from src.engine.scenario_runtime import ScenarioObjectiveState
        svc = _make_service(victory_conditions=[{"kind": "tick_limit", "value": 100}])
        mock_kernel = _make_mock_kernel(tick=0)
        svc._kernel = mock_kernel
        svc.start(tick_limit=50)
        assert svc.objective_state == ScenarioObjectiveState.RUNNING
        assert svc.tick == 50

    def test_tick_limit_exact_boundary(self):
        """At tick == value the condition fires (>= not >)."""
        from src.engine.scenario_runtime import ScenarioObjectiveState
        svc = _make_service(victory_conditions=[{"kind": "tick_limit", "value": 10}])
        mock_kernel = _make_mock_kernel(tick=0)
        svc._kernel = mock_kernel
        svc.start(tick_limit=10)
        assert svc.objective_state == ScenarioObjectiveState.OBJECTIVE_MET

    def test_step_also_triggers_objective_met(self):
        """step() must evaluate objectives, not just _run_loop()."""
        from src.engine.scenario_runtime import ScenarioObjectiveState
        svc = _make_service(victory_conditions=[{"kind": "tick_limit", "value": 3}])
        mock_kernel = _make_mock_kernel(tick=0)
        svc._kernel = mock_kernel
        try:
            svc.step()  # tick → 1, state.tick → 1
            assert svc.objective_state == ScenarioObjectiveState.RUNNING
            svc.step()  # tick → 2, state.tick → 2
            assert svc.objective_state == ScenarioObjectiveState.RUNNING
            svc.step()  # tick → 3, state.tick → 3 → fires
            assert svc.objective_state == ScenarioObjectiveState.OBJECTIVE_MET
        finally:
            svc.abort()


# ── AC2: entity_count → OBJECTIVE_FAILED ──────────────────────────────────────


class TestObjectiveFailed:
    def test_entity_count_fires_when_alive_below_threshold(self):
        """entity_count condition fires when alive entities < value."""
        from src.engine.scenario_runtime import ScenarioObjectiveState, ObjectiveEvaluator
        dead_entity = MagicMock()
        dead_entity.combat.alive = False
        mock_state = MagicMock()
        mock_state.tick = 5
        mock_state.entities = {1: dead_entity}
        conditions = [{"kind": "entity_count", "value": 1}]
        result = ObjectiveEvaluator.evaluate(mock_state, conditions)
        assert result == ScenarioObjectiveState.OBJECTIVE_FAILED

    def test_entity_count_above_threshold_stays_running(self):
        """alive count >= value → RUNNING."""
        from src.engine.scenario_runtime import ScenarioObjectiveState, ObjectiveEvaluator
        live_entity = MagicMock()
        live_entity.combat.alive = True
        mock_state = MagicMock()
        mock_state.tick = 10
        mock_state.entities = {1: live_entity, 2: live_entity}
        conditions = [{"kind": "entity_count", "value": 1}]
        result = ObjectiveEvaluator.evaluate(mock_state, conditions)
        assert result == ScenarioObjectiveState.RUNNING

    def test_entity_count_uses_combat_alive_not_len(self):
        """Dead entities in dict do NOT count: uses e.combat.alive filter."""
        from src.engine.scenario_runtime import ScenarioObjectiveState, ObjectiveEvaluator
        alive = MagicMock()
        alive.combat.alive = True
        dead = MagicMock()
        dead.combat.alive = False
        mock_state = MagicMock()
        mock_state.tick = 1
        # 2 entities in dict, but only 1 alive; value=2 → alive(1) < 2 → FAILED
        mock_state.entities = {1: alive, 2: dead}
        result = ObjectiveEvaluator.evaluate(mock_state, [{"kind": "entity_count", "value": 2}])
        assert result == ScenarioObjectiveState.OBJECTIVE_FAILED

    def test_entity_count_wired_into_run_loop(self):
        """entity_count condition fires via _run_loop() when alive count drops below value."""
        from src.engine.scenario_runtime import ScenarioObjectiveState
        svc = _make_service(victory_conditions=[{"kind": "entity_count", "value": 1}])
        dead_entity = MagicMock()
        dead_entity.combat.alive = False
        mock_kernel = MagicMock()
        mock_kernel.state.tick = 0
        mock_kernel.state.entities = {1: dead_entity}
        mock_kernel._current_tick_event_count = 0
        # tick_once() doesn't change state in this mock
        svc._kernel = mock_kernel
        svc.start(tick_limit=5)
        assert svc.objective_state == ScenarioObjectiveState.OBJECTIVE_FAILED


# ── AC3: stall detector ────────────────────────────────────────────────────────


class TestStallDetector:
    def test_stall_threshold_is_50(self):
        from src.engine.scenario_runtime import STALL_THRESHOLD
        assert STALL_THRESHOLD == 50

    def test_stall_detector_fires_on_no_events(self):
        """STALLED fires after STALL_THRESHOLD + 1 consecutive ticks with zero events."""
        from src.engine.scenario_runtime import ScenarioObjectiveState, STALL_THRESHOLD
        # Scenario with no victory conditions so objective evaluation never fires
        svc = _make_service()
        mock_kernel = MagicMock()
        mock_kernel.state.entities = {}
        mock_kernel.state.tick = 0
        mock_kernel._current_tick_event_count = 0
        svc._kernel = mock_kernel
        # Drive STALL_THRESHOLD + 1 idle evaluation cycles directly
        for _ in range(STALL_THRESHOLD + 1):
            svc._tick += 1
            svc._evaluate_after_tick()
        assert svc.objective_state == ScenarioObjectiveState.STALLED

    def test_stall_resets_when_events_fire(self):
        """A tick with events resets the stall counter to 0."""
        from src.engine.scenario_runtime import ScenarioObjectiveState, STALL_THRESHOLD
        svc = _make_service()
        mock_kernel = MagicMock()
        mock_kernel.state.entities = {}
        mock_kernel.state.tick = 0
        svc._kernel = mock_kernel
        # Manually advance counter to STALL_THRESHOLD - 1
        svc._stall_counter = STALL_THRESHOLD - 1
        # One tick with events resets counter
        mock_kernel._current_tick_event_count = 3
        svc._tick += 1
        svc._evaluate_after_tick()
        assert svc._stall_counter == 0
        assert svc.objective_state == ScenarioObjectiveState.RUNNING

    def test_stall_not_fired_before_threshold(self):
        """Exactly STALL_THRESHOLD idle ticks do NOT trigger STALLED (requires > threshold)."""
        from src.engine.scenario_runtime import ScenarioObjectiveState, STALL_THRESHOLD
        svc = _make_service()
        mock_kernel = MagicMock()
        mock_kernel.state.entities = {}
        mock_kernel.state.tick = 0
        mock_kernel._current_tick_event_count = 0
        svc._kernel = mock_kernel
        # Drive exactly STALL_THRESHOLD idle ticks
        for _ in range(STALL_THRESHOLD):
            svc._tick += 1
            svc._evaluate_after_tick()
        # Counter is exactly STALL_THRESHOLD; condition is > threshold, not >=
        assert svc._stall_counter == STALL_THRESHOLD
        assert svc.objective_state == ScenarioObjectiveState.RUNNING

    def test_objective_takes_priority_over_stall(self):
        """When entities are dead, OBJECTIVE_FAILED fires before STALLED."""
        from src.engine.scenario_runtime import ScenarioObjectiveState, STALL_THRESHOLD
        dead_entity = MagicMock()
        dead_entity.combat.alive = False
        svc = _make_service(victory_conditions=[{"kind": "entity_count", "value": 1}])
        mock_kernel = MagicMock()
        mock_kernel.state.tick = 0
        mock_kernel.state.entities = {1: dead_entity}
        mock_kernel._current_tick_event_count = 0
        svc._kernel = mock_kernel
        # Even with high stall counter, objective fires first
        svc._stall_counter = STALL_THRESHOLD
        svc._tick += 1
        svc._evaluate_after_tick()
        assert svc.objective_state == ScenarioObjectiveState.OBJECTIVE_FAILED


# ── AC4: no victory conditions ────────────────────────────────────────────────


class TestNoVictoryConditions:
    def test_no_conditions_stays_running(self):
        """Spec with no victory_conditions never transitions via evaluator."""
        from src.engine.scenario_runtime import ScenarioObjectiveState, ObjectiveEvaluator
        state = MagicMock()
        state.tick = 9999
        result = ObjectiveEvaluator.evaluate(state, [])
        assert result == ScenarioObjectiveState.RUNNING

    def test_none_conditions_guard(self):
        """Passing None conditions (defensive) returns RUNNING."""
        from src.engine.scenario_runtime import ScenarioObjectiveState, ObjectiveEvaluator
        state = MagicMock()
        result = ObjectiveEvaluator.evaluate(state, None)
        assert result == ScenarioObjectiveState.RUNNING

    def test_service_without_victory_conditions_runs_to_limit(self):
        """Service with no conditions runs to tick_limit and stays RUNNING."""
        from src.engine.scenario_runtime import ScenarioObjectiveState
        svc = _make_service()
        mock_kernel = _make_mock_kernel(tick=0, event_count=1)
        svc._kernel = mock_kernel
        svc.start(tick_limit=10)
        assert svc.objective_state == ScenarioObjectiveState.RUNNING
        assert svc.tick == 10


# ── AC5: terminal state guards ────────────────────────────────────────────────


class TestTerminalStateGuards:
    def test_step_raises_after_objective_met(self):
        """step() raises RuntimeError when scenario is in OBJECTIVE_MET."""
        from src.engine.scenario_runtime import ScenarioObjectiveState
        svc = _make_service(victory_conditions=[{"kind": "tick_limit", "value": 1}])
        mock_kernel = _make_mock_kernel(tick=0)
        svc._kernel = mock_kernel
        svc.start(tick_limit=10)
        assert svc.objective_state == ScenarioObjectiveState.OBJECTIVE_MET
        with pytest.raises(RuntimeError):
            svc.step()

    def test_step_raises_after_objective_failed(self):
        """step() raises RuntimeError when scenario is in OBJECTIVE_FAILED."""
        from src.engine.scenario_runtime import ScenarioObjectiveState
        dead_entity = MagicMock()
        dead_entity.combat.alive = False
        svc = _make_service(victory_conditions=[{"kind": "entity_count", "value": 1}])
        mock_kernel = MagicMock()
        mock_kernel.state.tick = 0
        mock_kernel.state.entities = {1: dead_entity}
        mock_kernel._current_tick_event_count = 0
        svc._kernel = mock_kernel
        svc.start(tick_limit=5)
        assert svc.objective_state == ScenarioObjectiveState.OBJECTIVE_FAILED
        with pytest.raises(RuntimeError):
            svc.step()

    def test_step_raises_after_stalled(self):
        """step() raises RuntimeError when scenario is in STALLED."""
        from src.engine.scenario_runtime import ScenarioObjectiveState, STALL_THRESHOLD
        svc = _make_service()
        mock_kernel = MagicMock()
        mock_kernel.state.entities = {}
        mock_kernel.state.tick = 0
        mock_kernel._current_tick_event_count = 0
        svc._kernel = mock_kernel
        for _ in range(STALL_THRESHOLD + 1):
            svc._tick += 1
            svc._evaluate_after_tick()
        assert svc.objective_state == ScenarioObjectiveState.STALLED
        with pytest.raises(RuntimeError):
            svc.step()

    def test_step_raises_after_aborted(self):
        """step() raises RuntimeError when scenario is ABORTED (pre-existing guard)."""
        svc = _make_service()
        svc.abort()
        with pytest.raises(RuntimeError, match="aborted"):
            svc.step()


# ── E31C: checkpoint / restore ────────────────────────────────────────────────


class TestCheckpointRestore:
    """AC coverage for TCK-20260619-E31C-CHECKPOINT."""

    @pytest.mark.slow
    def test_checkpoint_restore_determinism(self, tmp_path):
        """Checkpoint at tick 25, restore, run to tick 50 → hash-identical final state.

        Uses CanonicalStateHasher.get_hash() with reason='certification' to compare
        final state between a reference run and a checkpoint-restored run.
        """
        from src.engine.scenario_checkpoint import ScenarioCheckpointer
        from src.engine.checkpoint import CanonicalStateHasher

        spec = _make_spec()
        checkpoint_path = tmp_path / "tick25.bin"

        # --- Reference run: uninterrupted 0→50 ---
        ref_svc = _make_service()
        try:
            ref_svc.start(tick_limit=50)
            ref_hash = CanonicalStateHasher.get_hash(ref_svc._kernel.state)
        finally:
            ref_svc.abort()

        # --- Checkpoint run: 0→25, save, restore, 25→50 ---
        ckpt_svc = _make_service()
        try:
            ckpt_svc.start(tick_limit=25)
            ScenarioCheckpointer.save(ckpt_svc, checkpoint_path)
        finally:
            ckpt_svc.abort()

        restored_svc = ScenarioCheckpointer.restore(checkpoint_path, spec)
        try:
            restored_svc.start(tick_limit=50)
            restored_hash = CanonicalStateHasher.get_hash(restored_svc._kernel.state)
        finally:
            restored_svc.abort()

        assert ref_hash == restored_hash, (
            f"Determinism broken: reference hash {ref_hash!r} != "
            f"restored hash {restored_hash!r}"
        )

    @pytest.mark.parametrize("seed", [0, 13])
    def test_restore_keeps_the_state_seed_and_the_per_tick_digest(self, tmp_path, seed):
        """A run restored at tick N matches the unbroken run at every tick N+1..N+k, for a nonzero seed too.

        The red of this test is the RNG assertions (seed and a stateless draw). The per-tick digest equality is the
        acceptance law, but it did not diverge on this fixture (hero and goblin, up to 80 ticks) so it alone cannot catch the defect.

        The service is built with an initial state, so the unbroken run's RNG uses base_seed=state.seed
        (scenario_runtime._build_kernel). Restore must give the resumed kernel's RNG the same base seed,
        or every stateless draw after the restore comes from seed 0. The default-built service in
        test_checkpoint_restore_determinism has no initial state and always takes the seed-0 branch,
        so it cannot see this.
        """
        from src.core.state import AuthoritativeState
        from src.engine.checkpoint import CanonicalStateHasher
        from src.engine.scenario_checkpoint import ScenarioCheckpointer
        from src.engine.scenario_runtime import ScenarioRuntimeService
        from src.systems.world_systems.generator import EntityGenerator

        spec = _make_spec()
        split, total = 6, 12

        def _fresh_service():
            gen = EntityGenerator(seed)
            hero = gen.spawn_hero((10.0, 10.0))
            goblin = gen.spawn_goblin((12.0, 12.0))
            state = AuthoritativeState(tick=0, seed=seed, entities={hero.id: hero, goblin.id: goblin})
            return ScenarioRuntimeService(spec, initial_state=state)

        def _digests(svc, ticks):
            out = []
            for _ in range(ticks):
                svc.step()
                out.append(CanonicalStateHasher.get_hash(svc._kernel.state))
            return out

        ref = _fresh_service()
        try:
            ref.start(tick_limit=split)
            ref_tail = _digests(ref, total - split)
        finally:
            ref.abort()

        ckpt = _fresh_service()
        path = tmp_path / "ckpt.bin"
        try:
            ckpt.start(tick_limit=split)
            ScenarioCheckpointer.save(ckpt, path)
        finally:
            ckpt.abort()

        restored = ScenarioCheckpointer.restore(path, spec)
        try:
            assert restored._kernel._rng.seed == seed
            # the behavioural form of the same law: a stateless draw is what a fresh run at this seed gives
            from src.platform.rng import DeterministicRNG
            from src.core.enums import Domain
            assert restored._kernel._rng.get_float(Domain.COMBAT, 7, 3) == DeterministicRNG(seed).get_float(Domain.COMBAT, 7, 3)
            restored_tail = _digests(restored, total - split)
        finally:
            restored.abort()

        assert restored_tail == ref_tail

    def test_checkpoint_file_contains_rng_checkpoint(self, tmp_path):
        """Checkpoint header contains rng_checkpoint field."""
        import struct
        from src.engine.scenario_checkpoint import ScenarioCheckpointer

        svc = _make_service()
        try:
            svc.start(tick_limit=5)
            path = tmp_path / "ckpt.bin"
            ScenarioCheckpointer.save(svc, path)
        finally:
            svc.abort()

        with path.open("rb") as f:
            header_len = struct.unpack("<I", f.read(4))[0]
            header = json.loads(f.read(header_len).decode("utf-8"))

        assert "rng_checkpoint" in header

    def test_restore_sets_service_tick(self, tmp_path):
        """Restored service.tick matches the checkpoint tick."""
        from src.engine.scenario_checkpoint import ScenarioCheckpointer

        svc = _make_service()
        try:
            svc.start(tick_limit=10)
            saved_tick = svc.tick
            path = tmp_path / "ckpt.bin"
            ScenarioCheckpointer.save(svc, path)
        finally:
            svc.abort()

        restored = ScenarioCheckpointer.restore(path, _make_spec())
        try:
            assert restored.tick == saved_tick
            assert restored._kernel.state.tick == saved_tick
        finally:
            restored.abort()

    @pytest.mark.slow
    def test_rng_checkpoint_populated_after_tick(self):
        """state.rng_checkpoint is non-None after one real tick."""
        svc = _make_service()
        try:
            svc.step()
            assert svc._kernel.state.rng_checkpoint is not None
        finally:
            svc.abort()

    def test_save_before_start_raises(self, tmp_path):
        """save() on unstarted service raises RuntimeError."""
        from src.engine.scenario_checkpoint import ScenarioCheckpointer

        svc = _make_service()
        with pytest.raises(RuntimeError, match="not been started"):
            ScenarioCheckpointer.save(svc, tmp_path / "ckpt.bin")
