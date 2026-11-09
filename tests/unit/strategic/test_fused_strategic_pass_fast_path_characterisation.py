"""Characterisation of fused_strategic_pass's off-cadence fast path, and a fast-against-slow differential.

TCK-20261109-FUSED-STRATEGIC-PASS-FAST-PATH-IS-PINNED-BRANCH-BY-BRANCH-AND-AGAINST-THE-SLOW-PATH.

The fast path is the block taken when neither concern nor intent evaluation is due for the entity, no strategic
update is pending for it, and it has no blockers or leads. Twelve test files call the function; none targets that
block. These tests pin today's behaviour branch by branch (Feathers characterisation: the expected values are what
the code does now, not what a document says), and run the same entity state through both paths.

Reading the tests:
* "off cadence" = both cadences so long that tick 5 is not due for entity 1, so the fast path is eligible.
* "due" = the concern cadence is 1, so the tick is due and the slow path runs. The intent cadence stays long so
  the intent evaluation (which can drop a project) does not run: the comparison is about the navigation
  redirection, which both paths contain.
* Tests reach every branch through hand-built state only. No world compiler, no private helper, no mock.

The differential's known disagreements are listed in KNOWN_DISAGREEMENTS with their reason and owning ticket. A
disagreement that is not in that table fails the differential.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.inventory import ItemStack
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState
from src.core.strategic import (
    BlockerKind, BlockerState, LeadKind, LeadState, ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectKind,
    ProjectState, ProjectStatus,
)
from src.core.updates import EntityUpdate, InventoryUpdate, NavigationUpdate, StateUpdate
from src.engine.cadence import SystemCadence
from src.systems.strategic import StrategicIntelligenceSystem

pytestmark = [pytest.mark.domain("strategic_cognition"), pytest.mark.level("unit")]

TOWN = (50.0, 50.0)
OFF_CADENCE = SystemCadence(strategic_intelligence=1000, concern_evaluation=1000)
DUE_CADENCE = SystemCadence(strategic_intelligence=1000, concern_evaluation=1)

# The sentinel row (5) is owned by rpg-planner's filing; it is on main once the owner merges #851.
TOWN_CENTER_SENTINEL_TICKET = "TCK-20261109-STATE-TOWN-CENTER-DEFAULT-IS-A-SENTINEL-A-RETREAT-CAN-AIM-AT"
DEFECT_A = "TCK-20261109-THE-FAST-STRATEGIC-PATH-SENDS-AN-ENTITY-TARGET-PURSUER-HOME-WITH-ITS-ITEMS"
CLEAR_TARGET = "TCK-20261101-CLEAR-TARGET-IS-NEVER-APPLIED"


# ---------------------------------------------------------------------------------------------------- builders
def _objective(**kw) -> ObjectiveState:
    kind = kw.pop("kind", ObjectiveKind.REACH_LOCATION)
    return ObjectiveState(id="o1", kind=kind, status=ObjectiveStatus.ACTIVE, **kw)


def _entity(*, pos=(10.0, 10.0), loaded=True, target=None, objective=None, lodged_in=None, task_action=None,
            blockers=None, leads=None, active=True, alive=True):
    b = V2EntityBuilder(1).kind("worker").location(*pos)
    if loaded:
        b = b.inventory(items=[ItemStack(item_id="wood", quantity=1)])
    if target is not None:
        b = b.navigation(target=target)
    if objective is not None:
        project = ProjectState(id="p1", kind=ProjectKind.TRAVEL, status=ProjectStatus.ACTIVE,
                               objectives=[objective], active_objective_id=objective.id)
        b = b.strategic(projects={"p1": project}, current_project_id="p1")
    if blockers or leads:
        b = b.strategic(blockers=blockers or {}, leads=leads or {})
    if task_action:
        b = b.task(work_kind="REST", payload={"action": task_action})
    if not active:
        b = b.lifecycle(active=False)
    if not alive:
        b = b.combat(alive=False)
    entity = b.build()
    if lodged_in is not None:
        entity = replace(entity, navigation=replace(entity.navigation, lodged_in=lodged_in))
    return entity


def _pass(entity, cadence, earlier=None, town_center=TOWN, town_tiles=None):
    """Run the pass on tick 5 with entity 1 (the subject) and entity 2 (a live pursuit target at (30, 30))."""
    target_entity = V2EntityBuilder(2).kind("worker").location(30.0, 30.0).build()
    state = AuthoritativeState(tick=5, seed=1, entities={1: entity, 2: target_entity}, town_center=town_center,
                               town_tiles=town_tiles or set())
    update = StateUpdate(entity_updates={1: earlier} if earlier is not None else {})
    return StrategicIntelligenceSystem.fused_strategic_pass(state, update, cadence=cadence), update


def _outcome(result):
    """What the pass decided for entity 1's walk: (target, movement mode, interaction reset). None = no walk decision."""
    upd = result.entity_updates.get(1)
    nav = upd.navigation if upd is not None else None
    reset = bool(upd is not None and upd.interaction is not None and upd.interaction.reset)
    if nav is None and not reset:
        return None
    return (nav.target_set if nav else None, nav.movement_mode_set if nav else None, reset)


def _run(entity, cadence, **kw):
    return _outcome(_pass(entity, cadence, **kw)[0])


REGROUP_HOME = (TOWN, MovementMode.REGROUP, True)


# ------------------------------------------------------------------- row 1: regroup home with items (fast :391-402)
def test_row1_position_objective_with_the_walk_already_set_does_not_regroup_off_cadence():
    entity = _entity(objective=_objective(target_position=(20.0, 20.0)), target=(20.0, 20.0))
    assert _run(entity, OFF_CADENCE) is None


def test_row1_entity_objective_does_not_regroup_on_cadence():
    # An entity-typed objective owns the direction on the slow path: no point is set and no regroup is written.
    entity = _entity(objective=_objective(target_entity_id=2))
    assert _run(entity, DUE_CADENCE) is None


def test_row1_loaded_entity_with_no_objective_regroups_home_off_cadence():
    assert _run(_entity(), OFF_CADENCE) == REGROUP_HOME


# -------------------------------------------------------------------------- row 2: proj_resolved early-out (:389-390)
def _completed_projects(result):
    upd = result.entity_updates.get(1)
    strat = upd.strategic if upd is not None else None
    return [p.id for p in (strat.projects_add_or_update if strat else []) if p.status == ProjectStatus.COMPLETED]


def test_row2_craft_objective_whose_item_is_held_falls_through_to_the_slow_path_and_completes_the_project():
    # kind "craft"/"collect" are plain strings on the objective (not ObjectiveKind members); the guard reads them as such.
    entity = _entity(objective=_objective(kind="craft", target="wood"))
    assert _completed_projects(_pass(entity, OFF_CADENCE)[0]) == ["p1"]


def test_row2_the_same_objective_without_the_item_is_left_alone_off_cadence():
    entity = _entity(objective=_objective(kind="craft", target="herb"))
    assert _completed_projects(_pass(entity, OFF_CADENCE)[0]) == []


def test_row2_an_item_added_by_an_earlier_phase_this_tick_counts_as_held():
    entity = _entity(loaded=False, objective=_objective(kind="collect", target="herb"))
    earlier = EntityUpdate(entity_id=1, inventory=InventoryUpdate(items_add=[ItemStack(item_id="herb", quantity=1)]))
    assert _completed_projects(_pass(entity, OFF_CADENCE, earlier=earlier)[0]) == ["p1"]


# ------------------------------------------------------------------------------- row 3: nav_changed (:392-394)
def test_row3_objective_position_differing_from_the_nav_target_sets_the_walk_target_off_cadence():
    entity = _entity(objective=_objective(target_position=(20.0, 20.0)), target=(5.0, 5.0))
    assert _run(entity, OFF_CADENCE) == ((20.0, 20.0), None, False)


# ------------------------------------------------------------------------------- row 4: lodged_stayer suppression
def test_row4_lodged_stayer_gets_no_regroup_on_either_path():
    entity = _entity(lodged_in=7, task_action="SLEEP")
    assert _run(entity, OFF_CADENCE) is None
    assert _run(entity, DUE_CADENCE) is None


def test_row4_lodged_entity_whose_task_is_not_a_rest_is_not_a_stayer_and_regroups():
    entity = _entity(lodged_in=7)
    assert _run(entity, OFF_CADENCE) == REGROUP_HOME
    assert _run(entity, DUE_CADENCE) == REGROUP_HOME


# ------------------------------------------- row 5: position != (0, 0) guard and the state.town_center fallback
def test_row5_entity_at_the_origin_is_never_regrouped():
    entity = _entity(pos=(0.0, 0.0))
    assert _run(entity, OFF_CADENCE) is None
    assert _run(entity, DUE_CADENCE) is None


def test_row5_with_no_town_tile_the_regroup_target_is_state_town_center():
    assert _run(_entity(), OFF_CADENCE) == REGROUP_HOME
    assert _run(_entity(), DUE_CADENCE) == REGROUP_HOME


def test_row5_nearest_town_tile_wins_over_town_center():
    assert _run(_entity(), OFF_CADENCE, town_tiles={(12, 10), (40, 40)})[0] == (12.0, 10.0)


def test_row5_current_behaviour_the_default_town_center_sentinel_is_a_valid_regroup_target():
    # TOWN_CENTER_SENTINEL_TICKET: state.town_center defaults to (0.0, 0.0), a non-empty tuple, so a world with no town
    # tile and no set centre sends a loaded entity to the map origin. Pinned as it is; that ticket decides the change.
    assert TOWN_CENTER_SENTINEL_TICKET
    result = _run(_entity(), OFF_CADENCE, town_center=(0.0, 0.0))
    assert result == ((0.0, 0.0), MovementMode.REGROUP, True)


# --------------------------------------------------- row 6: fast path overwrites an earlier phase's target_set
def test_row6_current_behaviour_fast_path_overwrites_an_earlier_phase_target_set():
    earlier = EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(30.0, 30.0)))
    assert _run(_entity(), OFF_CADENCE, earlier=earlier) == REGROUP_HOME


def test_row6_slow_path_keeps_an_earlier_phase_target_set():
    earlier = EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(30.0, 30.0)))
    assert _run(_entity(), DUE_CADENCE, earlier=earlier) == ((30.0, 30.0), None, False)


# ------------------------------- row 7: material-blocker lead redirection (slow path only) and the malformed row
def _material_blocker_entity(detail):
    return _entity(
        loaded=False,
        blockers={"b1": BlockerState(id="b1", kind=BlockerKind.MATERIAL, subject="iron_ore")},
        leads={"l1": LeadState(id="l1", kind=LeadKind.LOCATION, subject="iron_ore", detail=detail)},
    )


def test_row7_material_blocker_with_a_location_lead_redirects_to_the_lead_and_resets_the_interaction():
    assert _run(_material_blocker_entity("40.0,41.0"), OFF_CADENCE) == ((40.0, 41.0), None, True)


def test_row7_malformed_lead_detail_redirects_nowhere_and_does_not_raise():
    # Behaviour only: nothing is asserted about logging (the bare excepts become narrow, logging excepts under B).
    assert _run(_material_blocker_entity("north of here"), OFF_CADENCE) is None


# ----------------------------------------------------------------------------------- inactive and dead skip
# Pins the pass-level behaviour. The in-function early exit is shadowed: StrategicWorkQueue.build already drops inactive
# and dead entities before the loop, so removing the in-function guard alone changes nothing observable (a perturbation
# check showed this row stays green); only a change that lets such an entity into the queue would turn it red.
@pytest.mark.parametrize("kwargs", [{"active": False}, {"alive": False}], ids=["inactive", "dead"])
@pytest.mark.parametrize("cadence", [OFF_CADENCE, DUE_CADENCE], ids=["off", "due"])
def test_inactive_and_dead_entities_are_skipped(kwargs, cadence):
    result, update = _pass(_entity(**kwargs), cadence)
    assert result is update


# ============================================================================================ the differential
# Each row: the same entity state through the off-cadence (fast) path and the due (slow) path; the walk decision must match.
# A row that is meant to differ is listed here, with its reason and its owning ticket. Anything else must be equal.
KNOWN_DISAGREEMENTS = {
    "entity_objective_loaded_entity": ("strict_xfail", DEFECT_A,
                                       "fast path sends a loaded entity with an entity-typed objective home; slow path leaves it on the pursuit"),
    "earlier_phase_target_set": ("pinned_difference", CLEAR_TARGET,
                                 "fast path overwrites an earlier phase's target_set, slow path keeps it; nobody has ruled it a defect"),
}

_DIFFERENTIAL_ROWS = {
    "position_objective_walk_set": lambda: dict(entity=_entity(objective=_objective(target_position=(20.0, 20.0)), target=(20.0, 20.0))),
    "position_objective_walk_differs": lambda: dict(entity=_entity(objective=_objective(target_position=(20.0, 20.0)), target=(5.0, 5.0))),
    "entity_objective_loaded_entity": lambda: dict(entity=_entity(objective=_objective(target_entity_id=2))),
    "craft_item_held": lambda: dict(entity=_entity(objective=_objective(kind="craft", target="wood"))),
    "craft_item_missing": lambda: dict(entity=_entity(objective=_objective(kind="craft", target="herb"))),
    "lodged_stayer": lambda: dict(entity=_entity(lodged_in=7, task_action="SLEEP")),
    "lodged_non_stayer": lambda: dict(entity=_entity(lodged_in=7)),
    "origin_guard": lambda: dict(entity=_entity(pos=(0.0, 0.0))),
    "town_center_fallback": lambda: dict(entity=_entity()),
    "nearest_town_tile": lambda: dict(entity=_entity(), town_tiles={(12, 10), (40, 40)}),
    "town_center_sentinel": lambda: dict(entity=_entity(), town_center=(0.0, 0.0)),
    "earlier_phase_target_set": lambda: dict(entity=_entity(),
                                              earlier=EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(30.0, 30.0)))),
    "material_blocker_lead": lambda: dict(entity=_material_blocker_entity("40.0,41.0")),
}


def _differential_params():
    for row, build in _DIFFERENTIAL_ROWS.items():
        marks = []
        if KNOWN_DISAGREEMENTS.get(row, ("",))[0] == "strict_xfail":
            marks.append(pytest.mark.xfail(strict=True, reason=KNOWN_DISAGREEMENTS[row][1]))
        yield pytest.param(row, build, id=row, marks=marks)


@pytest.mark.parametrize("row, build", list(_differential_params()))
def test_fast_and_slow_paths_decide_the_same_walk(row, build):
    kw = build()
    entity = kw.pop("entity")
    fast = _run(entity, OFF_CADENCE, **kw)
    slow = _run(entity, DUE_CADENCE, **kw)
    if KNOWN_DISAGREEMENTS.get(row, ("",))[0] == "pinned_difference":
        # Current behaviour: pinned as different. A change in either direction fails here and is a decision, not a drift.
        assert fast != slow
        return
    assert fast == slow


def test_the_known_disagreement_table_holds_exactly_rows_1_and_6():
    assert set(KNOWN_DISAGREEMENTS) == {"entity_objective_loaded_entity", "earlier_phase_target_set"}
    assert set(KNOWN_DISAGREEMENTS) <= set(_DIFFERENTIAL_ROWS)
