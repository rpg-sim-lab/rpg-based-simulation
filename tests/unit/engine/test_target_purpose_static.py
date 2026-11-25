"""The #996 rework, step a2 (design docs/plans/systemic_world/experience_memory_design.md section 4): every place-target writer passes the purpose to the gate AND stores it with its target.

A source test over ``src/``. It checks three things, each with a planted mutant the checker must catch (`test_the_mutants_are_caught`):

 1. every call of a gate function (`propose_target`, `destination_open`, `destination_suppressed`, `suppression_anchors`, `retreat_destination`, `suppressed_move_to`, `_open_or_none`) and of a builder that
    writes a target from one (`regroup_to_town_update`, `_walk_to`, `_retreat`, `stalemate_break_update`) passes its ``purpose`` argument (the position the signature gives it);
 2. every ``target_set=<non-None>`` write names a ``target_purpose_set`` and a ``target_gated_set`` in the same call (a re-emission at the executor carries the stored pair; ``redirection.enforce`` is not wired);
 3. a ``target_purpose_set`` that is a Name is bound in the same function, by name identity with a gate call's purpose argument, from ``purpose_of`` / ``ungated_purpose`` / ``stored_purpose`` / ``_purpose_and_gated``,
    or is the function's own parameter (a builder). A literal or an unbound name is not accepted.

Limit: this checks the shape of the call, not the value reaching it; the behaviour is covered by tests/unit/strategic/test_target_purpose.py and the per-writer tests."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[3]
PURPOSE_ARG_INDEX = {  # callee -> index of its positional `purpose` argument
    "propose_target": 3, "destination_open": 3, "destination_suppressed": 3, "suppression_anchors": 3, "retreat_destination": 3, "suppressed_move_to": 4, "_open_or_none": 3,
    "regroup_to_town_update": 3, "_walk_to": 2, "_retreat": 4, "stalemate_break_update": 3,
}
BINDERS = {"purpose_of", "ungated_purpose", "stored_purpose", "_purpose_and_gated"}
UNWIRED = {("src/systems/strategic_systems/redirection.py", "enforce")}
DEFINITIONS = {name for name in PURPOSE_ARG_INDEX}  # a `def` of the same name is not a call


def _callee(call: ast.Call) -> Optional[str]:
    f = call.func
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None


def _enclosing(node: ast.AST, parents: Dict[ast.AST, ast.AST]) -> Optional[ast.AST]:
    cur = node
    while cur in parents:
        cur = parents[cur]
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cur
    return None


def _purpose_arg(call: ast.Call) -> Optional[ast.AST]:
    name = _callee(call)
    index = PURPOSE_ARG_INDEX[name]
    if len(call.args) > index:
        return call.args[index]
    return next((k.value for k in call.keywords if k.arg == "purpose"), None)


def _bound_names(func: ast.AST) -> set:
    """Names assigned (plain or tuple target) from a call of a binder, anywhere in ``func``."""
    found = set()
    for st in ast.walk(func):
        if isinstance(st, ast.Assign) and isinstance(st.value, ast.Call) and _callee(st.value) in BINDERS:
            for target in st.targets:
                found |= {n.id for n in ast.walk(target) if isinstance(n, ast.Name)}
    return found


def violations(path: str, source: str) -> List[Tuple[str, str, int, str]]:
    tree = ast.parse(source)
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    found: List[Tuple[str, str, int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = _enclosing(node, parents)
        fname = func.name if func is not None else "<module>"
        name = _callee(node)
        if name in PURPOSE_ARG_INDEX and fname != name and _purpose_arg(node) is None:
            found.append((path, fname, node.lineno, f"{name} called without its purpose"))
        kws = {k.arg: k.value for k in node.keywords if k.arg}
        target = kws.get("target_set")
        if target is None or (isinstance(target, ast.Constant) and target.value is None) or (path, fname) in UNWIRED:
            continue
        if "target_purpose_set" not in kws or "target_gated_set" not in kws:
            found.append((path, fname, node.lineno, "target_set written without target_purpose_set and target_gated_set"))
            continue
        value = kws["target_purpose_set"]
        if isinstance(value, ast.Call) and _callee(value) in BINDERS:
            continue
        if isinstance(value, ast.Name) and func is not None:
            params = {a.arg for a in func.args.args}
            gate_args = {a.id for c in ast.walk(func) if isinstance(c, ast.Call) and _callee(c) in PURPOSE_ARG_INDEX for a in [_purpose_arg(c)] if isinstance(a, ast.Name)}
            if value.id in params or value.id in _bound_names(func) or value.id in gate_args:
                continue
        found.append((path, fname, node.lineno, "target_purpose_set is not a bound purpose"))
    return found


def _src_files() -> List[Path]:
    return sorted(p for p in (REPO / "src").rglob("*.py"))


def test_every_gate_call_passes_a_purpose_and_every_target_write_stores_one():
    problems = []
    for p in _src_files():
        rel = str(p.relative_to(REPO))
        problems += violations(rel, p.read_text(encoding="utf-8"))
    assert not problems, f"{len(problems)} writers break the purpose rule: {problems[:8]}"


def test_the_mutants_are_caught():
    ok = (
        "def f(entity, tick):\n    purpose = purpose_of(entity, None, M)\n    if propose_target(entity, p, tick, purpose) is not None:\n"
        "        return NavigationUpdate(target_set=p, target_purpose_set=purpose, target_gated_set=True)\n"
    )
    assert violations("m.py", ok) == []
    no_arg = ok.replace("propose_target(entity, p, tick, purpose)", "propose_target(entity, p, tick)")
    assert any("without its purpose" in v[3] for v in violations("m.py", no_arg))
    no_store = ok.replace("target_purpose_set=purpose, ", "")
    assert any("without target_purpose_set" in v[3] for v in violations("m.py", no_store))
    no_flag = ok.replace(", target_gated_set=True", "")
    assert any("without target_purpose_set" in v[3] for v in violations("m.py", no_flag))
    unbound = ok.replace("purpose = purpose_of(entity, None, M)", "other = 1").replace("target_purpose_set=purpose", "target_purpose_set=mystery")
    assert any("not a bound purpose" in v[3] for v in violations("m.py", unbound))
    literal = ok.replace("target_purpose_set=purpose", "target_purpose_set=None")
    assert any("not a bound purpose" in v[3] for v in violations("m.py", literal))
    builder = "def _walk(entity, pos, purpose):\n    return NavigationUpdate(target_set=pos, target_purpose_set=purpose, target_gated_set=True)\n"
    assert violations("m.py", builder) == []
    unpacked = "def g(entity):\n    purpose = purpose_of(entity)\n    stored_for, gated = _purpose_and_gated(entity, d, purpose, M)\n    return NavigationUpdate(target_set=p, target_purpose_set=stored_for, target_gated_set=gated)\n"
    assert violations("m.py", unpacked) == []
