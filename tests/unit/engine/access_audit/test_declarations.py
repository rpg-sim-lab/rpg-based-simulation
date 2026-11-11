"""Every step dispatched through pipeline.run_phase has a declaration, and each declaration's statically derived reads are pinned.

Reads here are "statically derived, not observed" (no read-proxy; rpg-planner ruling 2026-11-10): a lower bound taken from the entry function only."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.engine.access_audit.declarations import DECLARATIONS
from src.engine.access_audit.static_reads import resolve, static_state_reads

_PIPELINE = Path("src/engine/pipeline.py").read_text(encoding="utf-8")
_STEPS = tuple(re.findall(r'run_phase\(\s*"([a-z_0-9]+)"', _PIPELINE))


def test_every_run_phase_step_has_exactly_one_declaration_and_no_declaration_is_stale():
    assert len(set(_STEPS)) == len(_STEPS)
    assert set(_STEPS) == set(DECLARATIONS)


@pytest.mark.parametrize("name", sorted(DECLARATIONS))
def test_entry_resolves_and_its_static_reads_equal_the_pinned_reads(name):
    decl = DECLARATIONS[name]
    if decl.entry is None:
        assert not decl.reads_tick_start
        return
    assert callable(resolve(decl.entry))
    assert static_state_reads(decl.entry) == decl.reads_tick_start


def test_declared_writes_use_known_prefixes_and_a_known_source():
    for decl in DECLARATIONS.values():
        assert decl.writes, decl.name
        assert all(w.startswith(("eu:", "su:")) for w in decl.writes), decl.name
        assert decl.source in {"phase_graph", "feasibility_review_s2", "first_pass"}, decl.name
