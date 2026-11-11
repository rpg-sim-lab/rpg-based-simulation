"""Reads, statically derived from a step's source and NOT observed at runtime (no read-proxy: rpg-planner ruling 2026-11-10, Q2).

For the entry callable of a step, the names accessed as ``<state>.<name>`` or ``getattr(<state>, "<name>", ...)``, where ``<state>`` is the parameter named ``state`` (else the
first parameter after self/cls). The scan is NOT transitive: a read made by a helper the entry calls is not seen, so the set is a lower bound."""
from __future__ import annotations

import ast
import importlib
import inspect
import textwrap
from typing import Any, FrozenSet, Optional


def resolve(entry: str) -> Any:
    """``"pkg.module:Class.method"`` to the callable (a staticmethod resolves to the function)."""
    mod_name, qual = entry.split(":")
    obj: Any = importlib.import_module(mod_name)
    for part in qual.split("."):
        obj = inspect.getattr_static(obj, part) if inspect.isclass(obj) else getattr(obj, part)
        if isinstance(obj, (staticmethod, classmethod)):
            obj = obj.__func__
    return obj


def static_state_reads(entry: str) -> FrozenSet[str]:
    """The statically derived reads of ``entry`` (see the module docstring for what that does and does not cover)."""
    func = resolve(entry)
    tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    fn = next(n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
    params = [a.arg for a in fn.args.args if a.arg not in ("self", "cls")]
    name: Optional[str] = "state" if "state" in params else (params[0] if params else None)
    if name is None:
        return frozenset()
    reads = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == name and isinstance(node.ctx, ast.Load):
            reads.add(node.attr)
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr" and len(node.args) >= 2
              and isinstance(node.args[0], ast.Name) and node.args[0].id == name and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str)):
            reads.add(node.args[1].value)
    return frozenset(reads)
