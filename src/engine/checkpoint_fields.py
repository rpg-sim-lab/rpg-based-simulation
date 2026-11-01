"""Fill fields missing from an older checkpoint: the one post-unpickle step of ScenarioCheckpointer.restore.

A frozen slotted record unpickled from an older checkpoint does not run __init__/__post_init__ and lacks every slot added since, so the
first read raises AttributeError. A missing field is filled ONLY when its value is a pure function of the loaded state that a ruling already
defines; otherwise the restore is refused with CheckpointFieldMissingError. Nothing is guessed. Every rule is a row of FIELD_RULES, applied by the
single function fill_missing_fields(); there are no fixups anywhere else.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Iterable, Tuple

from src.core.state import seeded_next_group_id

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState


class CheckpointFieldMissingError(ValueError):
    """An older checkpoint lacks a field whose value cannot be derived from the loaded state, so the restore is refused.

    A ValueError, so the scenarios restore route answers it as a client error (400), not a server error.
    """


class GroupCounterBehindStoreError(ValueError):
    """A restored checkpoint's group id counter is not above every non-squad group id in its store (dissolved records included), so the next formation
    could reuse a taken id. Raised at restore, after the fill; never in __post_init__ or replace. A ValueError, so the restore route answers 400."""


@dataclass(frozen=True)
class FieldRule:
    """One row of the restore table: where a field lives, how a missing value is derived (or refused), and the ruling that allows it."""

    name: str  # rule name, for messages and tests
    records: Callable[[Any], Iterable[Tuple[Any, Any]]]  # state -> (key, record) pairs the field lives on
    field: str  # slot name on the record
    fill: Callable[[Any, Any, Any], Any]  # (record, state, key) -> value; raises CheckpointFieldMissingError to refuse
    ruling: str  # where the rule is decided


def _state_itself(state: AuthoritativeState) -> Iterable[Tuple[Any, Any]]:
    return [(None, state)]


def _groups(state: AuthoritativeState) -> Iterable[Tuple[Any, Any]]:
    return sorted(state.groups.items(), key=lambda kv: str(kv[0]))


def _seed_next_group_id(record: Any, state: AuthoritativeState, key: Any) -> int:
    return seeded_next_group_id(state.groups)


def _none_on_unbound_group(record: Any, state: AuthoritativeState, key: Any) -> None:
    """None is the only valid value on a group with no contract. A group with a contract_id (retained dissolved records included) has no
    knowable holder or end reason, so the checkpoint is refused, naming the group."""
    contract_id = getattr(record, "contract_id", None)
    if contract_id is not None:
        raise CheckpointFieldMissingError(
            f"Checkpoint predates the group-contract binding: group {key} has contract_id {contract_id!r} (a retained dissolved record "
            f"counts) but no contract holder or end reason, which cannot be derived from the state. Restore refused; "
            f"re-create the checkpoint with a current build."
        )
    return None


_GROUP_RULING = "rpg-designer 2026-11-01, checkpoint restore (TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS)"

FIELD_RULES: Tuple[FieldRule, ...] = (
    FieldRule("next_group_id", _state_itself, "next_group_id", _seed_next_group_id, "rpg-designer 2026-10-31, group id allocation (addition 4)"),
    FieldRule("group.contract_holder_id", _groups, "contract_holder_id", _none_on_unbound_group, _GROUP_RULING),
    FieldRule("group.dissolution_reason", _groups, "dissolution_reason", _none_on_unbound_group, _GROUP_RULING),
    FieldRule("group.dissolution_contract_status", _groups, "dissolution_contract_status", _none_on_unbound_group, _GROUP_RULING),
)


def check_group_counter(state: AuthoritativeState) -> None:
    """The counter must be above every non-squad stored group id; the seed rule yields exactly the smallest such value."""
    floor = seeded_next_group_id(state.groups)
    if state.next_group_id < floor:
        raise GroupCounterBehindStoreError(f"next_group_id {state.next_group_id} is not above the highest non-squad group id in the store (needs >= {floor})")


def fill_missing_fields(state: AuthoritativeState, rules: Tuple[FieldRule, ...] = FIELD_RULES) -> None:
    """Apply every rule to the freshly unpickled state. A field that is present (not missing, not None for next_group_id) is left alone."""
    for rule in rules:
        for key, record in rule.records(state):
            present = hasattr(record, rule.field)
            if present and not (rule.field == "next_group_id" and getattr(record, rule.field) is None):
                continue
            object.__setattr__(record, rule.field, rule.fill(record, state, key))
