"""TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK: an oscillation replan runs the rung ladder before it gives up, and the stored target is cleared
through the apply path (``clear_target`` was never applied; TCK-20261114-NAVIGATION-CLEAR-TARGET-FLAG-IS-NEVER-APPLIED)."""
from dataclasses import replace

import pytest

from tests.named_run_dirs import remove_restored_run_dirs  # noqa: F401

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, NavigationUpdate
from src.engine.movement import MovementSystem
from src.engine.patches import NavigationPatch


def _hero(**nav):
    return V2EntityBuilder(1).kind("HERO").location(5, 5).combat(readiness=100.0).navigation(**nav).build()


def _state(hero, *obstacles):
    ents = {1: hero, **{o.id: o for o in obstacles}}
    return AuthoritativeState(entities=ents, tick=0, seed=123)


def _wall(eid, x, y):
    return V2EntityBuilder(eid).kind("OBSTACLE").location(x, y).build()


def test_osc_loop_with_a_free_tile_round_it_steps_there_instead_of_giving_up():
    hero = _hero(target=(9, 5), last_position=(6, 5), oscillation_count=3)
    upd = MovementSystem.resolve_move(_state(hero), hero, (9, 5))[1]
    assert upd.new_position is not None and (int(upd.new_position[0]), int(upd.new_position[1])) not in {(5, 5), (6, 5)}
    assert upd.navigation.clear_target is False  # a way round was found: the target stays
    assert upd.navigation.oscillation_count_delta == -3  # a fresh cycle


def test_osc_loop_with_no_way_round_replans_and_clears_target_and_path():
    hero = _hero(target=(9, 5), last_position=(6, 5), oscillation_count=3)
    upd = MovementSystem.resolve_move(_state(hero, _wall(10, 5, 4), _wall(11, 5, 6), _wall(12, 4, 5)), hero, (9, 5))[1]
    assert upd.new_position is None
    assert upd.navigation.clear_target is True and upd.navigation.clear_path is True


def test_clear_target_is_applied_to_the_stored_target_through_the_patch():
    """S4: the flag every writer sets (movement.py replan, actor_validity.py, blacksmith.py) clears the stored target when the patch is applied."""
    hero = _hero(target=(9, 5))
    patch = NavigationPatch(entity_id=1, navigation=NavigationUpdate(clear_target=True))
    changes = {}
    patch.apply(hero, changes)
    assert changes["navigation"].target is None


def test_target_set_wins_over_clear_target_in_the_same_update():
    hero = _hero(target=(9, 5))
    patch = NavigationPatch(entity_id=1, navigation=NavigationUpdate(clear_target=True, target_set=(2, 2)))
    changes = {}
    patch.apply(hero, changes)
    assert tuple(changes["navigation"].target) == (2, 2)


def _apply_nav(entity, nav_update):
    changes = {}
    NavigationPatch(entity_id=entity.id, navigation=nav_update).apply(entity, changes)
    return changes["navigation"]


def test_actor_validity_writer_clears_the_target_through_the_apply_path():
    """S4, writer 2 (actor_validity.py): a sleeping subject's navigation proposal is stripped, and its stored target is cleared when applied."""
    from src.core.updates import StateUpdate
    from src.engine.pipeline_phases.actor_validity import ActorValidityPhase

    hero = V2EntityBuilder(1).kind("HERO").location(5, 5).combat(readiness=100.0).navigation(target=(9, 5)).properties({"status_sleeping": True}).build()
    state = _state(hero)
    refined = ActorValidityPhase.resolve(state, StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(2, 2)))}))
    nav = refined.entity_updates[1].navigation
    assert nav.clear_target is True and nav.target_set is None
    assert _apply_nav(hero, nav).target is None


def test_blacksmith_craft_writer_clears_the_target_through_the_apply_path():
    """S4, writer 3 (blacksmith.py): a completed craft clears the stale material-seeking target, and the apply path really clears it."""
    from src.core.state import ItemStack
    from src.core.updates import StateUpdate
    from src.engine.blacksmith import BlacksmithSystem

    recipe = BlacksmithSystem.RECIPES["craft_steel_sword"]
    hero = (V2EntityBuilder(1).kind("HERO").location(5, 5).combat(readiness=100.0).navigation(target=(9, 5))
            .identity(known_recipes={recipe.recipe_id}, craft_target=recipe.recipe_id)
            .inventory(items=[ItemStack(m, n) for m, n in recipe.materials.items()], gold=recipe.gold_cost + 1).build())
    state = replace(_state(hero), building_tiles={(5, 5): "blacksmith"})
    refined = BlacksmithSystem.enforce(state, StateUpdate())
    nav = refined.entity_updates[1].navigation
    assert nav.clear_target is True
    assert _apply_nav(hero, nav).target is None


# ---- the bounded give-up (2.213, rpg-designer 2026-11-17, N = 2) ----

WALL = [(6, y) for y in range(3, 8)]  # a straight wall of five obstacle tiles; a greedy walk east of (5,5) meets it head on


def _drive(hero, walls, target, ticks):
    """Chain resolve_move through the real navigation patch (the apply path); returns (final hero, [(position, wayround_count, target)])."""
    trace = []
    for tick in range(ticks):
        if hero.navigation.target is None:  # a give-up cleared the target and nothing in this driver re-chooses one (the brain does that in play)
            trace.append((tuple(int(c) for c in hero.navigation.position), hero.navigation.wayround_count, None))
            continue
        state = AuthoritativeState(entities={hero.id: hero, **walls}, tick=tick, seed=1)
        upd = MovementSystem.resolve_move(state, hero, target)[hero.id]
        changes = {}
        if upd.navigation is not None:
            NavigationPatch(entity_id=hero.id, navigation=upd.navigation).apply(hero, changes)
        nav = changes.get("navigation", hero.navigation)
        if upd.new_position is not None:
            nav = replace(nav, position=upd.new_position)
        if upd.navigation is not None and upd.navigation.last_position_set is not None:
            nav = replace(nav, last_position=upd.navigation.last_position_set)
        if upd.navigation is not None and upd.navigation.step_ready_tick_set is not None:
            nav = replace(nav, step_ready_tick=upd.navigation.step_ready_tick_set)
        hero = replace(hero, navigation=nav)
        trace.append((tuple(int(c) for c in nav.position), nav.wayround_count, nav.target))
    return hero, trace


def test_the_wall_probe_gives_up_after_two_no_progress_way_rounds_and_does_not_cycle():
    hero = V2EntityBuilder(1).kind("HERO").location(5, 5).combat(readiness=100.0).navigation(target=(9, 5)).build()
    walls = {10 + i: _wall(10 + i, *t) for i, t in enumerate(WALL)}
    hero, trace = _drive(hero, walls, (9, 5), 40)
    counts = [c for _, c, _ in trace]
    assert max(counts) == 2  # two way-round steps were allowed...
    gave_up = next(i for i, (_, _, tgt) in enumerate(trace) if tgt is None)  # ...and the third oscillation replan cleared the target
    assert counts[gave_up] == 0
    assert all(t is None for _, _, t in trace[gave_up:])  # no cycle: after the give-up nothing re-targets it, so it stays put
    assert hero.navigation.target is None and hero.navigation.wayround_best_distance is None


def test_progress_resets_the_way_round_count():
    """A way-round at a distance below the best seen is progress: the count restarts at 1 and the baseline moves down."""
    hero = _hero(target=(9, 5), last_position=(6, 5), oscillation_count=3)
    hero = replace(hero, navigation=replace(hero.navigation, wayround_count=2, wayround_best_distance=2, wayround_anchor=(9, 5), wayround_last_tick=0))
    upd = MovementSystem.resolve_move(_state(hero), hero, (9, 5))[1]  # distance 4 is not below 2: no progress -> the third event gives up
    assert upd.navigation.wayround_clear is True and upd.navigation.clear_target is True
    hero = replace(hero, navigation=replace(hero.navigation, wayround_best_distance=9))
    upd = MovementSystem.resolve_move(_state(hero), hero, (9, 5))[1]  # distance 4 is below the best 9: progress -> count 1, step taken
    assert upd.navigation.wayround_count_set == 1 and upd.navigation.wayround_best_distance_set == 4 and upd.new_position is not None


def _open_count(hero, count=2, best=4, anchor=(9, 5), last_tick=0):
    return replace(hero, navigation=replace(hero.navigation, wayround_count=count, wayround_best_distance=best, wayround_anchor=anchor, wayround_last_tick=last_tick))


def test_a_target_rewrite_or_clear_no_longer_ends_the_count_in_the_patch_only_the_give_up_does():
    """F1 (amends 2.213): the count belongs to the pursuit. The patch keeps it across a new, cleared or re-issued target; only wayround_clear ends it (all four fields together)."""
    hero = _open_count(_hero(target=(9, 5)))
    for update in (NavigationUpdate(target_set=(2, 2)), NavigationUpdate(target_clear=True), NavigationUpdate(clear_target=True), NavigationUpdate(target_set=(9, 5))):
        nav = _apply_nav(hero, update)
        assert (nav.wayround_count, nav.wayround_best_distance, nav.wayround_anchor, nav.wayround_last_tick) == (2, 4, (9, 5), 0)
    nav = _apply_nav(hero, NavigationUpdate(wayround_clear=True, clear_target=True))
    assert (nav.wayround_count, nav.wayround_best_distance, nav.wayround_anchor, nav.wayround_last_tick) == (0, None, None, None)


def _event(hero, target, tick):
    """One oscillation event on an open map: the hero stands at (5,5) with the A-B loop armed; returns resolve_move's navigation update."""
    h = replace(hero, navigation=replace(hero.navigation, last_position=(6, 5), oscillation_count=3, position=(5, 5)))
    state = AuthoritativeState(entities={1: h}, tick=tick, seed=1)
    return MovementSystem.resolve_move(state, h, target)[1].navigation


def test_a_one_tile_jitter_of_the_target_continues_the_count():
    hero = _open_count(_hero(target=(9, 5)), count=1, best=3, anchor=(9, 5), last_tick=0)  # best 3: none of the jittered distances (3 to 6 from (5,5)) is below it, so none is progress
    for jitter in ((9, 6), (8, 5), (10, 6), (8, 4)):  # Chebyshev <= 1 from the anchor (9,5)
        nav = _event(hero, jitter, 5)
        assert nav.wayround_count_set == 2 and nav.wayround_anchor_set == (9, 5) and nav.wayround_last_tick_set == 5


def test_a_jump_of_two_or_more_tiles_opens_a_fresh_count():
    hero = _open_count(_hero(target=(9, 5)), count=2, best=4, anchor=(9, 5), last_tick=0)
    nav = _event(hero, (11, 5), 5)
    assert nav.wayround_count_set == 1 and nav.wayround_anchor_set == (11, 5) and nav.wayround_best_distance_set == 6


def test_a_gap_of_more_than_200_ticks_opens_a_fresh_count_and_exactly_200_continues():
    hero = _open_count(_hero(target=(9, 5)), count=1, best=4, anchor=(9, 5), last_tick=0)
    assert _event(hero, (9, 5), 200).wayround_count_set == 2
    nav = _event(hero, (9, 5), 201)
    assert nav.wayround_count_set == 1 and nav.wayround_anchor_set == (9, 5) and nav.wayround_last_tick_set == 201


def test_progress_rebaselines_the_count_and_keeps_the_anchor():
    hero = _open_count(_hero(target=(9, 5)), count=2, best=9, anchor=(9, 5), last_tick=0)
    nav = _event(hero, (9, 6), 5)  # distance 5 is below the best 9
    assert nav.wayround_count_set == 1 and nav.wayround_best_distance_set == 5 and nav.wayround_anchor_set == (9, 5)


def test_a_clear_then_a_reset_of_the_target_continues_the_count_through_the_patch():
    hero = _open_count(_hero(target=(9, 5)), count=1, best=4, anchor=(9, 5), last_tick=0)
    nav = _apply_nav(hero, NavigationUpdate(clear_target=True))
    hero = replace(hero, navigation=nav)
    nav = _apply_nav(hero, NavigationUpdate(target_set=(9, 6)))
    hero = replace(hero, navigation=nav)
    assert nav.target == (9, 6) and nav.wayround_count == 1
    assert _event(hero, (9, 6), 8).wayround_count_set == 2


def test_the_give_up_fires_after_two_way_rounds_across_a_one_tile_jitter():
    """The v7 trace defect: the task layer rewrites the target by one tile every few ticks, and the give-up must still fire on the third event."""
    hero = _hero(target=(9, 5))
    for tick, tgt in ((0, (9, 5)), (5, (9, 6)), (10, (9, 5))):
        nav_u = _event(hero, tgt, tick)
        if tick < 10:
            assert nav_u.wayround_count_set == (1 if tick == 0 else 2) and nav_u.wayround_clear is False
        else:
            assert nav_u.wayround_clear is True and nav_u.clear_target is True and nav_u.clear_path is True and nav_u.wayround_count_set is None
        nav = _apply_nav(hero, nav_u)
        hero = replace(hero, navigation=nav)
        hero = replace(hero, navigation=replace(hero.navigation, target=tgt if tick < 10 else hero.navigation.target))
    assert (hero.navigation.wayround_count, hero.navigation.wayround_anchor, hero.navigation.wayround_last_tick) == (0, None, None)


def test_the_anchor_fields_omit_when_none_and_show_in_the_canonical_form_and_fingerprint_only_while_a_count_is_open():
    from src.replay.fingerprint import StateFingerprinter
    closed = _hero(target=(9, 5))
    canon = closed.navigation.to_canonical_dict()
    assert "wayround_anchor" not in canon and "wayround_last_tick" not in canon and "wayround_count" not in canon
    def fp(h):
        return StateFingerprinter.get_fingerprint(_state(h))["state_hash"]

    opened = _open_count(closed, count=1, best=4, anchor=(9, 5), last_tick=7)
    canon = opened.navigation.to_canonical_dict()
    assert canon["wayround_anchor"] == (9, 5) and canon["wayround_last_tick"] == 7
    assert fp(opened) != fp(closed)  # an open count is in the fingerprint ...
    assert fp(opened) != fp(_open_count(closed, count=1, best=4, anchor=(9, 6), last_tick=7))  # ... with its anchor ...
    assert fp(opened) != fp(_open_count(closed, count=1, best=4, anchor=(9, 5), last_tick=8))  # ... and its tick
    assert fp(closed) == fp(replace(closed, navigation=replace(closed.navigation, wayround_anchor=None, wayround_last_tick=None)))  # a closed count adds nothing


def test_best_distance_is_none_exactly_when_the_count_is_zero_on_every_patch_path():
    """The invariant behind the canonical form (rpg-designer 2026-11-17): the pair is set together on a way-round and cleared together on a reset, a give-up and a new target."""
    def pair(nav):
        return nav.wayround_count, nav.wayround_best_distance

    def invariant(nav):
        return (nav.wayround_best_distance is None) == (nav.wayround_count == 0)

    hero = _hero(target=(9, 5))
    assert invariant(hero.navigation)
    paths = [
        NavigationUpdate(wayround_count_set=1, wayround_best_distance_set=4, wayround_anchor_set=(9, 5), wayround_last_tick_set=3),  # the first way-round: set together
        NavigationUpdate(wayround_count_set=2, wayround_best_distance_set=4, wayround_anchor_set=(9, 5), wayround_last_tick_set=8),
        NavigationUpdate(wayround_clear=True),  # the give-up
        NavigationUpdate(target_set=(2, 2)),  # a new target
        NavigationUpdate(target_clear=True),
        NavigationUpdate(clear_target=True),
        NavigationUpdate(target_set=(9, 5)),  # the same target re-issued
        NavigationUpdate(),  # nothing about navigation
    ]
    for start in (pair(hero.navigation), (2, 4)):
        for update in paths:
            h = replace(hero, navigation=replace(hero.navigation, wayround_count=start[0], wayround_best_distance=start[1] if start[0] else None,
                                                 wayround_anchor=(9, 5) if start[0] else None, wayround_last_tick=0 if start[0] else None))
            changes = {}
            NavigationPatch(entity_id=1, navigation=update).apply(h, changes)
            n = changes["navigation"]
            assert invariant(n), (start, update)
            assert (n.wayround_anchor is None) == (n.wayround_count == 0) and (n.wayround_last_tick is None) == (n.wayround_count == 0), (start, update)
    # and through resolve_move: the first way-round sets the pair together, the give-up clears it together
    h = _hero(target=(9, 5), last_position=(6, 5), oscillation_count=3)
    upd = MovementSystem.resolve_move(_state(h), h, (9, 5))[1]
    assert (upd.navigation.wayround_count_set is None) == (upd.navigation.wayround_best_distance_set is None)
    boxed = _state(h, _wall(10, 5, 4), _wall(11, 5, 6), _wall(12, 4, 5))
    upd = MovementSystem.resolve_move(boxed, h, (9, 5))[1]
    assert upd.navigation.wayround_clear is True and upd.navigation.wayround_count_set is None and upd.navigation.wayround_best_distance_set is None


@pytest.mark.usefixtures("remove_restored_run_dirs")
def test_an_open_count_round_trips_through_the_real_checkpoint_writer_and_continues(tmp_path):
    """F1 (rpg-designer review): save an open count (count 1, best 4, anchor (9,5), last tick 7) through the real checkpoint writer and load it back. The anchor stays a TUPLE (a list would
    change the fingerprint and the Chebyshev read), the canonical hash and the fingerprint equal the originals, and the next oscillation event continues the count (count 2)."""
    from types import SimpleNamespace
    from src.engine.scenario_checkpoint import ScenarioCheckpointer
    from src.replay.fingerprint import StateFingerprinter
    from src.engine.checkpoint import CanonicalStateHasher
    from src.scenarios.schema import SimulationScenarioDefinition

    spec = SimulationScenarioDefinition(id="f1_roundtrip", world_composition="frontier_living_world", perspective="hero_guild_perspective")
    hero = _open_count(_hero(target=(9, 5)), count=1, best=4, anchor=(9, 5), last_tick=7)
    state = _state(hero)
    svc = SimpleNamespace(_kernel=SimpleNamespace(state=state), tick=0, _spec=spec)  # exactly what save() reads: kernel.state, tick, spec id
    path = tmp_path / "ckpt.bin"
    ScenarioCheckpointer.save(svc, path)
    restored = ScenarioCheckpointer.restore(path, spec)
    try:
        r_state = restored._kernel.state
        nav = r_state.entities[1].navigation
        assert nav.wayround_anchor == (9, 5) and isinstance(nav.wayround_anchor, tuple)
        assert (nav.wayround_count, nav.wayround_best_distance, nav.wayround_last_tick) == (1, 4, 7)
        assert CanonicalStateHasher.get_hash(r_state) == CanonicalStateHasher.get_hash(state)
        assert StateFingerprinter.get_fingerprint(r_state)["state_hash"] == StateFingerprinter.get_fingerprint(state)["state_hash"]
        assert _event(r_state.entities[1], (9, 6), 12).wayround_count_set == 2  # the restored count continues across a one-tile jitter
    finally:
        restored.abort()


def test_the_give_up_writes_wayround_give_up_replaces_the_old_code_and_files_no_blocker():
    """2.214: the give-up is not a legal step; it writes its own typed code, which replaces any older one, and infer_blockers files nothing from it."""
    from src.core.enums import ReasonCode
    from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem

    hero = _hero(target=(9, 5), last_position=(6, 5), oscillation_count=3, last_failure_reason="STUCK")
    hero = replace(hero, navigation=replace(hero.navigation, wayround_count=2, wayround_best_distance=4, wayround_anchor=(9, 5), wayround_last_tick=0))
    walls = [_wall(10, 5, 4), _wall(11, 5, 6), _wall(12, 4, 5)]
    upd = MovementSystem.resolve_move(_state(hero, *walls), hero, (9, 5))[1]
    assert upd.navigation.wayround_clear is True and upd.navigation.failure_reason == ReasonCode.WAYROUND_GIVE_UP
    after = _apply_nav(hero, upd.navigation)
    assert after.last_failure_reason == ReasonCode.WAYROUND_GIVE_UP  # replaces the stale STUCK
    filed = StrategicIntelligenceSystem.infer_blockers(replace(hero, navigation=after), "ENTITY_MOVE", {"target_position": (9.0, 5.0)}, navigation_failure=after.last_failure_reason)
    assert not filed.blockers_add_or_update


def test_no_failed_movement_step_writes_legal():
    """F1 acceptance line: every failing branch of resolve_move reports a typed failure, never the legality verdict LEGAL. The scenarios cover: a step into a wall (legality failure),
    a replan at wait_count 5, the oscillation give-up, and an oscillation way-round (a success, which carries no code)."""
    from src.core.enums import ReasonCode

    ring = [_wall(10 + i, 5 + dx, 5 + dy) for i, (dx, dy) in enumerate((a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if (a, b) != (0, 0))]
    scenarios = [
        (_hero(target=(9, 5)), ring),                                                        # boxed in: the step is illegal
        (_hero(target=(9, 5), wait_count=5), ring),                                          # boxed in at wait_count 5: the replan branch
        (_hero(target=(9, 5), last_position=(6, 5), oscillation_count=3), [_wall(10, 5, 4), _wall(11, 5, 6), _wall(12, 4, 5)]),  # the give-up
        (_hero(target=(9, 5), last_position=(6, 5), oscillation_count=3), []),               # a way-round exists: a success
        (_hero(target=(9, 5)), []),                                                          # a free step: a success
    ]
    failed = 0
    for hero, walls in scenarios:
        upd = MovementSystem.resolve_move(_state(hero, *walls), hero, (9, 5))[1]
        reason = upd.navigation.failure_reason if upd.navigation is not None else None
        if upd.new_position is None:
            failed += 1
            assert reason is not None and reason != ReasonCode.LEGAL, (hero.navigation, reason)
        else:
            assert reason is None
    assert failed >= 3  # not vacuous: the wall, the wait_count replan and the give-up all failed
