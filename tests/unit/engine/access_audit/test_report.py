"""The report generator turns audit JSON into table rows (pure: paths in, text out) and fills every count field."""
from __future__ import annotations

import json

from src.engine.access_audit import report
from src.engine.access_audit.declarations import DECLARATIONS, StepDeclaration

_ROWS = {
    "alpha": StepDeclaration("alpha", None, frozenset(), frozenset({"eu:combat"}), "first_pass", False),
    "self_model": StepDeclaration("self_model", None, frozenset(), frozenset(), "first_pass", False),
}
_CELL = {
    "world": "w", "seed": 1, "observations": 7, "wall_s_not_a_measurement": 1.5,
    "timeline_content_sampled": {"every_ticks": 100, "samples": 2, "findings": []},
    "per_phase": {"alpha": {
        "ticks_run": 3, "writes": ["eu:combat", "eu:social"], "inplace_update_mutations": ["su:world_updates"],
        "hidden_state_mutations": ["route_plans", "other"], "promote": ["other"], "hidden_ticks": {"route_plans": 3, "other": 1},
        "global_ticks": {"m:attr": 2}, "created_entries_ticks": 2, "created_entries_max": 4, "fanout_max": {"eu:combat": 5},
        "identity_only": ["eu:combat"], "unsafe_equality": [],
    }},
}


def _text(tmp_path, cells=None):
    paths = []
    for i, cell in enumerate(cells or [_CELL]):
        p = tmp_path / f"c{i}.audit.json"
        p.write_text(json.dumps(cell))
        paths.append(str(p))
    return report.render(report.load_cells(paths), _ROWS)


def test_rows_for_each_section_and_no_unfilled_template_field(tmp_path):
    text = _text(tmp_path)
    assert "| w s1 | 7 | 1 | 1.5 |" in text
    assert "| self_model | ENABLE_SELF_MODEL_COGNITION |" in text
    assert "| alpha | eu:social |" in text and "1 of 1 observed steps write something their declaration does not list." in text
    assert "| alpha | route_plans (3 ticks) |" in text and "| alpha | other (1 ticks) |" in text
    assert "| alpha | m:attr (2 ticks) |" in text
    assert "| alpha | 2 | 4 | eu:combat (5) |" in text
    assert "| alpha | su:world_updates |" in text and "| alpha | eu:combat | - |" in text
    assert "2 samples every 100 ticks, 0 finding(s)" in text
    assert "{" not in text.replace("{}", "")


def test_two_cells_sum_ticks_and_max_the_maxima(tmp_path):
    text = _text(tmp_path, [_CELL, _CELL])
    assert "route_plans (6 ticks)" in text and "| alpha | 2 | 4 | eu:combat (5) |" not in text and "| alpha | 4 | 4 | eu:combat (5) |" in text


def test_no_global_change_prints_the_none_detected_line(tmp_path):
    cell = json.loads(json.dumps(_CELL))
    cell["per_phase"]["alpha"]["global_ticks"] = {}
    assert "No process-global change detected" in _text(tmp_path, [cell])


def test_every_declared_step_is_either_observed_or_listed_unobserved():
    text = report.render([{"world": "w", "seed": 0, "observations": 0, "per_phase": {}}])
    assert all(name in text for name in DECLARATIONS)
