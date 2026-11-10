"""Pure observation helpers for the access audit: cheap fingerprints of tick-start state and of a StateUpdate, and their diffs.

Plain attribute reads only: no ``to_dict``, digest or hash call that fills a cache (``_canonical_cache``), and no lazy property. A token is ``id`` for an object,
``(id, len)`` for a container and the value for a primitive, so an in-place append (``entity.timeline.append``) and a replaced attribute are both seen; a scalar written
INTO an unchanged sub-object (``object.__setattr__`` on a frozen sub-state) is not (one level of entity attributes is read, not their contents)."""
from __future__ import annotations

import dataclasses
from typing import Any, Dict, FrozenSet, Tuple

_PRIMITIVES = (int, float, str, bool, bytes, type(None))
_CONTAINERS = (dict, list, set, frozenset, tuple)
_NAMES_CACHE: Dict[type, Tuple[str, ...]] = {}


def _declared_names(tp: type) -> Tuple[str, ...]:
    names = _NAMES_CACHE.get(tp)
    if names is None:
        found: list = []
        if dataclasses.is_dataclass(tp):
            found.extend(f.name for f in dataclasses.fields(tp))
        for klass in tp.__mro__:
            slots = klass.__dict__.get("__slots__", ())
            found.extend([slots] if isinstance(slots, str) else slots)
        names = tuple(dict.fromkeys(n for n in found if not n.startswith("__")))
        _NAMES_CACHE[tp] = names
    return names


def _attr_names(obj: Any) -> Tuple[str, ...]:
    """Declared field and slot names plus any instance-dict key (a flag set with ``object.__setattr__`` lands there)."""
    names = _declared_names(type(obj))
    extra = getattr(obj, "__dict__", None)
    return names + tuple(k for k in extra if k not in names) if extra else names


def token(value: Any) -> Any:
    """A cheap identity token: the value for a primitive, ``(id, len)`` for a container, ``id`` otherwise."""
    if isinstance(value, _PRIMITIVES):
        return value
    if isinstance(value, _CONTAINERS):
        return (id(value), len(value))
    return id(value)


def _attr_tokens(obj: Any, prefix: str, out: Dict[str, Any]) -> None:
    """Add a token per attribute of ``obj`` to ``out`` under ``prefix``."""
    for name in _attr_names(obj):
        try:
            out[prefix + name] = token(object.__getattribute__(obj, name))
        except AttributeError:
            continue


def snapshot_state(state: Any) -> Dict[str, Any]:
    """Token per top-level state attribute, and per attribute of every entity (``entities[<id>].<attr>``)."""
    snap: Dict[str, Any] = {}
    _attr_tokens(state, "", snap)
    entities = snap.get("entities")
    if isinstance(entities, tuple):  # a dict token is (id, len)
        for e_id, ent in object.__getattribute__(state, "entities").items():
            _attr_tokens(ent, f"entities[{e_id}].", snap)
    return snap


def diff_state(before: Dict[str, Any], after: Dict[str, Any]) -> FrozenSet[str]:
    """The paths whose token changed or that appeared or vanished, with the entity id folded out: ``entities[*].timeline``."""
    changed = {k for k in before.keys() | after.keys() if before.get(k, _MISSING) != after.get(k, _MISSING)}
    return frozenset(_fold(k) for k in changed)


_MISSING = object()


def _fold(path: str) -> str:
    if path.startswith("entities[") and "]." in path:
        return "entities[*]." + path.split("].", 1)[1]
    return path


def snapshot_update(upd: Any) -> Dict[str, Any]:
    """Token per StateUpdate field, and per bucket of every EntityUpdate (``entity_updates[<id>].<bucket>``)."""
    snap: Dict[str, Any] = {}
    for f in dataclasses.fields(upd):
        value = getattr(upd, f.name)
        snap[f.name] = token(value)
        if f.name == "entity_updates" and isinstance(value, dict):
            for e_id, eu in value.items():
                for g in dataclasses.fields(eu):
                    snap[f"entity_updates[{e_id}].{g.name}"] = token(getattr(eu, g.name))
    return snap


def _differs(a: Any, b: Any) -> bool:
    if a is b:
        return False
    try:
        return bool(a != b)
    except (TypeError, ValueError):
        return True


def _is_set(value: Any) -> bool:
    try:
        return bool(value)
    except (TypeError, ValueError):
        return True


def _entity_bucket_writes(old: Any, new: Any) -> set:
    """The EntityUpdate buckets ``new`` wrote relative to ``old`` (None = the entity's update is new, so every set bucket counts)."""
    return {
        f"eu:{g.name}"
        for g in dataclasses.fields(new)
        if g.name != "entity_id" and (_is_set(getattr(new, g.name)) if old is None else _differs(getattr(old, g.name), getattr(new, g.name)))
    }


def update_writes(before: Any, after: Any) -> FrozenSet[str]:
    """The update entries a step wrote: ``su:<field>`` for a StateUpdate field, ``eu:<bucket>`` for an EntityUpdate bucket (entity ids folded out).

    A field or bucket counts when its value differs from the input update's, or is set (non-default) on an entity the step added."""
    writes = {f"su:{f.name}" for f in dataclasses.fields(after) if f.name != "entity_updates" and _differs(getattr(before, f.name), getattr(after, f.name))}
    for e_id, eu in after.entity_updates.items():
        writes |= _entity_bucket_writes(before.entity_updates.get(e_id), eu)
    return frozenset(writes)


def update_inplace(before: Dict[str, Any], upd: Any) -> FrozenSet[str]:
    """Fields of the INPUT update that the step mutated in place (token changed on the same object)."""
    now = snapshot_update(upd)
    return frozenset(_fold_update(k) for k in before.keys() | now.keys() if before.get(k, _MISSING) != now.get(k, _MISSING))


def _fold_update(path: str) -> str:
    if path.startswith("entity_updates[") and "]." in path:
        return "eu:" + path.split("].", 1)[1]
    return f"su:{path}"
