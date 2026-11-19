"""Rerun only the rows main's latest gate report does not carry, and the "new vs main" diff (TCK-20261119-RPG-GATE-RERUN-ONLY-NEW-ROWS-AND-A-BASELINE-DIFF-AGAINST-MAIN).

The replay uses TRIMMED fixtures under tests/fixtures/rpg_gate_replay/ (each names its source run id): five recorded PR-run gate reports (44281112176, 44316977936,
44339505504, 44353267564, 44366629746) and one MAIN-run report (44323101062). Their findings stand in for the first pass (``evaluate`` is stubbed to return
them), so the replay exercises the rerun decision, the ownership carried on each row, the verdict and the diff, with no simulation.
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tools.test_architecture import rpg_gate_harness as harness
from tools.test_architecture import rpg_gate_main_report as mainrep
from tools.test_architecture import rpg_gate_report as rep
from tools.test_architecture.rpg_gate_baseline import GateConfig, References

FIX = Path(__file__).resolve().parents[2] / "fixtures" / "rpg_gate_replay"
PR_RUNS = ("44281112176", "44316977936", "44339505504", "44353267564", "44366629746")
WORLDS = ("crowded_frontier", "frontier_living_world", "urban_political")
SEEDS = (42, 43, 44, 45, 46)
TODAY = dt.date(2026, 11, 19)
HASH = "5a7f145920aab68597a09f72a7e97ea861ffa4cc927197a0d98b98ac5eb23920"


def _fix(name):
    return json.loads((FIX / f"{name}.json").read_text(encoding="utf-8"))


def _config():
    return GateConfig(worlds=WORLDS, seeds=SEEDS, ticks=5000, stale_after_days=30)


def _refs(fixture):
    by = {r["ref"]: {"version": r["version"], "milestone": r["milestone"]} for r in fixture["references"]}
    return References(last=by["last"], milestone_first=by["milestone-first"])


class _Rerun:
    def __init__(self):
        self.calls = []

    def __call__(self, pairs):
        self.calls.append(list(pairs))
        return {}


@pytest.fixture(autouse=True)
def _stub_evaluate_and_ownership(monkeypatch):
    """The recorded findings are the first pass; their ownership was recorded with them, so it is carried over instead of re-derived from today's known list."""
    state = {}
    calls = []

    def evaluate(*a, **k):
        calls.append(1)
        return copy.deepcopy(state["second"] if len(calls) > 1 and "second" in state else state["findings"])

    monkeypatch.setattr(rep, "evaluate", evaluate)
    monkeypatch.setattr(rep, "_ownership", lambda findings, known, today: findings)
    return state


def _run(stub, fixture, *, findings=None, main=None, fallback="", rerun=True):
    stub["findings"] = findings if findings is not None else fixture["findings"]
    rr = _Rerun() if rerun else None
    report = rep.build_report(_config(), {}, _refs(fixture), {}, [], TODAY, sha=fixture["sha"], harness_hash=HASH, rerun=rr, main=main, main_fallback=fallback)
    return report, rr


def _baseline_file(tmp_path, fixture, run_id="44323101062", **over):
    path = tmp_path / "main-baseline.json"
    report = {k: fixture[k] for k in ("schema", "sha", "harness_hash", "references", "findings")} | {"verdict": fixture["recorded"]["verdict"]}
    path.write_text(json.dumps({"run_id": run_id, "head_sha": fixture["sha"], "report": report} | over), encoding="utf-8")
    return path


def _main(tmp_path, **over):
    fixture = _fix("main-44323101062")
    base, why = rep.load_main_baseline(_baseline_file(tmp_path, fixture, **over), HASH, _refs(fixture))
    assert why == "" and base is not None
    return base


def _rows(report):
    return sorted(json.dumps({k: v for k, v in f.items() if k != "not_rerun"}, sort_keys=True) for f in report["findings"])


# ------------------------------------------------------------------ replay of the recorded reports


@pytest.mark.parametrize("run_id", PR_RUNS)
def test_replay_gives_the_same_verdict_rows_and_pass_fail_with_and_without_the_skip(run_id, tmp_path, _stub_evaluate_and_ownership):
    fixture = _fix(run_id)
    legacy, legacy_rr = _run(_stub_evaluate_and_ownership, fixture)  # today's behaviour: no main report, the full rerun
    skip, skip_rr = _run(_stub_evaluate_and_ownership, fixture, main=_main(tmp_path))
    assert legacy["verdict"] == skip["verdict"] == fixture["recorded"]["verdict"]
    assert sorted(legacy["reasons"]) == sorted(skip["reasons"]) == sorted(fixture["recorded"]["reasons"])  # the fixture is trimmed and re-sorted: compare as sets of lines
    assert _rows(legacy) == _rows(skip)
    assert legacy["counts"] == skip["counts"]
    assert [p for call in legacy_rr.calls for p in call] == sorted((w, s) for w in WORLDS for s in SEEDS)  # the full rerun of all 15 runs
    assert sum(len(c) for c in skip_rr.calls) < 15  # the skip reruns strictly fewer


def test_replay_of_the_latest_pr_run_reruns_only_the_pairs_behind_its_new_rows_and_names_them(tmp_path, _stub_evaluate_and_ownership):
    report, rr = _run(_stub_evaluate_and_ownership, _fix("44366629746"), main=_main(tmp_path))
    # Two rows are not in main's report: the V3 fail of flw/42 (reruns that seed) and urban_political's O2.population drift (an outcome row: every seed of its world).
    assert rr.calls == [[("frontier_living_world", 42)] + [("urban_political", s) for s in SEEDS]]
    new = report["vs_main"]["new"]
    assert sorted((f["id"], f["world"], f.get("seed"), f["state"]) for f in new) == [("O2.population", "urban_political", None, "drift"), ("V3", "frontier_living_world", 42, "fail")]
    assert {k: report["vs_main"]["source"][k] for k in ("run_id", "head_sha")} == {"run_id": "44323101062", "head_sha": _fix("main-44323101062")["sha"]}
    assert report["verdict"] == "red"  # the verdict is unchanged: an unowned fail is still red
    skipped = [f for f in report["findings"] if f.get("not_rerun")]
    assert skipped and all(f["not_rerun"] == "in main's report, run 44323101062" for f in skipped)
    assert all(f["state"] != "unstable" for f in skipped)
    assert not any(f.get("not_rerun") and (f["world"], f.get("seed")) == ("frontier_living_world", 42) for f in report["findings"] if f["scope"] == "run")  # that pair WAS rerun


# ------------------------------------------------------------------ the five cases


def test_no_new_row_means_no_rerun_and_new_vs_main_none(tmp_path, _stub_evaluate_and_ownership):
    fixture = _fix("main-44323101062")
    report, rr = _run(_stub_evaluate_and_ownership, fixture, main=_main(tmp_path))
    assert rr.calls == [] and report["rerun"]["performed"] is False
    assert report["vs_main"]["new"] == [] and report["vs_main"]["carried"] == report["counts"]["fail"] + report["counts"]["drift"]
    assert "New vs main: none" in rep.render_markdown(report)
    assert "run 44323101062" in rep.render_markdown(report) and "not rerun: in main's report, run 44323101062" in rep.render_markdown(report)
    assert report["verdict"] == fixture["recorded"]["verdict"]


def test_one_new_row_gets_its_confirming_rerun_for_its_pairs_only_and_appears_verbatim(tmp_path, _stub_evaluate_and_ownership):
    fixture = _fix("main-44323101062")
    extra = copy.deepcopy(next(f for f in _fix("44366629746")["findings"] if f["id"] == "V3"))
    report, rr = _run(_stub_evaluate_and_ownership, fixture, findings=fixture["findings"] + [extra], main=_main(tmp_path))
    assert rr.calls == [[("frontier_living_world", 42)]]
    assert report["vs_main"]["new"] == [extra]
    assert "New vs main: 1 row(s)" in rep.render_markdown(report) and "V3" in rep.render_markdown(report)


def test_a_carried_row_inside_a_pair_the_rerun_covers_is_read_from_the_second_pass(tmp_path, _stub_evaluate_and_ownership):
    fixture = _fix("main-44323101062")
    extra = copy.deepcopy(next(f for f in _fix("44366629746")["findings"] if f["id"] == "V3"))  # new: reruns (frontier_living_world, 42)
    first = fixture["findings"] + [extra]
    carried = next(f for f in first if f["id"] == "V1" and f["world"] == "frontier_living_world" and f["seed"] == 42)
    second = [{**f, "state": "pass"} if rep.finding_key(f) == rep.finding_key(carried) else f for f in copy.deepcopy(first)]
    _stub_evaluate_and_ownership["second"] = second
    report, rr = _run(_stub_evaluate_and_ownership, fixture, findings=first, main=_main(tmp_path))
    row = next(f for f in report["findings"] if f["id"] == "V1" and f["world"] == "frontier_living_world" and f["seed"] == 42)
    assert row["state"] == "unstable" and "not_rerun" not in row
    other = next(f for f in report["findings"] if f["id"] == "V1" and f["world"] == "urban_political" and f["seed"] == 42)
    assert other["state"] == "fail" and other["not_rerun"].startswith("in main's report")  # a pair that was not rerun keeps its first-pass state


def test_a_missing_main_report_falls_back_to_the_full_rerun(tmp_path, _stub_evaluate_and_ownership):
    fixture = _fix("main-44323101062")
    base, why = rep.load_main_baseline(tmp_path / "absent.json", HASH, _refs(fixture))
    assert base is None and "missing" in why
    report, rr = _run(_stub_evaluate_and_ownership, fixture, main=base, fallback=why)
    assert sorted(p for c in rr.calls for p in c) == sorted((w, s) for w in WORLDS for s in SEEDS)
    assert report["vs_main"]["source"] is None and why in report["vs_main"]["fallback"]
    assert "New vs main: unknown" in rep.render_markdown(report) and why in rep.render_markdown(report)


@pytest.mark.parametrize("content", ["{not json", "[1, 2]", "{}", json.dumps({"run_id": 1, "report": {"schema": "other"}}), json.dumps({"fallback": "none of main's runs has a report"})])
def test_an_unreadable_main_report_falls_back_to_the_full_rerun(content, tmp_path, _stub_evaluate_and_ownership):
    fixture = _fix("main-44323101062")
    path = tmp_path / "main-baseline.json"
    path.write_text(content, encoding="utf-8")
    base, why = rep.load_main_baseline(path, HASH, _refs(fixture))
    assert base is None and why
    report, rr = _run(_stub_evaluate_and_ownership, fixture, main=base, fallback=why)
    assert len([p for c in rr.calls for p in c]) == 15 and report["vs_main"]["fallback"] == why


def test_a_row_whose_state_changed_since_main_is_new_and_is_rerun(tmp_path, _stub_evaluate_and_ownership):
    fixture = _fix("main-44323101062")
    findings = copy.deepcopy(fixture["findings"])
    row = next(f for f in findings if f["state"] == "drift" and f["id"] == "O4.accepted" and f.get("key") == "TOWN_SERVICE")
    row["state"] = "fail"  # main carries it as drift; now it is a fail: same key, other state
    row.update({"violations": 1, "examples": []})
    report, rr = _run(_stub_evaluate_and_ownership, fixture, findings=findings, main=_main(tmp_path))
    assert rr.calls == [[("frontier_living_world", s) for s in SEEDS]]  # pooled/outcome scope: every seed of its world
    assert [(f["id"], f["state"]) for f in report["vs_main"]["new"]] == [("O4.accepted", "fail")]


def test_a_changed_value_with_the_same_key_and_state_is_not_new(tmp_path, _stub_evaluate_and_ownership):
    fixture = _fix("main-44323101062")
    findings = copy.deepcopy(fixture["findings"])
    for f in findings:
        if f["state"] == "fail":
            f["violations"] += 7
    report, rr = _run(_stub_evaluate_and_ownership, fixture, findings=findings, main=_main(tmp_path))
    assert rr.calls == [] and report["vs_main"]["new"] == []


def test_a_main_row_that_is_gone_is_counted(tmp_path, _stub_evaluate_and_ownership):
    fixture = _fix("main-44323101062")
    findings = [f for f in fixture["findings"] if not (f["state"] == "drift" and f["id"] == "O6.feeding_kills")]
    report, _ = _run(_stub_evaluate_and_ownership, fixture, findings=findings, main=_main(tmp_path))
    assert report["vs_main"]["gone"] == 1


def test_the_known_list_does_not_exempt_a_row_from_the_rerun(tmp_path, _stub_evaluate_and_ownership):
    """Ownership is derived after the rerun decision and is not an input to it: the decision is the same whatever the known list holds."""
    fixture = _fix("44366629746")
    a, rr_a = _run(_stub_evaluate_and_ownership, fixture, main=_main(tmp_path))
    owned = copy.deepcopy(fixture["findings"])
    for f in owned:
        f["ownership"] = "known"
    b, rr_b = _run(_stub_evaluate_and_ownership, fixture, findings=owned, main=_main(tmp_path))
    assert rr_a.calls == rr_b.calls and len(rr_a.calls[0]) == 6


def test_the_comparison_is_refused_for_another_harness_or_other_baseline_versions(tmp_path):
    fixture = _fix("main-44323101062")
    path = _baseline_file(tmp_path, fixture)
    base, why = rep.load_main_baseline(path, "another-hash", _refs(fixture))
    assert base is None and "harness" in why
    other = References(last={"version": 9}, milestone_first={"version": 9})
    base, why = rep.load_main_baseline(path, HASH, other)
    assert base is None and "baseline versions" in why


# ------------------------------------------------------------------ the CLI keeps the diff in JSON, markdown and the log


def test_cli_logs_the_diff_and_writes_it_to_json_and_markdown(tmp_path, monkeypatch, capsys, _stub_evaluate_and_ownership):
    fixture = _fix("main-44323101062")
    config = _config()
    monkeypatch.setattr(rep, "load_config", lambda p: config)
    monkeypatch.setattr(rep, "load_baselines", lambda p: [])
    monkeypatch.setattr(rep, "resolve_references", lambda b: _refs(fixture))
    monkeypatch.setattr(rep, "staleness", lambda *a, **k: type("S", (), {"reasons": []})())
    monkeypatch.setattr(rep, "load_documents", lambda d, c: {})
    monkeypatch.setattr(rep.known_reds, "load_known_reds", lambda *a, **k: [])
    monkeypatch.setattr(harness, "harness_hash", lambda *a, **k: HASH)
    _stub_evaluate_and_ownership["findings"] = fixture["findings"]
    out_json, out_md = tmp_path / "r.json", tmp_path / "r.md"
    rc = rep.main(["--config", "c", "--docs", str(tmp_path), "--baselines", "b", "--known", "k", "--out-json", str(out_json), "--out-md", str(out_md),
                   "--no-rerun", "--main-baseline", str(_baseline_file(tmp_path, fixture))])
    assert rc == 0
    assert "New vs main: none" in capsys.readouterr().out
    assert json.loads(out_json.read_text())["vs_main"]["new"] == [] and "New vs main: none" in out_md.read_text()


# ------------------------------------------------------------------ fetching main's report


def _gh(runs, artifacts, listing_error=False):
    calls = []

    def gh(args):
        calls.append(args)
        if args[:2] == ["run", "list"]:
            if listing_error:
                raise subprocess.CalledProcessError(1, "gh")
            return json.dumps(runs)
        run_id, out = args[2], Path(args[args.index("-D") + 1])
        art = artifacts.get(run_id)
        if art is None:
            raise subprocess.CalledProcessError(1, "gh")
        (out / "report").mkdir()
        (out / "report" / "rpg-gate-report.json").write_text(art if isinstance(art, str) else json.dumps(art))
        return ""

    gh.calls = calls
    return gh


def _run_row(rid, sha):
    return {"databaseId": rid, "headSha": sha, "event": "schedule", "createdAt": "2026-11-18T00:00:00Z"}


NOW = datetime(2026, 11, 19, tzinfo=timezone.utc)


def test_fetch_takes_the_newest_run_with_a_report_and_passes_over_runs_without_one():
    runs = [_run_row(3, "c"), _run_row(2, "b"), _run_row(1, "a")]
    out = mainrep.fetch(_gh(runs, {"2": {"sha": "b", "findings": []}, "1": {"sha": "a", "findings": []}}), now=NOW)
    assert out["run_id"] == 2 and out["head_sha"] == "b"  # run 3 (gate-skipped: no artifact) is passed over; its conclusion is irrelevant


def test_fetch_passes_over_a_report_made_from_another_checkout():
    runs = [_run_row(2, "b"), _run_row(1, "a")]
    out = mainrep.fetch(_gh(runs, {"2": {"sha": "dispatched-ref-sha"}, "1": {"sha": "a"}}), now=NOW)
    assert out["run_id"] == 1


def test_fetch_gives_a_fallback_when_the_newest_report_is_unreadable_never_an_older_one():
    out = mainrep.fetch(_gh([_run_row(2, "b"), _run_row(1, "a")], {"2": "{broken", "1": {"sha": "a"}}), now=NOW)
    assert "fallback" in out and "unreadable" in out["fallback"]


@pytest.mark.parametrize("runs, artifacts, listing_error", [([], {}, False), ([_run_row(1, "a")], {}, False), ([_run_row(1, "a")], {"1": {"sha": "a"}}, True)])
def test_fetch_falls_back_when_there_is_no_run_no_artifact_or_the_listing_fails(runs, artifacts, listing_error):
    out = mainrep.fetch(_gh(runs, artifacts, listing_error), now=NOW)
    assert "fallback" in out and "report" not in out


def test_fetch_excludes_the_current_run_and_asks_only_for_completed_runs_on_main():
    gh = _gh([_run_row(2, "b"), _run_row(1, "a")], {"1": {"sha": "a"}})
    assert mainrep.fetch(gh, exclude_run_id="2", now=NOW)["run_id"] == 1
    listing = gh.calls[0]
    assert "--status" in listing and listing[listing.index("--status") + 1] == "completed" and listing[listing.index("--branch") + 1] == "main"


def _event_row(rid, sha, event, created="2026-11-18T00:00:00Z"):
    return {"databaseId": rid, "headSha": sha, "event": event, "createdAt": created}


def test_a_scheduled_main_run_counts_and_the_source_names_event_head_and_age():
    out = mainrep.fetch(_gh([_event_row(2, "abcdef0123456789", "schedule")], {"2": {"sha": "abcdef0123456789"}}), now=NOW)
    assert (out["run_id"], out["event"], out["age_days"], out["max_age_days"]) == (2, "schedule", 1, 3)


def test_a_dispatch_on_main_whose_report_sha_equals_its_head_counts_even_with_a_ref_input_equal_to_main_head():
    """Model of run 44452967207: a workflow_dispatch on main, head a30847030, ref input a30847030: the report is made from the run's own head."""
    head = "a30847030" + "0" * 31
    out = mainrep.fetch(_gh([_event_row(44452967207, head, "workflow_dispatch")], {"44452967207": {"sha": head}}), now=NOW)
    assert out["run_id"] == 44452967207 and out["event"] == "workflow_dispatch"


def test_a_dispatch_on_main_with_a_ref_input_elsewhere_is_passed_over_and_the_next_older_run_is_used():
    runs = [_event_row(3, "main-head", "workflow_dispatch"), _event_row(2, "older-head", "schedule")]
    out = mainrep.fetch(_gh(runs, {"3": {"sha": "some-other-commit"}, "2": {"sha": "older-head"}}), now=NOW)
    assert out["run_id"] == 2


def test_a_branch_run_is_never_asked_for_and_never_selected():
    gh = _gh([_event_row(1, "a", "workflow_dispatch")], {"1": {"sha": "a"}})
    mainrep.fetch(gh, now=NOW)
    listing = gh.calls[0]
    assert listing[listing.index("--branch") + 1] == "main"  # the branch filter is what keeps PR-branch dispatches out
    cli = mainrep.fetch(_gh([], {}), branch="pr-branch", now=NOW)
    assert "fallback" in cli  # nothing is invented for a listing with no runs


def test_the_age_bound_is_inclusive_of_the_bound_and_falls_back_beyond_it_without_using_an_older_report():
    runs = [_event_row(2, "b", "schedule", "2026-11-16T00:00:00Z"), _event_row(1, "a", "schedule", "2026-11-18T00:00:00Z")]
    arts = {"2": {"sha": "b"}, "1": {"sha": "a"}}
    inside = mainrep.fetch(_gh(runs, arts), now=datetime(2026, 11, 19, 23, tzinfo=timezone.utc))
    assert inside["run_id"] == 2 and inside["age_days"] == 3  # exactly at the bound counts
    beyond = mainrep.fetch(_gh(runs, arts), now=datetime(2026, 11, 20, 1, tzinfo=timezone.utc))
    assert beyond["fallback"] == "main's newest gate report is 4 days old, bound 3"
    assert "fallback" in mainrep.fetch(_gh([_event_row(2, "b", "schedule", "garbage")], {"2": {"sha": "b"}}), now=NOW)


@pytest.mark.parametrize("content", [None, "", "other_key: 3\n", "main_report_max_age_days: 0\n", "main_report_max_age_days: -2\n", "main_report_max_age_days: three\n",
                                     "main_report_max_age_days: 2.5\n", "main_report_max_age_days: true\n", "- a list\n"])
def test_a_missing_or_invalid_bound_falls_back_to_the_full_rerun_never_to_no_bound(content, tmp_path):
    settings = tmp_path / "s.yaml"
    if content is not None:
        settings.write_text(content, encoding="utf-8")
    gh = _gh([_event_row(1, "a", "schedule")], {"1": {"sha": "a"}})
    out = mainrep.fetch(gh, now=NOW, settings=settings)
    assert "report" not in out and "settings are invalid" in out["fallback"] and gh.calls == []  # nothing is even fetched


def test_the_shipped_settings_hold_a_positive_integer_and_the_harness_hash_does_not_cover_them():
    assert mainrep.load_max_age_days() == 3
    assert not any("rpg_gate_main_report" in rel for rel in harness._HARNESS_SOURCES)  # not an input of harness_hash, so the baselines stay current
    assert "rpg_gate_main_report" not in Path(harness.__file__).read_text(encoding="utf-8")


def test_the_summary_line_names_run_event_head_age_and_bound(tmp_path, _stub_evaluate_and_ownership):
    fixture = _fix("main-44323101062")
    main = _main(tmp_path, event="schedule", age_days=1, max_age_days=3, run_id=44323101062, head_sha="a9dc29cdf2347dfaacdb0ba48acd6ebc6e34b68a")
    report, _ = _run(_stub_evaluate_and_ownership, fixture, main=main)
    assert "run 44323101062 (schedule, a9dc29cd, 1d old, bound 3d)" in rep.render_markdown(report)


def test_fetch_cli_writes_a_fallback_record_and_exits_zero_on_any_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(mainrep, "_gh", lambda args: (_ for _ in ()).throw(OSError("no gh")))
    monkeypatch.setattr(mainrep, "fetch", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    out = tmp_path / "b.json"
    assert mainrep.main(["fetch", "--out", str(out)]) == 0
    assert "fallback" in json.loads(out.read_text())
