"""Pure observation helpers for the access audit: cheap fingerprints of tick-start state and of a StateUpdate, and their diffs.

Plain attribute reads only: no ``to_dict``, digest or hash call that fills a cache (``_canonical_cache``), and no lazy property. A token is ``id`` for an object,
``(id, len)`` for a container and the value for a primitive, so an in-place append (``entity.timeline.append``) and a replaced attribute are both seen; a scalar written
INTO an unchanged sub-object (``object.__setattr__`` on a frozen sub-state) is not (one level of entity attributes is read, not their contents)."""
from __future__ import annotations

import collections
import dataclasses
import sys
from typing import Any, Dict, FrozenSet, List, Tuple

_PRIMITIVES = (int, float, str, bool, bytes, type(None))
_CONTAINERS = (dict, list, set, frozenset, tuple, collections.deque)
_NAMES_CACHE: Dict[type, Tuple[str, ...]] = {}

# Tier 1 (plan 3a): content-hashed. State attributes (carried across ticks by reference) and the one per-entity attribute.
WATCH_STATE_ATTRS: FrozenSet[str] = frozenset({
    "route_plans", "movement_cache", "occupancy_snapshot", "_occupancy_map_cache", "transient_claims", "_has_hostiles_or_dead_cache", "world_indexes",
    "_spatial_grid_cache", "_region_list_cache", "_node_map_cache", "_corpse_map_cache", "_ground_item_map_cache", "_building_map_cache",
    "_region_index_cache", "_building_region_map_cache", "_readonly_entities_cache",
})
WATCH_ENTITY_ATTRS: FrozenSet[str] = frozenset({"timeline"})
WATCH_PATHS: FrozenSet[str] = WATCH_STATE_ATTRS | frozenset(f"entities[*].{a}" for a in WATCH_ENTITY_ATTRS)
# Process globals (plan 1): (module, attribute), read through ``sys.modules`` only, never imported from the hot path.
GLOBAL_WATCH: Tuple[Tuple[str, str], ...] = (
    ("src.content.terrain_cost", "_terrain_cache"),
    ("src.core.registries", "runtime_content_source"),
    ("src.content.common_knowledge_seed", "_warm_catalog_provider"),
    ("src.content.common_knowledge_seed", "_fallback_catalog"),
)
_MAX_DEPTH = 3
_NODE_BUDGET = 400


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


_FROZEN: Dict[type, bool] = {}


def _is_frozen_record(tp: type) -> bool:
    """True for a frozen dataclass (an immutable record): its identity stands for its content."""
    known = _FROZEN.get(tp)
    if known is None:
        params = getattr(tp, "__dataclass_params__", None)
        known = _FROZEN[tp] = bool(params is not None and params.frozen) or tp in _PRIMITIVES
    return known


TIMELINE_MUTABLE_BY_CONTENT = False  # True: digest the content of a non-frozen timeline element (measured ~2.7x the ids-only cost on 100 ticks)


def _element_token(element: Any) -> Any:
    return digest(element, 1) if TIMELINE_MUTABLE_BY_CONTENT and not _is_frozen_record(type(element)) else id(element)


def timeline_token(value: Any) -> Any:
    """Token of an entity timeline: the deque's own id, its length, and per element its id (a frozen dataclass: immutable, so identity is content) or its content digest (a mutable record, e.g. a pydantic ``SimulationEvent``).

    Kept behind this one function so full-content hashing is a one-line change."""
    if isinstance(value, collections.deque):
        return (id(value), len(value), hash(tuple(_element_token(e) for e in value)))
    return token(value)


TIMELINE_SAMPLE_EVERY = 100  # ticks between the sampled content checks of mutable timeline elements (reported as "sampled, not per step")


FIELD_REPR_CHARS = 80


def _stable_key(element: Any, type_name: str, seen: Dict[Any, int]) -> Any:
    """Identity of a timeline element that does not depend on ``id()``: its own ``event_id`` when it has one, else (tick, type, ordinal among same-tick same-type elements in that deque)."""
    event_id = getattr(element, "event_id", None)
    if isinstance(event_id, str):
        return event_id
    base = (getattr(element, "tick", None), type_name)
    seen[base] = seen.get(base, 0) + 1
    return (*base, seen[base])


def _field_reprs(element: Any) -> Dict[str, str]:
    """Plain-attribute field values as truncated reprs (kept only to name the fields that differ)."""
    attrs = getattr(element, "__dict__", None)
    return {k: repr(v)[:FIELD_REPR_CHARS] for k, v in attrs.items()} if isinstance(attrs, dict) else {}


def sample_mutable_timeline_elements(state: Any) -> Dict[int, Tuple[Any, str, int, Any, Any, Dict[str, str]]]:
    """Per NON-frozen timeline element (frozen dataclasses are immutable, so identity is content), keyed by element id (no reference to the element is kept): ``(entity_id, type name, index in the deque, content digest, stable key, field reprs)``."""
    out: Dict[int, Tuple[Any, str, int, Any, Any, Dict[str, str]]] = {}
    for e_id, ent in object.__getattribute__(state, "entities").items():
        timeline = getattr(ent, "timeline", None)
        seen: Dict[Any, int] = {}
        for idx, element in enumerate(timeline if isinstance(timeline, collections.deque) else ()):
            if not _is_frozen_record(type(element)):
                name = type(element).__name__
                out[id(element)] = (e_id, name, idx, digest(element, 1), _stable_key(element, name, seen), _field_reprs(element))
    return out


def digest(value: Any, depth: int = 0, budget: List[int] | None = None) -> Any:
    """Content digest (keys, values, order) of ``value``, reading plain attributes only. Past ``_MAX_DEPTH`` or the node budget a node falls back to its id."""
    if isinstance(value, _PRIMITIVES):
        return value
    budget = [_NODE_BUDGET] if budget is None else budget
    budget[0] -= 1
    if depth >= _MAX_DEPTH or budget[0] < 0:
        return id(value)
    nxt = depth + 1
    if isinstance(value, dict):
        return hash(tuple((k, digest(v, nxt, budget)) for k, v in value.items()))
    if isinstance(value, (list, tuple, collections.deque)):
        return hash((len(value), tuple(digest(v, nxt, budget) for v in value)))
    if isinstance(value, (set, frozenset)):
        return hash(frozenset(value))
    return _object_digest(value, nxt, budget)


def _object_digest(value: Any, depth: int, budget: List[int]) -> Any:
    names = _attr_names(value)
    if not names:
        return id(value)
    parts = []
    for name in names:
        try:
            parts.append(digest(object.__getattribute__(value, name), depth, budget))
        except AttributeError:
            continue
    return hash((type(value).__name__, tuple(parts)))


def _attr_tokens(obj: Any, prefix: str, out: Dict[str, Any], watch: FrozenSet[str] = frozenset(), timeline_names: FrozenSet[str] = frozenset()) -> None:
    """Add a token per attribute of ``obj`` to ``out`` under ``prefix``: a content digest for a Tier 1 name, an id/len token otherwise."""
    for name in _attr_names(obj):
        try:
            raw = object.__getattribute__(obj, name)
        except AttributeError:
            continue
        out[prefix + name] = digest(raw) if name in watch else timeline_token(raw) if name in timeline_names else token(raw)


def snapshot_state(state: Any) -> Dict[str, Any]:
    """Token per top-level state attribute, and per attribute of every entity (``entities[<id>].<attr>``)."""
    snap: Dict[str, Any] = {}
    _attr_tokens(state, "", snap, WATCH_STATE_ATTRS)
    entities = snap.get("entities")
    if isinstance(entities, tuple):  # a dict token is (id, len)
        for e_id, ent in object.__getattribute__(state, "entities").items():
            _attr_tokens(ent, f"entities[{e_id}].", snap, frozenset(), WATCH_ENTITY_ATTRS)
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


def split_tiers(paths: FrozenSet[str]) -> Tuple[FrozenSet[str], FrozenSet[str]]:
    """Split changed (folded) paths into Tier 1 (watch list) and Tier 2 (everything else: a hit here is a field to promote to the watch list)."""
    return frozenset(p for p in paths if p in WATCH_PATHS), frozenset(p for p in paths if p not in WATCH_PATHS)


def snapshot_globals() -> Dict[str, Any]:
    """Content digest of each process-global watch entry whose module is already loaded (``sys.modules`` only, never an import); absent entries are omitted."""
    out: Dict[str, Any] = {}
    for mod, attr in GLOBAL_WATCH:
        module = sys.modules.get(mod)
        if module is not None and attr in vars(module):
            out[f"{mod}:{attr}"] = digest(vars(module)[attr])
    return out


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


def update_identity_only(before: Any, after: Any) -> Tuple[FrozenSet[str], FrozenSet[str]]:
    """A3 column: the fields/buckets whose object was REPLACED but compare equal (identity changed, value did not), and those whose ``==`` raised (not comparable, so treated as changed)."""
    same: set = set()
    unsafe: set = set()
    for name, a, b in _paired_values(before, after):
        if a is b:
            continue
        try:
            if a == b:
                same.add(name)
        except (TypeError, ValueError):
            unsafe.add(name)
    return frozenset(same), frozenset(unsafe)


def _paired_values(before: Any, after: Any) -> list:
    pairs = [(f"su:{f.name}", getattr(before, f.name), getattr(after, f.name)) for f in dataclasses.fields(after) if f.name != "entity_updates"]
    for e_id, eu in after.entity_updates.items():
        old = before.entity_updates.get(e_id)
        if old is not None:
            pairs.extend((f"eu:{g.name}", getattr(old, g.name), getattr(eu, g.name)) for g in dataclasses.fields(eu) if g.name != "entity_id")
    return pairs


def entity_fanout(before: Any, after: Any) -> Tuple[int, Dict[str, int]]:
    """Cross-entity proxy (the dispatch layer cannot know which entity a step acts for): how many entity entries the step CREATED (id absent from the input update), and per bucket how many distinct entity ids it wrote."""
    created = sum(1 for e_id in after.entity_updates if e_id not in before.entity_updates)
    ids: Dict[str, set] = {}
    for e_id, eu in after.entity_updates.items():
        for bucket in _entity_bucket_writes(before.entity_updates.get(e_id), eu):
            ids.setdefault(bucket, set()).add(e_id)
    return created, {b: len(v) for b, v in ids.items()}
