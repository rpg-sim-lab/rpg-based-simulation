"""Tests for the required `## Durable state, lifecycle and clocks` ticket section, its done-checker condition,
its rendering into the PR body and the lint on that body
(TCK-20261118-REQUIRED-DURABLE-STATE-LIFECYCLE-CLOCKS-SECTION-IN-TICKETS-AND-PR-BODIES)."""
from pathlib import Path

import pytest

from tools import ticket_field_values as tfv
from tools.agent_working_paths import TICKETS
from tools.delivery import pr_body_lint, pr_render
from tools.gate_checks import done_checker_static as dcs
from tests.tools.test_delivery_pr_render import FakeRunner, _git_diff_rule, _git_log_rule, _write_ticket

_ROOT = Path(__file__).resolve().parents[2]
_REQUIRED_FROM = tfv.LIFECYCLE_SECTION_REQUIRED_FROM
_NEW = "2026-11-19"
_OLD = "2026-11-18"


def _ticket(tmp_path, date, section=None, name="TCK-20261119-FIXTURE"):
    body = f"## Title\nFixture\n\n## Status\nOPEN\n\n## Tier\nstandard\n\n## Priority\nP2\n"
    if section is not None:
        body += f"\n## {tfv.LIFECYCLE_SECTION}\n{section}\n"
    body += "\n## Test Summary\nok\n"
    path = tmp_path / f"{name}.md"
    path.write_text(f"---\nstatus: active\nlayer: ai\nticket_id: {name}\ndate: {date}\ntags: []\n---\n\n# {name}\n\n{body}", encoding="utf-8")
    return path


def test_landing_date_is_the_day_after_this_ticket_was_written():
    assert _REQUIRED_FROM == _NEW


def test_missing_section_fails_for_a_new_ticket(tmp_path):
    status, evidence = tfv.check_lifecycle_section(_ticket(tmp_path, _NEW))
    assert status == "FAIL" and "missing" in evidence


def test_empty_section_fails(tmp_path):
    status, evidence = tfv.check_lifecycle_section(_ticket(tmp_path, _NEW, section="   "))
    assert status == "FAIL" and "empty" in evidence


@pytest.mark.parametrize("text", ["N/A", "N/A:", "N/A:   ", "n/a.", "N/A :"])
def test_na_without_a_reason_fails(tmp_path, text):
    assert tfv.check_lifecycle_section(_ticket(tmp_path, _NEW, section=text))[0] == "FAIL"


def test_na_with_a_reason_passes(tmp_path):
    status, evidence = tfv.check_lifecycle_section(_ticket(tmp_path, _NEW, section="N/A: tooling only, no durable record"))
    assert status == "PASS" and "N/A with a reason" in evidence


def test_answers_pass(tmp_path):
    assert tfv.check_lifecycle_section(_ticket(tmp_path, _NEW, section="- field x: created by A; update merges; exits via expiry; cleared by B; clock: kernel tick"))[0] == "PASS"


def test_ticket_dated_before_the_landing_date_is_grandfathered(tmp_path):
    status, evidence = tfv.check_lifecycle_section(_ticket(tmp_path, _OLD))
    assert status == "NA" and "grandfathered" in evidence


def test_ticket_with_no_date_is_grandfathered(tmp_path):
    path = tmp_path / "TCK-X.md"
    path.write_text("---\nstatus: active\n---\n\n## Title\nT\n", encoding="utf-8")
    assert tfv.check_lifecycle_section(path)[0] == "NA"


def test_every_existing_closed_and_open_ticket_passes():
    """The corpus guard: nothing already on disk may fail the new check (grandfathering by date)."""
    failures = []
    for folder in ("done", "inprogress", "todos"):
        for path in (TICKETS / folder).rglob("TCK-*.md"):
            status, evidence = tfv.check_lifecycle_section(path)
            if status == "FAIL" and "dated" not in evidence:
                failures.append((str(path), evidence))
    # A ticket filed on or after the landing date would legitimately fail until it has the section.
    assert not [f for f in failures if f[0] and _date_of(f[0]) < _REQUIRED_FROM], failures


def _date_of(path):
    return str((tfv.extract_frontmatter(Path(path).read_text(encoding="utf-8")) or {}).get("date") or "")[:10]


def test_done_checker_reports_a_missing_section_as_a_warning_not_a_failure(tmp_path):
    """Advisory first (owner decision #715 6972698325): known-negative fixture WARNs, known-positive is OK, grandfathered and missing-file are NA."""
    assert dcs.check_ticket_lifecycle_section("TCK-X", _ticket(tmp_path, _NEW))[0] == "WARN"
    ok = dcs.check_ticket_lifecycle_section("TCK-X", _ticket(tmp_path, _NEW, section="N/A: tooling only", name="TCK-20261119-OK"))
    assert ok[0] == "OK" and ok[1].startswith("ran:")
    old = dcs.check_ticket_lifecycle_section("TCK-X", _ticket(tmp_path, _OLD, name="TCK-20261118-OLD"))
    assert old[0] == "NA" and old[1].startswith("skipped:")
    assert dcs.check_ticket_lifecycle_section("TCK-X", tmp_path / "missing.md")[0] == "NA"


def test_done_checker_shows_an_errored_check_instead_of_silencing_it(tmp_path, monkeypatch):
    monkeypatch.setattr(dcs, "check_lifecycle_section", lambda p: (_ for _ in ()).throw(RuntimeError("boom")))
    status, evidence = dcs.check_ticket_lifecycle_section("TCK-X", _ticket(tmp_path, _NEW))
    assert status == "WARN" and evidence.startswith("errored:")


def test_condition_is_advisory_and_leaves_the_blocking_precheck_alone(tmp_path, monkeypatch):
    results = _precheck(tmp_path, monkeypatch)
    assert len(results) == 8 and "ticket_lifecycle_section" not in [r["condition"] for r in results]  # not a Part A (PASS/FAIL) condition
    advisory = {r["condition"]: r for r in dcs.run_advisory_checks("TCK-FAKE", "standard")}
    assert advisory["ticket_lifecycle_section"]["status"] in ("OK", "WARN", "NA")  # ran, reported, or skipped: never silent


def _precheck(tmp_path, monkeypatch):
    from tests.tools.test_done_checker_static import _scaffold_precheck_repo
    _scaffold_precheck_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    return dcs.run_static_precheck("TCK-FAKE", "standard", "2026-07-05T00:00:00Z")


def test_ticket_cli_reports_a_missing_section(tmp_path, capsys):
    assert tfv.main([str(_ticket(tmp_path, _NEW))]) == 1  # the standalone checker CLI still exits 1: it is the check itself
    assert "missing" in capsys.readouterr().out


# --- renderer -------------------------------------------------------------------------------------------------------

def _render(tmp_path, changed, section="- x: created by A; merges; exits on expiry; cleared by B; kernel tick"):
    root = tmp_path / "fixture_tickets"
    root.mkdir()
    path = _write_ticket(root, "TCK-20260924-A", "ai", "Thing")
    if section is not None:
        path.write_text(path.read_text(encoding="utf-8") + f"\n## {tfv.LIFECYCLE_SECTION}\n{section}\n", encoding="utf-8")
    runner = FakeRunner([_git_log_rule(["TCK-20260924-A: x"]), _git_diff_rule(changed)])
    return pr_render.render(tickets_root=root, run_command=runner)["body"]


def test_no_src_change_renders_na_itself(tmp_path):
    body = _render(tmp_path, ["tools/x.py", "agent-working/tickets/TCK-20260924-A.md"])
    assert f"{pr_body_lint.LIFECYCLE_LINE} TCK-20260924-A: N/A: no src change" in body
    assert pr_body_lint.find_missing_lifecycle(body) is None


def test_src_change_renders_the_ticket_section_on_one_line(tmp_path):
    body = _render(tmp_path, ["src/engine/x.py", "agent-working/tickets/TCK-20260924-A.md"], section="- x: created by A.\n- exits on expiry.")
    assert f"{pr_body_lint.LIFECYCLE_LINE} TCK-20260924-A: - x: created by A. - exits on expiry." in body
    assert pr_body_lint.find_missing_lifecycle(body) is None


def test_src_change_with_a_ticket_lacking_the_section_says_so(tmp_path):
    body = _render(tmp_path, ["src/engine/x.py", "agent-working/tickets/TCK-20260924-A.md"], section=None)
    assert pr_render.NOT_RECORDED in body and pr_body_lint.find_missing_lifecycle(body) is None


def test_ticketless_body_carries_the_line_and_passes_the_lint(tmp_path):
    body = pr_render.render_ticketless_body("theme", "why", ["docs/x.md"], _spec(), [])
    assert f"{pr_body_lint.LIFECYCLE_LINE} {pr_render.NO_TICKET_NA}" in body
    assert pr_body_lint.find_missing_lifecycle(body) is None


def _spec():
    import json
    return json.loads((_ROOT / "tools/delivery/pr_template_spec.json").read_text(encoding="utf-8"))


def test_ticket_section_name_is_one_string_in_both_tools():
    assert pr_render.LIFECYCLE_SECTION == tfv.LIFECYCLE_SECTION


# --- lint -----------------------------------------------------------------------------------------------------------

_SHAPED = "## What landed\nx\n\n## Tickets\n| TCK-20261119-NEW | standard | t |\n\n## Why\ny\n\n## Verification\n- Tests: ok\n{line}- Known gaps: none\n\n## Review notes\nz\n"


def test_lint_fails_a_template_shaped_body_without_the_line():
    assert "no `- Durable" in pr_body_lint.find_missing_lifecycle(_SHAPED.format(line=""))


def test_lint_fails_an_empty_or_placeholder_line():
    assert "empty" in pr_body_lint.find_missing_lifecycle(_SHAPED.format(line=f"{pr_body_lint.LIFECYCLE_LINE}\n"))
    assert "empty" in pr_body_lint.find_missing_lifecycle(_SHAPED.format(line=f"{pr_body_lint.LIFECYCLE_LINE} <!-- rendered -->\n"))


def test_lint_passes_a_filled_line():
    assert pr_body_lint.find_missing_lifecycle(_SHAPED.format(line=f"{pr_body_lint.LIFECYCLE_LINE} TCK-X: N/A: no src change\n")) is None


def test_lint_skips_bodies_that_are_not_template_shaped():
    assert pr_body_lint.find_missing_lifecycle("Bump requests from 2.31 to 2.32") is None
    assert pr_body_lint.find_missing_lifecycle(None) is None


def test_lint_fails_a_shaped_body_with_no_verification_section():
    assert pr_body_lint.find_missing_lifecycle("## Tickets\n| TCK-20261120-NEW | s | t |\n") == "no ## Verification section"


def test_lint_cli_exit_codes(capsys):
    ok = {"PR_BODY": _SHAPED.format(line=f"{pr_body_lint.LIFECYCLE_LINE} TCK-X: N/A: no src change\n")}
    bad = {"PR_BODY": _SHAPED.format(line="")}
    assert pr_body_lint.main(environ=ok) == 0
    assert pr_body_lint.main(environ=bad) == 0  # advisory first: reported, exit code unaffected
    out = capsys.readouterr().out
    assert "::warning::" in out and "ran, REPORTED (advisory)" in out and "ran, OK" in out  # the status is always shown
    attribution = {"PR_BODY": _SHAPED.format(line="") + "\nCo-Authored-By: x <y@z>\n"}
    assert pr_body_lint.main(environ=attribution) == 1  # the attribution check still fails the job


def test_the_unfilled_github_template_fails_the_lint():
    """The raw template (placeholders still in) must fail, so a hand-filled body cannot skip the line."""
    template = (_ROOT / ".github/pull_request_template.md").read_text(encoding="utf-8")
    with_new_ticket = template.replace("| TCK-… | standard | … |", "| TCK-20261119-NEW | standard | t |")
    assert with_new_ticket != template and pr_body_lint.find_missing_lifecycle(with_new_ticket) is not None
    assert pr_body_lint.LIFECYCLE_LINE in template


# --- fill-rate report -----------------------------------------------------------------------------------------------

def test_fill_rate_counts_states_and_ignores_old_tickets(tmp_path):
    from tools.gate_checks import lifecycle_section_fill_rate as fr
    for name, date, section in [("TCK-20261119-A", _NEW, "- answers"), ("TCK-20261119-B", _NEW, "N/A: tooling"),
                                ("TCK-20261119-C", _NEW, None), ("TCK-20261101-D", "2026-11-01", None)]:
        _ticket(tmp_path, date, section=section, name=name)
    report = fr.collect(tmp_path)
    assert report["tickets_subject_to_section"] == 3
    assert report["counts"] == {"answers": 1, "na_with_reason": 1, "missing_or_invalid": 1}
    assert round(report["fill_rate"], 3) == 0.667 and round(report["na_rate"], 3) == 0.333


def test_fill_rate_is_none_when_no_ticket_is_subject(tmp_path):
    from tools.gate_checks import lifecycle_section_fill_rate as fr
    _ticket(tmp_path, _OLD, name="TCK-20261118-OLD")
    report = fr.collect(tmp_path)
    assert report["tickets_subject_to_section"] == 0 and report["fill_rate"] is None


def test_fill_rate_cli_prints_the_real_baseline(capsys):
    from tools.gate_checks import lifecycle_section_fill_rate as fr
    assert fr.main([]) == 0
    assert "tickets dated on or after 2026-11-19" in capsys.readouterr().out


def test_a_body_listing_only_grandfathered_tickets_passes_without_the_line():
    old = _SHAPED.replace("TCK-20261119-NEW", "TCK-20261118-OLD").format(line="")
    assert pr_body_lint.find_missing_lifecycle(old) is None


def test_a_body_with_one_new_ticket_among_old_ones_needs_the_line():
    mixed = _SHAPED.replace("| TCK-20261119-NEW | standard | t |", "| TCK-20261118-OLD | standard | t |\n| TCK-20261119-NEW | standard | t |").format(line="")
    assert pr_body_lint.find_missing_lifecycle(mixed) is not None


def test_a_ticketless_body_never_needs_the_line():
    assert pr_body_lint.find_missing_lifecycle("## Tickets\n(none: this PR closes no ticket)\n\n## Verification\n- Tests: x\n") is None


def test_lint_landing_date_matches_the_ticket_check():
    assert pr_body_lint.LIFECYCLE_REQUIRED_FROM == tfv.LIFECYCLE_SECTION_REQUIRED_FROM.replace("-", "")


def test_a_new_ticket_with_no_src_change_renders_na_and_passes(tmp_path):
    root = tmp_path / "fixture_tickets"
    root.mkdir()
    _write_ticket(root, "TCK-20261119-NEWDOCS", "ai", "Docs only")
    runner = FakeRunner([_git_log_rule(["TCK-20261119-NEWDOCS: x"]), _git_diff_rule(["docs/x.md", "agent-working/tickets/TCK-20261119-NEWDOCS.md"])])
    body = pr_render.render(tickets_root=root, run_command=runner)["body"]
    assert "TCK-20261119-NEWDOCS: N/A: no src change" in body and pr_body_lint.find_missing_lifecycle(body) is None
