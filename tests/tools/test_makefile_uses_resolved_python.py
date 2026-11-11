"""Makefile recipes run Python through $(PYTHON3), never a bare `python3` from PATH.

A bare `python3` is the system interpreter whenever the venv is not activated, so targets fail
with `No module named 'pydantic'` (owner repro, main 03ad89589). `$(PYTHON3)` (Makefile, near
line 51) resolves to the first interpreter that can import pydantic, .venv first.
"""

import re
from pathlib import Path

_MAKEFILE = Path(__file__).resolve().parents[2] / "Makefile"
# `python3` as a command word: not part of a path (.venv/bin/python3), a variable or a longer name.
_BARE_PYTHON3 = re.compile(r"(?<![\w/.$(-])python3(?=\s)")
# uv selects its own environment, so `uv run python3` is correct as written.
_ALLOWED = re.compile(r"\buv run python3\b")


def bare_python3_recipe_lines(text: str) -> list[str]:
    """`<line>: <text>` for each recipe line (tab-led) that runs a bare `python3`."""
    hits = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.startswith("\t"):
            continue
        if _BARE_PYTHON3.search(_ALLOWED.sub("", line)):
            hits.append(f"{number}: {line.strip()}")
    return hits


def test_no_makefile_recipe_runs_a_bare_python3():
    hits = bare_python3_recipe_lines(_MAKEFILE.read_text(encoding="utf-8"))
    assert hits == [], (
        f"{len(hits)} Makefile recipe line(s) run a bare `python3`; use `$(PYTHON3)` instead:\n"
        + "\n".join(hits)
    )


def test_the_check_catches_each_bare_form_and_allows_the_resolved_ones():
    text = (
        "PYTHON3 := $(shell for py in .venv/bin/python3 python3; do echo $$py; done)\n"
        "a:\n\tpython3 -m pytest tests/\n"
        "b:\n\t@python3 tools/x.py\n"
        "c:\n\tFOO=1 python3 -m src cli\n"
        "d:\n\t$(PYTHON3) -m mypy src/ | python3 -m mypy_baseline filter\n"
        "e:\n\t$(PYTHON3) -m pytest tests/\n"
        "f:\n\tuv run python3 -m src serve\n"
        "g:\n\t\"$(KNOWLEDGE_MAIN_ROOT)/.venv/bin/python3\" -c 'pass'\n"
    )
    hits = bare_python3_recipe_lines(text)
    assert [h.split(":")[0] for h in hits] == ["3", "5", "7", "9"], hits
