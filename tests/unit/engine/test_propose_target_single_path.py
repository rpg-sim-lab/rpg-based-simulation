"""F2 v2.2 D2 (owner scope #715 7062303482): every writer of a PLACE target goes through ``propose_target`` (or a function built on it).

A source test, not a behaviour test: it parses ``src/`` and finds every call that passes ``target_set=<non-None>`` (a ``NavigationUpdate`` or a ``replace`` of one). The guard is tied to the WRITTEN VALUE
(rpg-designer, G6): a write is guarded only when

 (a) the value is itself a vetted destination: a call of `propose_target`, `retreat_destination` or `_open_or_none` (a refused candidate is None), `_destination_or_hold` around such a call, or a
     conditional whose branches are all vetted, None, or the subject's own position (a hold);
 (b) the value is a Name whose latest assignment before the write is such a vetted value;
 (c) the write sits in an ``if``/conditional expression whose test calls a guard (`propose_target`, `destination_open`, `destination_suppressed`, `suppressed_move_to`) on the same expression as the value
     (``ast.dump`` equality), in its body or its else; or it is dominated by an earlier ``if <guard on the same expression>: return`` in the same block.

A target equal to the subject's own position is a hold, allowed by value. Builders that take the target as an argument (`regroup_to_town_update`, `stalemate_break_update`, `_retreat`, `_walk_to`) are allowed
per function, and every call site of each is held to the same rule. ``StrategicRedirectionSystem.enforce`` is not wired into the pipeline (the fused pass owns the bridge): allowed per function, with a test
that says so. A planted unguarded write must be caught: `test_the_mutants_are_caught` runs synthetic sources through the same checker.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[3]
VALUE_GUARDS = {"propose_target", "retreat_destination", "_open_or_none"}
TEST_GUARDS = {"propose_target": 1, "destination_open": 1, "destination_suppressed": 1, "suppressed_move_to": 2}  # name -> index of the checked expression
BUILDERS = {  # builder function -> index of the target argument at its call sites
    "regroup_to_town_update": 2, "stalemate_break_update": 2, "_retreat": 1, "_walk_to": 1,
}
BUILDER_DEFS = {
    ("src/strategy/destination_suppression.py", "regroup_to_town_update"),
    ("src/engine/tactical_hold.py", "stalemate_break_update"),
    ("src/engine/tactical_avoid.py", "_retreat"),
    ("src/engine/tactical_objective.py", "_walk_to"),
}
UNWIRED = {("src/systems/strategic_systems/redirection.py", "enforce")}


def _name(call: ast.Call) -> Optional[str]:
    f = call.func
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None


def _is_own_position(e: ast.AST) -> bool:
    return isinstance(e, ast.Attribute) and e.attr == "position" and isinstance(e.value, ast.Attribute) and e.value.attr == "navigation"


def _enclosing_function(node: ast.AST, parents: Dict[ast.AST, ast.AST]) -> Optional[ast.AST]:
    cur = node
    while cur in parents:
        cur = parents[cur]
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cur
    return None


def _latest_assignment(name: str, func: ast.AST, before: int) -> Optional[Tuple[int, ast.AST]]:
    best: Optional[Tuple[int, ast.AST]] = None
    for st in ast.walk(func):
        hit = (isinstance(st, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in st.targets)) or (
            isinstance(st, ast.NamedExpr) and isinstance(st.target, ast.Name) and st.target.id == name)
        if hit and st.lineno < before and (best is None or st.lineno > best[0]):
            best = (st.lineno, st.value)
    return best


def _value_ok(e: ast.AST, func: Optional[ast.AST], before: int, depth: int = 0) -> bool:
    if depth > 4:
        return False
    if (isinstance(e, ast.Constant) and e.value is None) or _is_own_position(e):
        return True
    if isinstance(e, ast.Call):
        n = _name(e)
        if n in VALUE_GUARDS:
            return True
        return n == "_destination_or_hold" and len(e.args) >= 2 and _value_ok(e.args[1], func, before, depth + 1)
    if isinstance(e, ast.IfExp):
        return _value_ok(e.body, func, before, depth + 1) and _value_ok(e.orelse, func, before, depth + 1)
    if isinstance(e, ast.Name) and func is not None:
        best = _latest_assignment(e.id, func, before)
        return best is not None and _value_ok(best[1], func, best[0], depth + 1)
    return False


def _guard_dumps(test: ast.AST) -> List[str]:
    out = []
    for n in ast.walk(test):
        if isinstance(n, ast.Call) and _name(n) in TEST_GUARDS and len(n.args) > TEST_GUARDS[_name(n)]:
            out.append(ast.dump(n.args[TEST_GUARDS[_name(n)]]))
    return out


def _guarded(node: ast.AST, value: ast.AST, parents: Dict[ast.AST, ast.AST]) -> bool:
    func = _enclosing_function(node, parents)
    if _value_ok(value, func, node.lineno):
        return True
    want = ast.dump(value)
    cur = node
    while cur in parents and cur is not func:
        parent = parents[cur]
        if isinstance(parent, (ast.If, ast.IfExp)) and want in _guard_dumps(parent.test):
            return True
        for block in (getattr(parent, "body", None), getattr(parent, "orelse", None)):
            if isinstance(block, list) and cur in block:  # an earlier `if <guard on the same expression>: return` in the same block dominates the write
                for stmt in block[: block.index(cur)]:
                    if isinstance(stmt, ast.If) and want in _guard_dumps(stmt.test) and stmt.body and isinstance(stmt.body[-1], (ast.Return, ast.Raise)):
                        return True
        cur = parent
    return False


def _parse(source: str) -> Tuple[ast.AST, Dict[ast.AST, ast.AST]]:
    tree = ast.parse(source)
    parents: Dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return tree, parents


def unguarded_writes(path: str, source: str) -> List[Tuple[str, str, int]]:
    """Every ``target_set=<non-None>`` write in ``source`` that is not guarded by value, and every call of a builder whose target argument is not guarded."""
    tree, parents = _parse(source)
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = _enclosing_function(node, parents)
        fname = func.name if func is not None else "<module>"
        kws = {k.arg: k for k in node.keywords if k.arg}
        tg = kws.get("target_set")
        if tg is not None and not (isinstance(tg.value, ast.Constant) and tg.value.value is None):
            if (path, fname) not in BUILDER_DEFS and (path, fname) not in UNWIRED and not _guarded(node, tg.value, parents):
                found.append((path, fname, node.lineno))
        n = _name(node)
        if n in BUILDERS and len(node.args) > BUILDERS[n] and (path, fname) not in BUILDER_DEFS and not _guarded(node, node.args[BUILDERS[n]], parents):
            found.append((path, f"{fname} -> {n}", node.lineno))
    return found


def _all_src_findings() -> List[Tuple[str, str, int]]:
    out: List[Tuple[str, str, int]] = []
    for p in sorted((REPO / "src").rglob("*.py")):
        out += unguarded_writes(str(p.relative_to(REPO)).replace("\\", "/"), p.read_text(encoding="utf-8"))
    return out


def test_every_place_target_writer_is_guarded_by_its_value():
    assert _all_src_findings() == [], "a place target is written without a guard on that very value (propose_target / destination_open ...)"


def test_the_allowed_lists_name_live_functions_and_the_redirection_system_is_not_wired():
    for fpath, fname in sorted(BUILDER_DEFS | UNWIRED):
        tree = ast.parse((REPO / fpath).read_text(encoding="utf-8"))
        assert any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == fname for n in ast.walk(tree)), f"{fpath}::{fname} is gone: drop it from the allowed lists"
    assert "StrategicRedirectionSystem" not in (REPO / "src/engine/pipeline.py").read_text(encoding="utf-8"), "the redirection system is wired: it can no longer be allowed per function"
    texts = [p.read_text(encoding="utf-8") for p in (REPO / "src").rglob("*.py")]
    for name in BUILDERS:  # a builder with no call site is dead: say so
        assert sum(t.count(f"{name}(") - t.count(f"def {name}(") for t in texts) > 0, f"builder {name} has no call site"


# --- the mutants the designer planted (M1-M4) must all be caught -----------------------------------------------------------------------------------
_M1 = """
def evaluate_entity_intent(entity, state):
    if propose_target(entity, (1.0, 1.0), state.tick) is not None:
        pass
    return EntityUpdate(entity_id=entity.id, navigation=NavigationUpdate(target_set=(5.0, 5.0)))
"""
_M2 = """
def fused(entity, state, coords):
    if destination_open(entity, coords, state.tick):
        pass
    other = (7.0, 7.0)
    return replace(ent, navigation=replace(nav, target_set=other))
"""
_M3 = """
def brand_new_writer(entity, pos):
    return EntityUpdate(entity_id=entity.id, navigation=NavigationUpdate(target_set=pos))
"""
_M4 = """
def late(entity, tick):
    ok = propose_target(entity, (1.0, 1.0), tick)
    if ok is None:
        return None
    return NavigationUpdate(target_set=(5.0, 5.0))
"""
_GUARDED = {
    "value": "def f(entity, t):\n    return NavigationUpdate(target_set=propose_target(entity, (5.0, 5.0), t))\n",
    "name": "def f(entity, t):\n    where = retreat_destination(s, entity, th)\n    return NavigationUpdate(target_set=where)\n",
    "if": "def f(entity, pos, t):\n    if pos and propose_target(entity, pos, t) is not None:\n        return NavigationUpdate(target_set=pos)\n",
    "else": "def f(entity, pos, t):\n    if propose_target(entity, pos, t) is None:\n        return None\n    else:\n        return NavigationUpdate(target_set=pos)\n",
    "early return": "def f(entity, pos, t):\n    if propose_target(entity, pos, t) is None:\n        return None\n    return NavigationUpdate(target_set=pos)\n",
    "own position hold": "def f(entity):\n    return NavigationUpdate(target_set=entity.navigation.position)\n",
}


def test_the_mutants_are_caught():
    for label, src in (("M1 late write in a big function", _M1), ("M2 other value after a guard on another", _M2), ("M3 new function", _M3), ("M4 guard on (1,1), write (5,5)", _M4)):
        assert unguarded_writes("src/x.py", src), f"{label} was not caught"


def test_the_checker_accepts_each_guarded_form():
    for label, src in _GUARDED.items():
        assert unguarded_writes("src/x.py", src) == [], f"a guarded write ({label}) was flagged"


def test_a_builder_call_with_an_unguarded_target_is_caught():
    bad = "def f(entity, pos):\n    return _walk_to(entity, pos)\n"
    ok = "def f(entity, pos, t):\n    if propose_target(entity, pos, t) is None:\n        return None\n    return _walk_to(entity, pos)\n"
    assert unguarded_writes("src/x.py", bad) and unguarded_writes("src/x.py", ok) == []
