"""A combat objective's navigation target tracks the target entity's LIVE position, through the real kernel
(TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES, AC1).

This is a regression guard, not a fix: on the current tree a combat objective is `defeat_enemy`, engagement is
the hostile branch, and the property already holds. Nothing else prevents it from regressing back to the
"point frozen at goal-win time" shape the ticket was filed for, and a unit test of the resolver cannot see
that, because the live path never calls the resolver for a combat objective.

World: a two-body arena built inside this module from two real compiled bodies of ``frontier_extended`` (seed 42), by ``replace(state, entities={12: first, 44: second})`` and nothing else removed or patched
(no species or faction is changed on a body): e12, a human of the merchant_league (hp 80), and e44, an undead of undead_remnants (hp 130), eight tiles apart on a clear row of plain tiles, (10, 10) and (18, 10), by day.
They are hostile by faction verdict, both PERCEIVE the other at t0 (asserted both ways, score 0.2268, a medium-visibility body at 8 tiles), and e12 is the WITHDRAWING side (the combat engagement posture toward e44 is
AVOID: CombatEngagementDecisionService.evaluate -> CombatPostureSelector.select), as the goblin of the original pair was. Both bodies move, so the target moves after the objective is created. Every need the brain reads is
set to zero at t0 so a need does not send either off the pursuit.

Why not the original pair: ``mechanic_scenario_combat_judgement_withdrawal`` (goblin_scout and orc_warchief) no longer works under PERC-02a (the shared world is unchanged). A goblin is a small body (visibility low) and a
still low-visibility body is never perceived short of touch (best score .132 < .2), so the second never perceived the goblin and never held a navigation target.

What is sampled: only PURSUIT ticks (``_is_pursuit_tick``, the plain pursuit branch of the tactical pass). A retreat, avoid, wander, kite, bracket, intercept or cover target is a point the body navigates to, not the
opponent's position, so it is counted in ``skipped`` (by reason) and not sampled. Measured on this arena over 60 ticks: pursuit ticks e12 = 31, e44 = 9 (e44 closes in for 9 ticks, then intercepts for the rest); skipped
e12 {no_target 19, AVOID_HOSTILE 2, ENTITY_ACT 8}, e44 {no_target 27, INTERCEPTING 24}; no deaths. ``N_FLOOR`` is the owner's number.

Deliberately NOT asserted: that either entity attacks. The navigation targets sampled stay within MAX_LAG of the opponent's live position, which is consistent with the documented single-axis diagonal pursuit limit
(docs/engine/known_limitations.md section 1.1), not with a frozen target point.
"""
from collections import Counter
from dataclasses import replace


from src.config.profiles import PROD_SMALL
from src.core.calendar import is_night
from src.core.movement_modes import MovementMode
from src.core.region_resolution import is_inside_world
from src.engine.appraisal import perceives
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.tile_distance import chebyshev_tile_distance
from src.platform.rng import DeterministicRNG
from tests.helpers.clock import DAY_WORLD_TIME
from tests.helpers.scenario import compile_world, empty_inventories

WORLD_ID = "frontier_extended"
SEED = 42
TICKS = 60
FIRST, SECOND = 12, 44                   # compiled bodies of frontier_extended s42: a human of the merchant_league (hp80, the WITHDRAWING side: posture AVOID toward the undead) and an undead of undead_remnants (hp130, ENGAGE)
DISTANCE = 8  # tiles apart in a row (Chebyshev = Manhattan); the owner-approved scenario distance (#715 6974976880)
FIRST_AT, SECOND_AT = (10.0, 10.0), (10.0 + DISTANCE, 10.0)  # a clear row of plain tiles (asserted in _arena: in bounds, passable, no building, nobody on it)
N_FLOOR = 9  # pursuit ticks per side: owner chose 9 (#715 6974976880), the measured minimum, below the designer's pre-data floor 10; trips on any lawful change to the closing phase
# Navigation steps one axis at a time, so a live target is allowed to lag the opponent by one step.
MAX_LAG = 2


def _arena():
    """The compiled frontier_extended with ONLY the two pair bodies left (``replace(state, entities={...})``), relocated DISTANCE tiles apart on a clear row, needs zeroed, by day."""
    state = compile_world(WORLD_ID, SEED)
    first, second = state.entities[FIRST], state.entities[SECOND]
    assert first.navigation.lodged_in is None and second.navigation.lodged_in is None
    first = replace(first, navigation=replace(first.navigation, position=FIRST_AT, target=None, path=[], last_moved_tick=None))
    second = replace(second, navigation=replace(second.navigation, position=SECOND_AT, target=None, path=[], last_moved_tick=None))
    # Setup only, at t0 (nothing is forced per tick): both bodies start with every need the brain reads at zero, so a need does not send either one off the pursuit (hunger, sleep_debt, rest_pressure).
    first, second = (replace(e, biological=replace(e.biological, hunger=0.0, sleep_debt=0.0, rest_pressure=0.0)) for e in (first, second))
    state = empty_inventories(replace(state, entities={FIRST: first, SECOND: second}))  # the scenario is about the navigation target, not about what the two bodies carry
    # A compiled world starts at world_time 0, which is night. By night neither body perceives the other (PERC-02a), so neither would hold a target; the scenario runs by day (owner #715 6971973729).
    state = replace(state, world_time=DAY_WORLD_TIME)
    line = [(x, 10) for x in range(10, 10 + DISTANCE + 1)]  # the straight line between the two bodies, ends included
    building_tiles = {(int(b.position[0]), int(b.position[1])) for b in state.buildings.values()}
    for tile in line:
        assert is_inside_world(state, (float(tile[0]), float(tile[1]))), f"{tile} is outside the world"
        assert state.terrain.get(tile) not in (None, "WALL"), f"{tile} is not passable terrain: {state.terrain.get(tile)!r}"
        assert tile not in building_tiles, f"{tile} is inside a building"
    for e in state.entities.values():
        assert (int(e.navigation.position[0]), int(e.navigation.position[1])) in (line[0], line[-1]) and e.combat.alive, f"entity {e.id} is not at an end of the line, alive"
    assert set(state.entities) == {FIRST, SECOND}
    first, second = state.entities[FIRST], state.entities[SECOND]
    night = is_night(state.world_time)
    assert not night and chebyshev_tile_distance(first.navigation.position, second.navigation.position) == DISTANCE
    assert perceives(first, second, night=night, tick=state.tick) and perceives(second, first, night=night, tick=state.tick), "the pair must perceive each other at t0"
    return state


def _is_pursuit_tick(me, other_id):
    """True when `me`'s task is the plain pursuit step of the tactical pass (tactical.py:770: ENTITY_MOVE, navigation.movement_mode_set PURSUE, payload target_id + target_position + stale_ticks and NO reason).
    No single field marks that branch alone: PURSUE is also set by PURSUIT_BLOCKED_KITE (tactical.py:651, which carries a reason) and target_id by KITING, BRACKETING, INTERCEPTING and SEEK_COVER (all carry a reason
    and navigate to a tactical point), so the test is the mode plus the absent reason."""
    payload = me.task.payload
    return me.task.work_kind == "ENTITY_MOVE" and me.navigation.movement_mode is MovementMode.PURSUE and payload.get("target_id") == other_id and "reason" not in payload


def _run():
    state = _arena()
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(SEED),
                    flags={"no_frame_pacing": True, "no_replay": True}, executor=LocalSequentialExecutor())
    samples = []  # (tick, entity id, nav target, opponent position): pursuit ticks only
    targets_seen = {FIRST: set(), SECOND: set()}
    skipped = {FIRST: Counter(), SECOND: Counter()}
    try:
        for tick in range(TICKS):
            kernel.tick_once()
            entities = kernel._state.entities
            for eid, other in ((FIRST, SECOND), (SECOND, FIRST)):
                me, foe = entities[eid], entities[other]
                if not (me.combat.alive and foe.combat.alive):
                    continue
                if me.navigation.target is None:
                    skipped[eid]["no_target"] += 1
                    continue
                if not _is_pursuit_tick(me, other):  # not a pursuit tick: a retreat, avoid, wander, kite, bracket, intercept or cover target is not a combat objective's target
                    skipped[eid][str(me.task.payload.get("reason") or me.task.payload.get("action") or me.task.work_kind)] += 1
                    continue
                targets_seen[eid].add(me.navigation.target)
                samples.append((tick, eid, me.navigation.target, foe.navigation.position))
    finally:
        kernel.shutdown()
    return samples, targets_seen, skipped


def _no_hard_law_violation(caplog):
    assert not [r.getMessage() for r in caplog.records if "Hard Law Violation" in r.getMessage()]
    assert not [r.getMessage() for r in caplog.records if r.levelno >= 40 and not r.name.startswith("src.observability.alerts")]  # no ERROR from the kernel (the watchdog's alert sink is a timing record)


def test_navigation_target_tracks_the_opponents_live_position(caplog):
    samples, targets_seen, skipped = _run()

    assert samples, "both entities must pursue (non-vacuous): no navigation target was ever set"
    for tick, eid, target, foe_pos in samples:
        lag = abs(target[0] - foe_pos[0]) + abs(target[1] - foe_pos[1])
        assert lag <= MAX_LAG, f"tick {tick}: entity {eid} navigates to {target}, {lag} tiles from the live target {foe_pos}"
    for eid in (FIRST, SECOND):
        n = sum(1 for s in samples if s[1] == eid)
        assert n >= N_FLOOR, f"entity {eid}: {n} pursuit ticks (skipped: {dict(skipped[eid])})"
    _no_hard_law_violation(caplog)


def test_navigation_target_is_not_frozen_while_the_opponent_moves(caplog):
    _, targets_seen, _ = _run()

    assert all(targets_seen[eid] for eid in (FIRST, SECOND))
    assert any(len(seen) >= 2 for seen in targets_seen.values()), "targets never changed: a frozen point"
    _no_hard_law_violation(caplog)


def test_scenario_is_deterministic():
    assert _run() == _run()
