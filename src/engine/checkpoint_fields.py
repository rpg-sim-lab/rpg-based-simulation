# Compliance IDs: INFRA-215
"""The one post-unpickle step of a scenario restore: a field a checkpoint predates (F3, divergence 2.155; later rows join this table).

A scenario checkpoint is a pickle of the whole ``AuthoritativeState``; its header carries a schema fingerprint (``checkpoint_schema``) that is checked before the unpickle and accepts only an append named by a row here (``record`` + ``field``). Unpickling a slotted, frozen record written before a field
existed skips ``__post_init__`` and leaves the slot UNSET, so the first read raises a raw ``AttributeError`` mid-tick. This step runs once, right after the unpickle, over a small table
``FIELD_RULES`` (the single restore step: later rows, from any lane, are added here; keep the names and the ``FieldRule`` shape): each row names the records that carry the field, the field, and a rule.

THE RULE: fill only a pure function of the loaded state that a ruling defines; else a typed refusal. A missing field is FILLED only when its value is a pure function of the loaded state that a ruling already defines (``fill``). Otherwise the row has no ``fill`` and the
restore REFUSES with ``CheckpointFieldMissingError``, naming the field and the records. A checkpoint that carries every field is not touched, so a current-shape restore is unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Optional

from src.core.navigation_experience import NavigationExperienceMemory
from src.core.state import seeded_next_group_id

_UNSET = object()


class CheckpointFieldMissingError(ValueError):
    """A checkpoint predates a field whose value cannot be derived from the loaded state: the restore is refused (never a raw ``AttributeError`` mid-tick)."""


class GroupCounterBehindStoreError(ValueError):
    """A restored checkpoint's group id counter is not above every non-squad group id in its store (dissolved records included), so the next formation could reuse a taken id.
    Raised at restore, after the fill; never in ``__post_init__`` or ``replace``. A ValueError, so the restore route answers 400."""


@dataclass(frozen=True)
class FieldRule:
    """``records(state)`` yields ``(label, owner)`` where ``owner`` is the record that carries ``field``; ``fill(state, owner)`` is the value to set, or ``None`` for no rule (refuse)."""
    name: str
    records: Callable[[Any], Iterable[Any]]
    field: str
    fill: Optional[Callable[[Any, Any], Any]] = None
    ruling: str = ""
    record: str = ""  # qualname of the class that carries ``field``: the schema check accepts an appended field only where a row names its class


def _navigations(state: Any) -> Iterable[Any]:
    for e in (getattr(state, "entities", None) or {}).values():
        yield (f"entity {e.id}", e.navigation)


def _memory_models(state: Any) -> Iterable[Any]:
    for e in (getattr(state, "entities", None) or {}).values():
        yield (f"entity {e.id}", e.cognition.memory)


def _identities(state: Any) -> Iterable[Any]:
    for e in (getattr(state, "entities", None) or {}).values():
        yield (f"entity {e.id}", e.identity)


def _projects(state: Any) -> Iterable[Any]:
    for e in (getattr(state, "entities", None) or {}).values():
        for project in ((getattr(getattr(e, "strategic", None), "projects", None)) or {}).values():
            yield (f"project {project.id} of entity {e.id}", project)


def _blockers(state: Any) -> Iterable[Any]:
    for e in (getattr(state, "entities", None) or {}).values():
        for blocker in ((getattr(getattr(e, "strategic", None), "blockers", None)) or {}).values():
            yield (f"blocker {blocker.id} of entity {e.id}", blocker)


def _buildings(state: Any) -> Iterable[Any]:
    for b in (getattr(state, "buildings", None) or {}).values():
        yield (f"building {b.id}", b)


def _state_itself(state: Any) -> Iterable[Any]:
    yield ("state", state)


def _groups(state: Any) -> Iterable[Any]:
    for gid, g in sorted((getattr(state, "groups", None) or {}).items(), key=lambda kv: str(kv[0])):
        yield (f"group {gid}", g)


def _seed_next_group_id(state: Any, owner: Any) -> int:
    return seeded_next_group_id(state.groups)


def _none_on_unbound_group(state: Any, owner: Any) -> None:
    """None is the only valid value on a group with no contract. A group with a contract_id (retained dissolved records included) has no knowable holder or end reason, so the
    checkpoint is refused, naming the group."""
    if owner.contract_id is not None:
        raise CheckpointFieldMissingError(
            f"Checkpoint predates the group-contract binding: group {owner.id} has contract_id {owner.contract_id!r} (a retained dissolved record counts) but no contract holder or "
            f"end reason, which cannot be derived from the state. Restore refused; re-create the checkpoint with a current build."
        )
    return None


_GROUP_RULING = "rpg-designer 2026-11-01, checkpoint restore (TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS)"

# F3 (2.155): a pre-F3 state never lodged anyone, so the field is None. ``beds`` is content (per building spec) that a restore cannot reach: refuse.
FIELD_RULES: List[FieldRule] = [
    # 2.213 (COMB-356): a state that predates the way-round give-up had no way-round count open.
    FieldRule("wayround_count", _navigations, "wayround_count", fill=lambda state, owner: 0, ruling="2.213: a state that predates the way-round give-up had no count open", record="NavigationComponent"),
    FieldRule("wayround_best_distance", _navigations, "wayround_best_distance", fill=lambda state, owner: None, ruling="2.213: a state that predates the way-round give-up had no best distance", record="NavigationComponent"),
    FieldRule("wayround_anchor", _navigations, "wayround_anchor", fill=lambda state, owner: None, ruling="2.213 F1: a state that predates the pursuit-anchored count had no anchor", record="NavigationComponent"),
    FieldRule("wayround_last_tick", _navigations, "wayround_last_tick", fill=lambda state, owner: None, ruling="2.213 F1: a state that predates the pursuit-anchored count had no last-event tick", record="NavigationComponent"),
    FieldRule("giveup_records", _navigations, "giveup_records", fill=lambda state, owner: (), ruling="F2: a state that predates the give-up records held none", record="NavigationComponent"),
    FieldRule("service_refusals", _navigations, "service_refusals", fill=lambda state, owner: (), ruling="K2 fix B: a state that predates the typed service refusals held none", record="NavigationComponent"),
    FieldRule("target_purpose", _navigations, "target_purpose", fill=lambda state, owner: None, ruling="rpg-designer 2026-11-23, experience memory (#715 7091099713): a target that predates the purpose was chosen for none that is known; None is exactly that state", record="NavigationComponent"),
    FieldRule("target_gated", _navigations, "target_gated", fill=lambda state, owner: False, ruling="rpg-designer 2026-11-23, experience memory (#715 7091099713): a target that predates the latch flag was not recorded as gated; False is exactly that state", record="NavigationComponent"),
    FieldRule("arrived_this_attempt", _navigations, "arrived_this_attempt", fill=lambda state, owner: False, ruling="rpg-designer ruling 476631fe, owner #715 7130852946 and 7130979190: a state that predates the arrived-this-attempt flag did not record that the body had reached its target; False is exactly that state", record="NavigationComponent"),
    FieldRule("navigation", _memory_models, "navigation", fill=lambda state, owner: NavigationExperienceMemory(), ruling="rpg-designer 2026-11-23, experience memory (#715 7091099713): a state that predates the navigation experience memory held none; the empty memory is exactly that state", record="MemoryModel"),
    FieldRule("lodged_in", _navigations, "lodged_in", fill=lambda state, owner: None, ruling="2.155: a state that predates lodging lodged no one", record="NavigationComponent"),
    # PERC-02 (2.210): a state that predates the step clock never recorded a step, so the body reads still until it steps; None is exactly that state.
    FieldRule("last_moved_tick", _navigations, "last_moved_tick", fill=lambda state, owner: None, ruling="rpg-designer 2026-11-18, PERC-02: a state that predates the step clock recorded no step", record="NavigationComponent"),
    FieldRule("beds", _buildings, "beds", fill=None, ruling="2.155: beds are copied from content at compile; the checkpoint carries no compiled content", record="BuildingState"),
    # A pre-2.156 state kept no retreat clear window, so a project that predates it has none yet (it opens on the first clear observation); None is exactly that state.
    FieldRule("cleared_since", _projects, "cleared_since", fill=lambda state, owner: None, ruling="2.156: a state that predates the retreat clear window had no window", record="ProjectState"),
    # N10 (2.212): a state that predates the suspension clock stamped none; `expire_suspended` stamps a SUSPENDED record on first sight.
    FieldRule("ended_tick", _projects, "ended_tick", fill=lambda state, owner: None, ruling="rpg-designer 2026-11-18, churn: a project that ended before the field kept no end tick", record="ProjectState"),
    FieldRule("suspended_since", _projects, "suspended_since", fill=lambda state, owner: None, ruling="rpg-designer 2026-11-16, N10: a state that predates the suspension clock had none", record="ProjectState"),
    # 2.214: a state that predates the blocker lifecycle never timed a blocker out and never stamped when one was last inferred.
    FieldRule("failure_count", _blockers, "failure_count", fill=lambda state, owner: 0, ruling="rpg-designer 2026-11-17, blocker churn: a state that predates the blocker lifecycle had no timeouts", record="BlockerState"),
    FieldRule("last_project_end_tick", _blockers, "last_project_end_tick", fill=lambda state, owner: None, ruling="rpg-designer 2026-11-18, churn: a blocker that predates the field had no project end recorded", record="BlockerState"),
    FieldRule("last_seen_tick", _blockers, "last_seen_tick", fill=lambda state, owner: None, ruling="rpg-designer 2026-11-17, blocker churn: a state that predates the last-seen tick had none", record="BlockerState"),
    # The group rows (2.146). next_group_id stays the LAST AuthoritativeState field and the three group fields stay after _canonical_cache (an insert is refused by the schema check).
    FieldRule("next_group_id", _state_itself, "next_group_id", fill=_seed_next_group_id, ruling="rpg-designer 2026-10-31, group id allocation (addition 4)", record="AuthoritativeState"),
    FieldRule("group.contract_holder_id", _groups, "contract_holder_id", fill=_none_on_unbound_group, ruling=_GROUP_RULING, record="GroupRecord"),
    FieldRule("group.dissolution_reason", _groups, "dissolution_reason", fill=_none_on_unbound_group, ruling=_GROUP_RULING, record="GroupRecord"),
    FieldRule("group.dissolution_contract_status", _groups, "dissolution_contract_status", fill=_none_on_unbound_group, ruling=_GROUP_RULING, record="GroupRecord"),
    # M1 (kind means species): a state that predates the occupation label gave no body one, so None is exactly that state.
    FieldRule("occupation", _identities, "occupation", fill=lambda state, owner: None, ruling="rpg-designer 2026-11-16, kind-is-species ruling step 2: a state that predates the occupation label had none", record="IdentityComponent"),
]


def check_group_counter(state: Any) -> None:
    """The counter must be above every non-squad stored group id; the seed rule yields exactly the smallest such value. Runs once at restore, after the fill."""
    floor = seeded_next_group_id(state.groups)
    if state.next_group_id < floor:
        raise GroupCounterBehindStoreError(f"next_group_id {state.next_group_id} is not above the highest non-squad group id in the store (needs >= {floor})")


def fill_missing_fields(state: Any, rules: Optional[List[FieldRule]] = None) -> Any:
    """Fill (or refuse) every field in ``rules`` that the unpickled ``state`` lacks. Returns ``state`` (records are mutated in place: they are frozen, so the slot is set through
    ``object.__setattr__``, the same way the unpickle itself set the others)."""
    for rule in (FIELD_RULES if rules is None else rules):
        missing = [(label, owner) for label, owner in rule.records(state) if getattr(owner, rule.field, _UNSET) is _UNSET]
        if not missing:
            continue
        if rule.fill is None:
            labels = ", ".join(label for label, _ in missing[:5]) + (f" (+{len(missing) - 5} more)" if len(missing) > 5 else "")
            raise CheckpointFieldMissingError(f"checkpoint predates field {rule.field!r} and no rule derives it ({rule.ruling}); missing on {len(missing)} record(s): {labels}")
        for _, owner in missing:
            object.__setattr__(owner, rule.field, rule.fill(state, owner))
    return state


# A new field of a slotted record must be the LAST field of its class and have a row here with ``record`` set: ``checkpoint_schema.check_schema`` refuses an insert, and an append without a row, before the unpickle.
