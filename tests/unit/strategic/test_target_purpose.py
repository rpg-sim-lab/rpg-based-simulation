"""The #996 rework, step a1 (design docs/plans/systemic_world/experience_memory_design.md sections 2.1 and 4): the purpose of a target and its gate flag.

`purpose_of` is a pure read; the navigation patch stores `target_purpose` and `target_gated` ONLY with the target it keeps; both are canonical, hashed and checkpoint-ruled. Each rule has a failing control."""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.giveup_records import GiveUpRecord
from src.core.movement_modes import MovementMode
from src.core.navigation_purpose import NO_PROJECT_KIND, TargetPurpose, purpose_of, stored_purpose, ungated_purpose
from src.core.state import AuthoritativeState
from src.core.strategic import ProjectState
from src.core.updates import EntityUpdate, NavigationUpdate, StrategicUpdate
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.checkpoint_fields import FIELD_RULES
from src.engine.patches import NavigationPatch

WANDER_NONE = TargetPurpose(NO_PROJECT_KIND, "WANDER")
HUNGER_WANDER = TargetPurpose("hunger", "WANDER")


def _entity(project_kind=None, mode=MovementMode.WANDER, target=None, purpose=None, gated=False):
    e = V2EntityBuilder(1).kind("HERO").location(5.0, 5.0).navigation(target=target).build()
    nav = replace(e.navigation, movement_mode=mode, target_purpose=purpose, target_gated=gated)
    strat = e.strategic
    if project_kind is not None:
        strat = replace(strat, projects={"p1": ProjectState(id="p1", kind=project_kind)}, current_project_id="p1")
    return replace(e, navigation=nav, strategic=strat)


def _applied(entity, upd):
    changes = {}
    NavigationPatch(entity_id=1, navigation=upd).apply(entity, changes)
    return changes["navigation"]


# --- purpose_of: a pure read ---------------------------------------------------------------------------------------------------------------------
def test_purpose_of_is_the_project_kind_value_and_the_stored_mode():
    assert purpose_of(_entity()) == WANDER_NONE
    assert purpose_of(_entity(project_kind="hunger")) == HUNGER_WANDER
    assert purpose_of(_entity(project_kind="hunger", mode=MovementMode.PURSUE)) == TargetPurpose("hunger", "PURSUE")


def test_the_writers_mode_wins_and_a_stored_hold_becomes_wander_when_the_writer_resets_it():
    e = _entity(mode=MovementMode.HOLD)
    assert purpose_of(e) == WANDER_NONE  # hold_reset_kwargs: a HOLD with no live action task is reset to WANDER by a walk decision
    assert purpose_of(e, None, MovementMode.RETREAT) == TargetPurpose(NO_PROJECT_KIND, "RETREAT")
    live = replace(e, task=replace(e.task, work_kind="ENTITY_ACT", payload={"x": 1}))
    assert purpose_of(live) == TargetPurpose(NO_PROJECT_KIND, "HOLD")  # a live action task keeps the HOLD, as the reset does


def test_the_staged_update_changes_the_project_the_purpose_names_and_nothing_is_written():
    e = _entity()
    staged = EntityUpdate(entity_id=1, strategic=StrategicUpdate(projects_add_or_update=[ProjectState(id="p2", kind="fatigue")], current_project_id_set="p2"))
    assert purpose_of(e, staged) == TargetPurpose("fatigue", "WANDER")
    ended = EntityUpdate(entity_id=1, strategic=StrategicUpdate(current_project_id_set=""))
    assert purpose_of(_entity(project_kind="hunger"), ended).project_kind == NO_PROJECT_KIND
    assert e.strategic.current_project_id is None and purpose_of(e) == WANDER_NONE  # the entity is untouched (frozen) and the call repeatable


def test_stored_and_ungated_helpers():
    assert stored_purpose(_entity()) is None and stored_purpose(_entity(purpose=HUNGER_WANDER)) == HUNGER_WANDER
    assert ungated_purpose(_entity(project_kind="hunger"), MovementMode.RETREAT) == TargetPurpose("hunger", "RETREAT")


# --- the patch: the pair is written only with the target the patch keeps -----------------------------------------------------------------------
def test_a_new_target_stores_its_purpose_and_gate_flag():
    nav = _applied(_entity(), NavigationUpdate(target_set=(30.0, 30.0), target_purpose_set=HUNGER_WANDER, target_gated_set=True))
    assert nav.target == (30.0, 30.0) and nav.target_purpose == HUNGER_WANDER and nav.target_gated is True


def test_a_new_target_with_no_purpose_stores_none_and_false_never_the_old_targets():
    e = _entity(target=(40.0, 40.0), purpose=HUNGER_WANDER, gated=True)
    nav = _applied(e, NavigationUpdate(target_set=(30.0, 30.0)))
    assert nav.target == (30.0, 30.0) and nav.target_purpose is None and nav.target_gated is False


def test_a_clear_takes_the_purpose_and_the_flag_with_the_target():
    e = _entity(target=(40.0, 40.0), purpose=HUNGER_WANDER, gated=True)
    nav = _applied(e, NavigationUpdate(target_clear=True))
    assert nav.target is None and nav.target_purpose is None and nav.target_gated is False


def test_a_re_emission_of_the_stored_target_keeps_the_stored_pair_unless_it_names_one():
    e = _entity(target=(40.0, 40.0), purpose=HUNGER_WANDER, gated=True)
    kept = _applied(e, NavigationUpdate(target_set=(40.0, 40.0)))
    assert kept.target_purpose == HUNGER_WANDER and kept.target_gated is True
    named = _applied(e, NavigationUpdate(target_set=(40.0, 40.0), target_purpose_set=WANDER_NONE, target_gated_set=False))
    assert named.target_purpose == WANDER_NONE and named.target_gated is False


def test_an_update_that_does_not_touch_the_target_leaves_the_pair_as_stored():
    e = _entity(target=(40.0, 40.0), purpose=HUNGER_WANDER, gated=True)
    nav = _applied(e, NavigationUpdate(path_set=[(6.0, 6.0)]))
    assert nav.target == (40.0, 40.0) and nav.target_purpose == HUNGER_WANDER and nav.target_gated is True


def test_a_dropped_gated_write_beside_a_stored_ungated_hold_leaves_the_flag_false_and_the_purpose_stored():
    """The give-up's anchor drops the update's target_set and keeps the stored own-tile hold: the dropped write's purpose and True flag must not land on the hold."""
    hold_purpose = TargetPurpose(NO_PROJECT_KIND, "RETREAT")
    e = _entity(target=(20.0, 20.0), purpose=hold_purpose, gated=False)
    upd = NavigationUpdate(giveup_record_add=GiveUpRecord((20, 20), 10), target_set=(20.0, 21.0), target_purpose_set=HUNGER_WANDER, target_gated_set=True)
    nav = _applied(e, upd)
    # the stored target sits on the anchor, so the rule clears it (and the set), taking the pair with it; a set far from the anchor would instead stand with its own pair
    assert nav.target is None and nav.target_purpose is None and nav.target_gated is False
    far_hold = _entity(target=(60.0, 60.0), purpose=hold_purpose, gated=False)
    nav2 = _applied(far_hold, NavigationUpdate(giveup_record_add=GiveUpRecord((20, 20), 10), target_set=(20.0, 21.0), target_purpose_set=HUNGER_WANDER, target_gated_set=True))
    assert nav2.target == (60.0, 60.0) and nav2.target_purpose == hold_purpose and nav2.target_gated is False  # failing control: the set was dropped, the stored pair is untouched


# --- merge: a later target brings its own purpose --------------------------------------------------------------------------------------------------
def test_a_later_target_set_brings_its_own_purpose_even_none_never_the_earlier_targets():
    first = NavigationUpdate(target_set=(1.0, 1.0), target_purpose_set=HUNGER_WANDER, target_gated_set=True)
    assert first.merge(NavigationUpdate(target_set=(2.0, 2.0))).target_purpose_set is None
    assert first.merge(NavigationUpdate(target_set=(2.0, 2.0), target_purpose_set=WANDER_NONE, target_gated_set=False)).target_purpose_set == WANDER_NONE
    assert first.merge(NavigationUpdate(path_set=[(1.0, 1.0)])).target_purpose_set == HUNGER_WANDER  # no new target: the earlier pair stands
    assert not NavigationUpdate(target_purpose_set=HUNGER_WANDER).is_noop() and not NavigationUpdate(target_gated_set=False).is_noop()


# --- canonical, hashed, checkpoint-ruled -----------------------------------------------------------------------------------------------------------
def _hash(**nav):
    e = V2EntityBuilder(1).kind("HERO").location(5.0, 5.0).build()
    return CanonicalStateHasher.get_hash(AuthoritativeState(entities={1: replace(e, navigation=replace(e.navigation, **nav))}, tick=3, seed=1))


def test_the_purpose_and_the_flag_are_canonical_omitted_at_default_and_hashed():
    plain = _entity()
    assert "target_purpose" not in plain.navigation.to_canonical_dict() and "target_gated" not in plain.navigation.to_canonical_dict()
    d = _entity(purpose=HUNGER_WANDER, gated=True).navigation.to_canonical_dict()
    assert d["target_purpose"] == {"project_kind": "hunger", "movement_mode": "WANDER"} and d["target_gated"] is True
    base = _hash()
    assert _hash(target_purpose=HUNGER_WANDER) != base and _hash(target_gated=True) != base
    assert _hash(target_purpose=TargetPurpose("hunger", "PURSUE")) != _hash(target_purpose=HUNGER_WANDER)  # an in-type change moves the hash


def test_an_older_checkpoint_loads_no_purpose_and_not_gated():
    rules = {r.field: r for r in FIELD_RULES}
    assert rules["target_purpose"].fill(None, None) is None and rules["target_purpose"].ruling
    assert rules["target_gated"].fill(None, None) is False and rules["target_gated"].ruling
