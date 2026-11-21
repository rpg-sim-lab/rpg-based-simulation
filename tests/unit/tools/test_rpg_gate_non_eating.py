"""TCK-20261121-RPG-GATE-METRICS-REJECT-A-NON-EATING-KIND-GROUP-AS-UNDECLARED: the config's non-eating declaration is strict, reaches the metric module's compute and pool
as an argument, rides into the seed document, and is printed per cell by the report."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
import yaml

from tools.test_architecture import rpg_gate_harness as h
from tools.test_architecture import rpg_gate_report as rep
from tools.test_architecture.rpg_gate_baseline import BaselineError, GateConfig, load_config

CONFIG = Path("tests/simulation_quality/rpg_gate/config.yaml")
DECL = {"none": {"food_metrics": "not_applicable"}}


def _config_file(tmp_path, **extra) -> Path:
    data = {"worlds": ["w"], "seeds": [1], "ticks": 10, "stale_after_days": 30, **extra}
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_the_shipped_config_declares_the_group_none_as_non_eating_with_its_food_rows_not_applicable():
    assert load_config(CONFIG).non_eating == DECL


def test_a_config_without_the_key_declares_nothing(tmp_path):
    assert load_config(_config_file(tmp_path)).non_eating == {}


@pytest.mark.parametrize("bad", [
    ["none"],                                            # not a mapping
    {"meat": {"food_metrics": "not_applicable"}},        # an unknown group
    {"none": {}},                                        # no exclusion
    {"none": "not_applicable"},                          # a malformed entry
    {"none": {"hunger_metrics": "not_applicable"}},      # an unknown exclusion
    {"none": {"food_metrics": "applicable"}},            # an unknown value
])
def test_a_malformed_or_unknown_declaration_raises(tmp_path, bad):
    with pytest.raises(BaselineError, match="non_eating_kind_groups"):
        load_config(_config_file(tmp_path, non_eating_kind_groups=bad))


def test_the_child_arguments_carry_the_declaration_only_when_there_is_one():
    assert h._non_eating_args(GateConfig(("w",), (1,), 10, 30)) == []
    assert h._non_eating_args(GateConfig(("w",), (1,), 10, 30, non_eating=DECL)) == ["--non-eating", '{"none": {"food_metrics": "not_applicable"}}']


def test_the_run_child_hands_the_declaration_to_compute_and_pool_and_writes_the_doc_key(tmp_path, monkeypatch):
    from tools.test_architecture import rpg_gate_run as run

    seen = {}

    def compute(artifacts, non_eating=None):
        seen["compute"] = non_eating
        return {"metrics": [], "not_applicable": {g: ["O1.starved"] for g in non_eating}}

    def pool(docs, non_eating=None):
        seen["pool"] = non_eating
        return []

    monkeypatch.setattr(run, "_resolve", lambda spec, attr: compute if attr == "compute" else pool)
    monkeypatch.setattr(run, "build_kernel", lambda *a: type("K", (), {"state": None, "tick_once": lambda s: None, "shutdown": lambda s: None})())
    monkeypatch.setattr(run, "runner_header", lambda d: {})
    monkeypatch.setattr(run, "_peak_rss_mb", lambda: 0.0)
    out = tmp_path / "doc.json"
    common = ["--world", "w", "--metrics-module", "m", "--sha", "s", "--harness-hash", "h", "--out", str(out), "--ticks", "0", "--non-eating", '{"none": {"food_metrics": "not_applicable"}}']
    assert run.main(["run", *common, "--seed", "1", "--run-id", "r", "--seeds", "1"]) == 0
    assert seen["compute"] == DECL
    import json

    assert json.loads(out.read_text())["not_applicable"] == {"none": ["O1.starved"]}  # the doc key is the config declaration's groups
    pooled = tmp_path / "pooled.json"
    common[common.index(str(out))] = str(pooled)
    assert run.main(["pool", *common, "--docs", str(out), "--seeds", "1"]) == 0
    assert seen["pool"] == DECL


def test_the_report_prints_the_not_applicable_groups_per_world():
    doc = {"schema": "rpg-gate-metrics/v1", "status": "ok", "harness_hash": "h", "world": "w", "seed": 1, "metrics": [], "not_applicable": {"none": ["O1.starved", "O4.accepted", "O1.at_risk"]}}
    report = rep.build_report(GateConfig(("w",), (1,), 10, 30), {("w", 1): doc}, None, {}, [], dt.date(2026, 11, 21))
    assert report["not_applicable"] == {"w": {"none": ["O1.at_risk", "O1.starved", "O4.accepted"]}}
    assert "Not applicable in w: kind group `none` has no O1.at_risk, O1.starved, O4.accepted rows (declared non-eating)" in rep.render_markdown(report)


def test_the_harness_hash_covers_the_config_and_the_metric_module_but_not_the_baseline_or_report_tooling():
    assert "tools/test_architecture/rpg_gate_run.py" in h._HARNESS_SOURCES and "tools/test_architecture/rpg_gate_harness.py" in h._HARNESS_SOURCES
    assert not any(src.endswith(("rpg_gate_baseline.py", "rpg_gate_report.py")) for src in h._HARNESS_SOURCES)


# ------------------------------------------------------------------------------------------------ R2's scope (a stop line's `when`)
from tools.test_architecture import rpg_gate_baseline as rgb  # noqa: E402

R2 = rgb.StopLine("R2", "O2.seeds_with_survivors", "*", min=1, when_row="O2.t0_population", when_min=1.0)


def _pooled(rid, group, value):
    return {"id": rid, "class": "outcome", "scope": "pooled", "world": "w", "group": group, "value": value}


def test_a_group_first_seen_after_t0_does_not_cross_r2_but_a_group_present_at_t0_does():
    rows = [_pooled("O2.seeds_with_survivors", "none", 0.0), _pooled("O2.t0_population", "none", 0.0)]
    assert rgb.stop_lines_crossed(rows, [R2]) == []
    rows = [_pooled("O2.seeds_with_survivors", "meat", 0.0), _pooled("O2.t0_population", "meat", 4.0)]
    assert rgb.stop_lines_crossed(rows, [R2]) == ["R2"]


def test_a_missing_scope_row_fails_closed_and_the_line_applies():
    assert rgb.stop_lines_crossed([_pooled("O2.seeds_with_survivors", "none", 0.0)], [R2]) == ["R2"]


@pytest.mark.parametrize("when", [{"row": "O2.t0_population"}, {"min": 1}, {"row": 3, "min": 1}, {"row": "O2.t0_population", "min": "1"}, {"row": "O2.t0_population", "min": 1, "x": 2}, "O2.t0_population"])
def test_a_malformed_stop_line_scope_raises(tmp_path, when):
    path = _config_file(tmp_path, stop_lines=[{"name": "R2", "metric": "O2.seeds_with_survivors", "min": 1, "when": when}])
    with pytest.raises(BaselineError, match="malformed when"):
        load_config(path)


def test_the_shipped_r2_is_scoped_to_groups_with_members_at_the_start():
    (line,) = load_config(CONFIG).stop_lines
    assert (line.name, line.when_row, line.when_min) == ("R2-kind-extinct-in-all-seeds", "O2.t0_population", 1.0)


def _pop(group, series):
    return [{"id": "O2.population", "class": "outcome", "scope": "run", "world": "w", "group": group, "tick": t, "value": v} for t, v in series]


def test_the_report_lists_the_groups_first_seen_after_t0_with_peak_and_end_and_no_group_that_was_there_from_the_start():
    metrics = _pop("none", [(1, 0), (100, 3), (200, 5), (300, 2)]) + _pop("meat", [(1, 4), (300, 4)]) + _pop("plant", [(1, 0), (300, 0)])
    doc = {"schema": "rpg-gate-metrics/v1", "status": "ok", "harness_hash": "h", "world": "w", "seed": 42, "metrics": metrics}
    report = rep.build_report(GateConfig(("w",), (42,), 300, 30), {("w", 42): doc}, None, {}, [], dt.date(2026, 11, 21))
    assert report["first_seen_after_t0"] == {"w": {"42": {"none": {"peak": 5.0, "end": 2.0}}}}
    assert "First seen after t0 in w (report-only): s42 `none` peak 5, end 2" in rep.render_markdown(report)
