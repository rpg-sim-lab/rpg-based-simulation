"""Mechanical per-field probe of the canonical state digest (TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ, item 1).

For every field path reachable from ``AuthoritativeState`` (entities are ``EntityState``) through nested dataclasses and containers, change the field and see whether
``CanonicalStateHasher.get_hash`` moves. The change is type-correct: it comes from the field's declared type (or its live value's type), never a sentinel that a
hasher would choke on. A field is

* ``covered``: the digest moved;
* ``unhashed``: a type-correct change left the digest equal (after every ``_canonical_cache`` memo was cleared, since components cache their canonical dict);
* ``unexercised``: no type-correct change could be built (the reason says why), or hashing raised on it, which shows only that the probe was wrong.

An empty container or a ``None`` optional is exercised by synthesizing one element from the type hints (``synthesize``) and probing that element's own fields in
place. Synthesized records exist only inside a probe: they are removed afterwards and are never given to a simulation.

Samples are fixed so the result is deterministic: ``SAMPLES`` names each world, seed and tick count.
"""
from __future__ import annotations

import collections
import dataclasses
import enum
import importlib
import shutil
import sys
import types
import typing
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.core.state import AuthoritativeState, ReadOnlyDict
from src.engine.checkpoint import CanonicalStateHasher

SAMPLES: Tuple[Tuple[str, int, int], ...] = (("urban_political", 42, 0), ("crowded_frontier", 42, 60))  # a third world (frontier_living_world, 60 ticks) adds no unhashed path
MAX_DEPTH = 14
CACHE_FIELD = "_canonical_cache"
_NS_MODULES = ("src.core.state", "src.core.cognition", "src.core.strategic", "src.core.self_model", "src.core.social", "src.core.inventory",
               "src.core.death_cause", "src.core.genetics", "src.core.updates", "src.domains.culture.model", "src.domains.fame.legend",
               "src.domains.belief_institution.model", "src.domains.combat_engagement.schema", "src.core.models.quests", "src.domains.information.providers")


class Cannot(Exception):
    """A type-correct value could not be built; the message says why."""


def _namespace() -> Dict[str, Any]:
    ns: Dict[str, Any] = {}
    for name in _NS_MODULES:
        try:
            mod = importlib.import_module(name)
        except ImportError:
            continue
        ns.update({k: v for k, v in vars(mod).items() if isinstance(v, type)})
    return ns


_NS = _namespace()


def hints_of(cls: type) -> Dict[str, Any]:
    ns = dict(vars(sys.modules[cls.__module__]))
    ns.update(_NS)
    try:
        return typing.get_type_hints(cls, ns)
    except Exception:  # noqa: BLE001 - an unresolvable forward reference: fall back per field
        out: Dict[str, Any] = {}
        for f in dataclasses.fields(cls):
            try:
                out[f.name] = typing.get_type_hints(type("_H", (), {"__annotations__": {"x": f.type}, "__module__": cls.__module__}), ns).get("x")
            except Exception:  # noqa: BLE001
                out[f.name] = None
        return out


def _strip_optional(tp: Any) -> Any:
    if typing.get_origin(tp) in (typing.Union, types.UnionType):
        args = [a for a in typing.get_args(tp) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return tp


def synthesize(tp: Any, _stack: Tuple[type, ...] = ()) -> Any:
    """One value of declared type ``tp``, small and non-default; raises ``Cannot`` with the reason."""
    if tp is Any or tp is object:
        return "x"  # declared as anything: a short string is type-correct
    if tp is None or isinstance(tp, (str, typing.ForwardRef)):
        raise Cannot("unresolved forward reference")
    tp = _strip_optional(tp)
    origin = typing.get_origin(tp)
    args = typing.get_args(tp)
    if origin in (typing.Union, types.UnionType):  # several types are accepted: the first declared one is type-correct
        return synthesize([a for a in args if a is not type(None)][0], _stack)
    if origin is typing.Literal:
        return args[0]
    if origin in (list, typing.List):
        return [synthesize(args[0], _stack)] if args else ["x"]
    if origin in (tuple, typing.Tuple):
        if not args:
            return ("x",)
        if len(args) == 2 and args[1] is Ellipsis:
            return (synthesize(args[0], _stack),)
        return tuple(synthesize(a, _stack) for a in args)
    if origin in (dict, typing.Dict, collections.abc.Mapping):
        return {synthesize(args[0], _stack): synthesize(args[1], _stack)} if len(args) == 2 else {"x": "x"}
    if origin in (set, frozenset, typing.Set, typing.FrozenSet):
        return origin({synthesize(args[0], _stack)}) if args else {"x"}
    if origin is collections.deque:
        return collections.deque([synthesize(args[0], _stack)] if args else ["x"])
    if origin is not None:
        raise Cannot(f"generic {origin}")
    if tp is bool:
        return True
    if tp is int:
        return 1
    if tp is float:
        return 1.0
    if tp is str:
        return "x"
    if isinstance(tp, type) and issubclass(tp, enum.Enum):
        return next(iter(tp))
    if isinstance(tp, type) and dataclasses.is_dataclass(tp):
        if tp in _stack:
            raise Cannot(f"recursive type {tp.__name__}")
        h = hints_of(tp)
        kwargs = {}
        for f in dataclasses.fields(tp):
            if not f.init:
                continue
            if f.default is not dataclasses.MISSING or f.default_factory is not dataclasses.MISSING:
                continue
            kwargs[f.name] = synthesize(h.get(f.name), _stack + (tp,))
        try:
            return tp(**kwargs)
        except Exception as exc:  # noqa: BLE001
            raise Cannot(f"{tp.__name__}(...) raised {type(exc).__name__}") from None
    if isinstance(tp, type):
        raise Cannot(f"no rule for {tp.__name__}")
    raise Cannot(f"unresolved type {tp!r}")


def _is_instance(o: Any) -> bool:
    return dataclasses.is_dataclass(o) and not isinstance(o, type)


def _elem_hint(hint: Any) -> Any:
    if hint is Any or hint is object:
        return Any
    hint = _strip_optional(hint)
    args = typing.get_args(hint)
    origin = typing.get_origin(hint)
    if origin in (dict, typing.Dict, collections.abc.Mapping) and len(args) == 2:
        return args[1]
    if args:
        return args[0]
    return None


def _perturb_set(value: Any, elem: Any, ehint: Any) -> Tuple[Any, Optional[Any]]:
    """A set or frozenset that is NOT equal to ``value``. The usual union with ``elem`` grows it; when ``elem`` is already a member (an enum set that holds the first member,
    which is what ``synthesize`` returns) the union equals the original and no digest could move, so add a member the set does not hold (another enum member, or a changed
    ``elem``) and, if there is none, remove one element (the least by ``repr``, so the choice is deterministic). The second value is the added element, ``None`` for a removal."""
    union = set(value) | {elem}
    if union != set(value):
        return type(value)(union), (elem if _is_instance(elem) else None)
    candidates = [m for m in type(elem) if m not in value] if isinstance(elem, enum.Enum) else []
    if not candidates and not isinstance(elem, enum.Enum):
        try:
            candidates = [perturb(elem, ehint)[0]]
        except Cannot:
            candidates = []
    for candidate in candidates:
        if candidate not in value:
            return type(value)(set(value) | {candidate}), (candidate if _is_instance(candidate) else None)
    smallest = min(value, key=repr)
    return type(value)(set(value) - {smallest}), None


def _perturb_fixed_arity(value: tuple, hint: Any) -> Optional[Tuple[Any, Optional[Any]]]:
    """A fixed-arity tuple (``Tuple[int, int]``: declared per position, no ``...``) keeps its length: appending is out of type, and ``to_canonical`` writes only the declared
    positions, so an append would read as unhashed. Change the first element that can be changed, with that position's own hint. ``None`` when ``hint`` is not a fixed-arity
    tuple of ``value``'s length (variadic ``Tuple[X, ...]`` and bare tuples keep the append); ``Cannot`` when no position can be changed."""
    args = typing.get_args(_strip_optional(hint))
    if typing.get_origin(_strip_optional(hint)) is not tuple or not args or Ellipsis in args or len(args) != len(value):
        return None
    for index, element_hint in enumerate(args):
        try:
            changed, inserted = perturb(value[index], element_hint)
        except Cannot:
            continue
        return value[:index] + (changed,) + value[index + 1:], inserted
    raise Cannot("no position of the fixed-arity tuple can be changed")


def perturb(value: Any, hint: Any) -> Tuple[Any, Optional[Any]]:
    """(new value, the inserted element or None). Type-correct; raises ``Cannot``."""
    if isinstance(value, bool):
        return (not value), None
    if isinstance(value, enum.Enum):
        others = [m for m in type(value) if m is not value]
        if not others:
            raise Cannot("single-member enum")
        return others[0], None
    if isinstance(value, int):
        return value + 1, None
    if isinstance(value, float):
        return value + 1.0, None
    if isinstance(value, str):
        return value + "~", None
    if value is None:
        inner = _strip_optional(hint)
        new = synthesize(inner)
        return new, (new if _is_instance(new) else None)
    if isinstance(value, tuple):
        in_place = _perturb_fixed_arity(value, hint)
        if in_place is not None:
            return in_place
    ehint = _elem_hint(hint)
    if isinstance(value, ReadOnlyDict) or isinstance(value, dict):
        if value and ehint is None:
            ehint = type(next(iter(value.values())))
        elem = synthesize(ehint)
        key_hint = (typing.get_args(_strip_optional(hint)) or (None,))[0]
        key = synthesize(key_hint) if key_hint is not None else "~probe"
        if key in value:
            key = (key + "~") if isinstance(key, str) else key
        new = dict(value)
        new[key] = elem
        return (ReadOnlyDict(new) if isinstance(value, ReadOnlyDict) else new), (elem if _is_instance(elem) else None)
    if isinstance(value, (tuple, list, collections.deque, set, frozenset)):
        if value and ehint is None:
            ehint = type(next(iter(value)))
        elem = synthesize(ehint)
        if isinstance(value, tuple):
            new = value + (elem,)
        elif isinstance(value, list):
            new = value + [elem]
        elif isinstance(value, collections.deque):
            new = collections.deque(value)
            new.append(elem)
        else:
            return _perturb_set(value, elem, ehint)
        return new, (elem if _is_instance(elem) else None)
    raise Cannot(f"no perturbation for {type(value).__name__}")


def cache_holders(state: Any) -> List[Any]:
    """Every instance in ``state`` that carries a ``_canonical_cache`` memo, found once per probed state."""
    holders: List[Any] = []
    seen: set = set()

    def rec(o: Any) -> None:
        if id(o) in seen:
            return
        seen.add(id(o))
        if _is_instance(o):
            if any(f.name == CACHE_FIELD for f in dataclasses.fields(o)):
                holders.append(o)
            for f in dataclasses.fields(o):
                if f.name != CACHE_FIELD:
                    rec(getattr(o, f.name))
        elif isinstance(o, dict):
            for x in o.values():
                rec(x)
        elif isinstance(o, (list, tuple, collections.deque)):
            for x in o:
                rec(x)

    rec(state)
    return holders


def clear_caches(state: Any) -> None:
    seen: set = set()

    def rec(o: Any) -> None:
        if id(o) in seen:
            return
        seen.add(id(o))
        if _is_instance(o):
            for f in dataclasses.fields(o):
                if f.name == CACHE_FIELD:
                    object.__setattr__(o, f.name, None)
                else:
                    rec(getattr(o, f.name))
        elif isinstance(o, dict):
            for x in o.values():
                rec(x)
        elif isinstance(o, (list, tuple, collections.deque)):
            for x in o:
                rec(x)

    rec(state)


@dataclasses.dataclass
class Result:
    path: str
    owner: str
    field: str
    status: str  # covered | unhashed | unexercised
    reason: str = ""


def probe_state(state: Any) -> List[Result]:
    results: List[Result] = []
    base = [None]

    holders = cache_holders(state)

    def digest() -> Optional[str]:
        for h in holders:
            object.__setattr__(h, CACHE_FIELD, None)
        try:
            return CanonicalStateHasher.get_hash(state)
        except Exception:  # noqa: BLE001
            return None

    def visit(o: Any, path: str, depth: int, seen: set, ref: Optional[str]) -> None:
        if id(o) in seen or depth > MAX_DEPTH:
            return
        seen.add(id(o))
        visited.append(o)
        hints = hints_of(type(o))
        for f in dataclasses.fields(o):
            if f.name == CACHE_FIELD:
                continue
            fpath = f"{path}.{f.name}"
            value = getattr(o, f.name)
            hint = hints.get(f.name)
            if _is_instance(value):
                visit(value, fpath, depth + 1, seen, ref)
                continue
            _recurse_existing(value, fpath, depth, seen, ref)  # live records first, then the synthesized one: both are probed, so a field hashed only conditionally shows
            try:
                new, inserted = perturb(value, hint)
            except Cannot as exc:
                results.append(Result(fpath, type(o).__name__, f.name, "unexercised", f"synthesis failed: {exc}"))
                continue
            object.__setattr__(o, f.name, new)
            try:
                after = digest()
                if after is None:
                    status, reason = "unexercised", "hashing raised on a type-correct value"
                else:
                    status, reason = ("covered" if after != ref else "unhashed"), ""
                results.append(Result(fpath, type(o).__name__, f.name, status, reason))
                if inserted is not None:  # probe the synthesized record's own fields while it is installed
                    extra = cache_holders(inserted)
                    holders.extend(extra)
                    try:
                        visit(inserted, fpath + "[]", depth + 1, seen, after)  # the installed record is part of the reference digest
                    finally:
                        del holders[len(holders) - len(extra):]
            finally:
                object.__setattr__(o, f.name, value)

    def _recurse_existing(value: Any, fpath: str, depth: int, seen: set, ref: Optional[str]) -> None:
        if isinstance(value, dict):
            items = list(value.values())
        elif isinstance(value, (list, tuple, collections.deque)):
            items = list(value)
        else:
            return
        for item in items[:1]:
            if _is_instance(item):
                visit(item, fpath + "[]", depth + 1, seen, ref)

    base[0] = digest()
    visited: List[Any] = []  # keeps every visited object alive for the whole probe: ``seen`` holds ids, and a freed synthesized record's id can be handed to the next one
    visit(state, "state", 0, set(), base[0])
    return results


def build_samples() -> List[Tuple[str, Any]]:
    """The fixed sample states; each kernel is shut down and its run directory removed by id."""
    from src.config.profiles import PROD_SMALL
    from src.engine.executor import LocalSequentialExecutor
    from src.engine.kernel import Kernel
    from src.platform.rng import DeterministicRNG
    from tests.helpers.kernel_pinning import PinnedNormalGovernor
    from tests.helpers.scenario import compile_world

    out = []
    for world, seed, ticks in SAMPLES:
        state = compile_world(world, seed)
        if ticks:
            run_id = f"digest_probe_{world}_{seed}"
            kernel = Kernel(PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state, DeterministicRNG(seed), governor=PinnedNormalGovernor(),
                            executor=LocalSequentialExecutor(), flags={"audit_mode": True, "no_frame_pacing": True}, run_id=run_id)
            try:
                for _ in range(ticks):
                    kernel.tick_once()
                state = kernel.state
            finally:
                kernel.shutdown()
                shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)
        out.append((f"{world}:s{seed}:t{ticks}", state))
    return out


def merge(per_sample: List[List[Result]]) -> Dict[str, Result]:
    """One result per path across the samples: covered or unhashed beat unexercised; a disagreement keeps ``unhashed`` and says so."""
    merged: Dict[str, Result] = {}
    for results in per_sample:
        for r in results:
            old = merged.get(r.path)
            if old is None or (old.status == "unexercised" and r.status != "unexercised"):
                merged[r.path] = r
            elif old.status != r.status and "unexercised" not in (old.status, r.status):
                merged[r.path] = Result(r.path, r.owner, r.field, "unhashed", "samples disagree: " + old.status + " vs " + r.status)
    return merged
