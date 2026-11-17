"""TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK: an oscillation replan runs the rung ladder before it gives up, and the stored target is cleared
through the apply path (``clear_target`` was never applied; TCK-20261114-NAVIGATION-CLEAR-TARGET-FLAG-IS-NEVER-APPLIED)."""
from dataclasses import replace

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
    hero = replace(hero, navigation=replace(hero.navigation, wayround_count=2, wayround_best_distance=2))
    upd = MovementSystem.resolve_move(_state(hero), hero, (9, 5))[1]  # distance 4 is not below 2: no progress -> the third event gives up
    assert upd.navigation.wayround_clear is True and upd.navigation.clear_target is True
    hero = replace(hero, navigation=replace(hero.navigation, wayround_best_distance=9))
    upd = MovementSystem.resolve_move(_state(hero), hero, (9, 5))[1]  # distance 4 is below the best 9: progress -> count 1, step taken
    assert upd.navigation.wayround_count_set == 1 and upd.navigation.wayround_best_distance_set == 4 and upd.new_position is not None


def test_a_new_target_or_a_cleared_target_resets_the_count_in_the_patch():
    hero = _hero(target=(9, 5))
    hero = replace(hero, navigation=replace(hero.navigation, wayround_count=2, wayround_best_distance=4))
    for update in (NavigationUpdate(target_set=(2, 2)), NavigationUpdate(target_clear=True), NavigationUpdate(clear_target=True)):
        changes = {}
        NavigationPatch(entity_id=1, navigation=update).apply(hero, changes)
        assert changes["navigation"].wayround_count == 0 and changes["navigation"].wayround_best_distance is None
    changes = {}
    NavigationPatch(entity_id=1, navigation=NavigationUpdate(target_set=(9, 5))).apply(hero, changes)  # the SAME target re-issued keeps the count
    assert changes["navigation"].wayround_count == 2 and changes["navigation"].wayround_best_distance == 4


def test_best_distance_is_none_exactly_when_the_count_is_zero_on_every_patch_path():
    """The invariant behind the canonical form (rpg-designer 2026-11-17): the pair is set together on a way-round and cleared together on a reset, a give-up and a new target."""
    def pair(nav):
        return nav.wayround_count, nav.wayround_best_distance

    def invariant(nav):
        return (nav.wayround_best_distance is None) == (nav.wayround_count == 0)

    hero = _hero(target=(9, 5))
    assert invariant(hero.navigation)
    paths = [
        NavigationUpdate(wayround_count_set=1, wayround_best_distance_set=4),  # the first way-round: set together
        NavigationUpdate(wayround_count_set=2, wayround_best_distance_set=4),
        NavigationUpdate(wayround_clear=True),  # the give-up
        NavigationUpdate(target_set=(2, 2)),  # a new target
        NavigationUpdate(target_clear=True),
        NavigationUpdate(clear_target=True),
        NavigationUpdate(target_set=(9, 5)),  # the same target re-issued
        NavigationUpdate(),  # nothing about navigation
    ]
    for start in (pair(hero.navigation), (2, 4)):
        for update in paths:
            h = replace(hero, navigation=replace(hero.navigation, wayround_count=start[0], wayround_best_distance=start[1] if start[0] else None))
            changes = {}
            NavigationPatch(entity_id=1, navigation=update).apply(h, changes)
            assert invariant(changes["navigation"]), (start, update)
    # and through resolve_move: the first way-round sets the pair together, the give-up clears it together
    h = _hero(target=(9, 5), last_position=(6, 5), oscillation_count=3)
    upd = MovementSystem.resolve_move(_state(h), h, (9, 5))[1]
    assert (upd.navigation.wayround_count_set is None) == (upd.navigation.wayround_best_distance_set is None)
    boxed = _state(h, _wall(10, 5, 4), _wall(11, 5, 6), _wall(12, 4, 5))
    upd = MovementSystem.resolve_move(boxed, h, (9, 5))[1]
    assert upd.navigation.wayround_clear is True and upd.navigation.wayround_count_set is None and upd.navigation.wayround_best_distance_set is None
