"""Static scan of src/: a construction of AuthoritativeState, or a `replace` that sets `groups=`, must pass `next_group_id=` too.

The counter defaults to 10000 and nothing seeds it at construction, so a builder that hands a state groups without the counter would leave it behind the
store. Exemptions, by name only: `to_readonly` (a view copy of an existing state; it passes `groups=` wrapped read-only and keeps the counter). A `replace`
that does not pass `groups=` merely carries the groups and the counter and is not flagged. The apply copy passes both. Today the list of offenders is empty."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import List, Tuple

SRC = Path(__file__).resolve().parents[3] / "src"
EXEMPT_FUNCTIONS = {"to_readonly"}


def _offenders(source: str, label: str) -> List[Tuple[str, int]]:
    tree = ast.parse(source)
    found: List[Tuple[str, int]] = []

    def visit(node: ast.AST, func: str) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func = node.name
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            keys = {k.arg for k in node.keywords}
            if name in ("AuthoritativeState", "replace") and "groups" in keys and "next_group_id" not in keys and func not in EXEMPT_FUNCTIONS:
                found.append((label, node.lineno))
        for child in ast.iter_child_nodes(node):
            visit(child, func)

    visit(tree, "")
    return found


def test_no_src_builder_supplies_groups_without_the_counter():
    offenders: List[Tuple[str, int]] = []
    for path in sorted(SRC.rglob("*.py")):
        offenders += _offenders(path.read_text(encoding="utf-8"), str(path.relative_to(SRC)))
    assert offenders == []


def test_the_scan_fails_on_a_planted_bad_source_and_passes_the_good_forms():
    """Positive control: the scan must see a constructor and a replace that give groups without the counter."""
    bad = "def build(s, g):\n    a = AuthoritativeState(tick=0, seed=1, groups=g)\n    return replace(s, groups=g)\n"
    assert [line for _, line in _offenders(bad, "planted")] == [2, 3]
    good = (
        "def build(s, g):\n    a = AuthoritativeState(tick=0, seed=1, groups=g, next_group_id=10001)\n    return replace(s, tick=2)\n"
        "def to_readonly(s, g):\n    return replace(s, groups=g)\n"
    )
    assert _offenders(good, "planted") == []
