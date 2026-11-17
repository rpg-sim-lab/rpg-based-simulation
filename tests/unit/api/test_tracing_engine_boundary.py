"""No simulation-side module imports opentelemetry (issue #622, R3): tracing lives in src/api only."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
GUARDED = ("src/engine", "src/core", "src/systems", "src/domains")


def opentelemetry_imports(root: Path) -> list[str]:
    """Every `file:line` under `root` that imports opentelemetry (any form, any depth)."""
    found = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""] if isinstance(node, ast.ImportFrom) else []
            if any(n == "opentelemetry" or n.startswith("opentelemetry.") for n in names):
                found.append(f"{path}:{node.lineno}")
    return found


@pytest.mark.parametrize("package", GUARDED)
def test_no_opentelemetry_import(package):
    assert (REPO / package).is_dir()
    assert opentelemetry_imports(REPO / package) == []


def test_scanner_sees_a_planted_import(tmp_path):
    (tmp_path / "a.py").write_text("def f():\n    from opentelemetry import trace\n")
    (tmp_path / "b.py").write_text("import opentelemetry.sdk.trace\n")
    (tmp_path / "c.py").write_text("import json\n")
    assert len(opentelemetry_imports(tmp_path)) == 2
