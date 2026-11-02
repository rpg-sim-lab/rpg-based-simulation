# Compliance IDs: INFRA-215
"""The one post-unpickle step of a scenario restore: a field a checkpoint predates (F3, divergence 2.155; later rows join this table).

A scenario checkpoint is a pickle of the whole ``AuthoritativeState`` with no format version (``ScenarioCheckpointer``). Unpickling a slotted, frozen record written before a field
existed skips ``__post_init__`` and leaves the slot UNSET, so the first read raises a raw ``AttributeError`` mid-tick. This step runs once, right after the unpickle, over a small table
``FIELD_RULES`` (the single restore step: later rows, from any lane, are added here; keep the names and the ``FieldRule`` shape): each row names the records that carry the field, the field, and a rule.

THE RULE: fill only a pure function of the loaded state that a ruling defines; else a typed refusal. A missing field is FILLED only when its value is a pure function of the loaded state that a ruling already defines (``fill``). Otherwise the row has no ``fill`` and the
restore REFUSES with ``CheckpointFieldMissingError``, naming the field and the records. A checkpoint that carries every field is not touched, so a current-shape restore is unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, List, Optional

_UNSET = object()


class CheckpointFieldMissingError(ValueError):
    """A checkpoint predates a field whose value cannot be derived from the loaded state: the restore is refused (never a raw ``AttributeError`` mid-tick)."""


@dataclass(frozen=True)
class FieldRule:
    """``records(state)`` yields ``(label, owner)`` where ``owner`` is the record that carries ``field``; ``fill(state, owner)`` is the value to set, or ``None`` for no rule (refuse)."""
    name: str
    records: Callable[[Any], Iterable[Any]]
    field: str
    fill: Optional[Callable[[Any, Any], Any]] = None
    ruling: str = ""


def _navigations(state: Any) -> Iterable[Any]:
    for e in (getattr(state, "entities", None) or {}).values():
        yield (f"entity {e.id}", e.navigation)


def _projects(state: Any) -> Iterable[Any]:
    for e in (getattr(state, "entities", None) or {}).values():
        for project in ((getattr(getattr(e, "strategic", None), "projects", None)) or {}).values():
            yield (f"project {project.id} of entity {e.id}", project)


def _buildings(state: Any) -> Iterable[Any]:
    for b in (getattr(state, "buildings", None) or {}).values():
        yield (f"building {b.id}", b)


# F3 (2.155): a pre-F3 state never lodged anyone, so the field is None. ``beds`` is content (per building spec) that a restore cannot reach: refuse.
FIELD_RULES: List[FieldRule] = [
    FieldRule("lodged_in", _navigations, "lodged_in", fill=lambda state, owner: None, ruling="2.155: a state that predates lodging lodged no one"),
    FieldRule("beds", _buildings, "beds", fill=None, ruling="2.155: beds are copied from content at compile; the checkpoint carries no compiled content"),
    # A pre-2.156 state kept no retreat clear window, so a project that predates it has none yet (it opens on the first clear observation); None is exactly that state.
    FieldRule("cleared_since", _projects, "cleared_since", fill=lambda state, owner: None, ruling="2.156: a state that predates the retreat clear window had no window"),
]


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


# A new field of a slotted record must be the LAST field of its class (``dataclasses._dataclass_setstate`` unpickles positionally: a field inserted before another silently takes
# that field's old value from an older checkpoint, which no check here can see). `tests/unit/engine/test_checkpoint_fields.py` pins the position of every row's field.
