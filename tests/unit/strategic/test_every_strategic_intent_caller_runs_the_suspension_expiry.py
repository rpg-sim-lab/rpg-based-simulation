"""N10 (divergence 2.212, rpg-designer ruling A): the suspension expiry pass runs in the CALLERS of `evaluate_strategic_intent`, through the one helper
`evaluate_strategic_intent_with_expiry`, so the evaluation itself keeps its name and body. Every production call site of `evaluate_strategic_intent` in src must therefore be the helper's own
delegation, or sit in a function that has no production caller (named below, with why). A new direct call fails here until it goes through the helper."""
from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[3] / "src"
EVAL = "evaluate_strategic_intent"
HELPER = "evaluate_strategic_intent_with_expiry"
#: Functions that may call `evaluate_strategic_intent` directly. The helper itself is the delegation. `evaluate_all_strategic_intents` has no production caller (only tests call it; the pipeline
#: runs `fused_strategic_pass`), so it is not wired; a deeper-issue candidate filed with the N10 PR.
ALLOWED_DIRECT = {HELPER, "evaluate_all_strategic_intents"}


def _calls(tree: ast.AST, name: str):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == name:
            yield node


def _enclosing(tree: ast.AST):
    """call node -> name of the function that contains it."""
    out = {}
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for call in _calls(fn, EVAL):
                out[id(call)] = fn.name
    return out


def test_every_direct_call_of_evaluate_strategic_intent_in_src_is_the_helper_or_the_unwired_path():
    offenders = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        owner = _enclosing(tree)
        for call in _calls(tree, EVAL):
            fn = owner.get(id(call))
            if fn not in ALLOWED_DIRECT:
                offenders.append(f"{path.relative_to(SRC.parent)}:{call.lineno} in {fn}")
    assert offenders == [], "call evaluate_strategic_intent_with_expiry instead (the suspension expiry pass must run first): " + "; ".join(offenders)


def test_the_production_strategic_pass_calls_the_helper():
    tree = ast.parse((SRC / "systems/strategic_systems/intelligence.py").read_text(encoding="utf-8"))
    callers = {fn.name for fn in ast.walk(tree) if isinstance(fn, ast.FunctionDef) and any(True for _ in _calls(fn, HELPER))}
    assert "fused_strategic_pass" in callers


def test_the_helper_runs_the_expiry_before_it_calls_the_evaluation():
    tree = ast.parse((SRC / "systems/strategic_systems/intelligence.py").read_text(encoding="utf-8"))
    helper = next(fn for fn in ast.walk(tree) if isinstance(fn, ast.FunctionDef) and fn.name == HELPER)
    expiry = min(c.lineno for c in _calls(helper, "suspension_expiry_update"))
    evaluation = min(c.lineno for c in _calls(helper, EVAL))
    assert expiry < evaluation
