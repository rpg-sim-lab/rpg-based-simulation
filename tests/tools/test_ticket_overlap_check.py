"""TCK-20261119-FILED-TICKETS-ARE-SCANNED-FOR-OVERLAP-WITH-OPEN-TODOS: the advisory overlap check, the pre-push check H and the report.

Frozen synthetic corpora only (never the live tickets). Every distinctive word below is a unique made-up token, so each one carries the same IDF weight and
q (the share of the draft's term weight that a candidate shares) is exactly the fraction of the draft's words the candidate repeats: the fixtures set q by counting.
The control rows are the numbered pairs of the stratified label sample (origin/main 5bedb5ff0): 15 is the duplicate (q 0.49 there), 2 the owner's inn-meal
pair (q 0.259, the reason the threshold is 0.25 and the raw floor is 0), 1 and 8 the related controls, 10 the known false positive the score does flag."""
from pathlib import Path

import pytest

from tools.delivery import pre_push_advisory_hook as hook
from tools.gate_checks import ticket_overlap_check as oc

FROM = "2026-11-21"
WORDS = [f"tok{c}{c}{c}{c}" for c in "abcdefghijklmnopqrstuvwxyz"]  # 26 unique 7-letter tokens, none a stopword


def _ticket(root: Path, folder: str, tid: str, title: str, summary: str, date: str = "2026-11-22", related: str = "- none", areas: str = "none"):
    d = root / folder
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{tid}.md"
    path.write_text(
        f"---\nstatus: active\nlayer: ai\nticket_id: {tid}\nphase: open\ndate: {date}\ntags: []\n---\n\n# {tid}\n\n## Title\n{title}\n\n## Status\nOPEN\n\n"
        f"## Request Summary\n{summary}\n\n## Related Tickets\n{related}\n\n## Related Code Areas\n{areas}\n\n## Test Summary\n", encoding="utf-8")
    return path


def _corpus(tmp_path):
    """Four filler tickets (their own words) so the corpus has several documents; returns the tickets root."""
    root = tmp_path / "corpus"
    for i in range(4):
        _ticket(root, "todos", f"TCK-20261101-FILLER-{i}", f"filler{i} subject", " ".join(f"fill{i}word{j}x" for j in range(6)), date="2026-11-01")
    return root


def _draft_and_twin(root, shared: int, own: int = 10, related: str = "- none", tid="TCK-20261122-DRAFT", twin="TCK-20261110-TWIN"):
    """A draft of `own` distinctive words, and an open twin repeating the first `shared` of them (so q = shared / own)."""
    words = WORDS[:own]
    _ticket(root, "todos", twin, " ".join(words[:shared]), " ".join(words[:shared]) + " twinonly1 twinonly2", date="2026-11-10")
    return _ticket(root, "todos", tid, " ".join(words[:2]), " ".join(words[2:]), related=related)


def _run(path, root):
    return oc.check_file(path, FROM, root / "todos", root / "inprogress")


# ---- the controls
def test_row_15_the_duplicate_is_flagged_with_its_title_and_q(tmp_path):
    root = _corpus(tmp_path)
    r = _run(_draft_and_twin(root, shared=8), root)
    assert r.status == "ran" and [h.ticket_id for h in r.hits] == ["TCK-20261110-TWIN"] and r.hits[0].q == pytest.approx(0.8)
    line = oc.render_line(r)
    assert line.startswith("overlap scan:") and "1 candidate: TCK-20261110-TWIN (" in line and "q=0.80" in line


def test_row_2_the_owners_inn_meal_pair_at_q_0_259_is_flagged_because_the_threshold_is_0_25_with_no_raw_floor(tmp_path):
    root = _corpus(tmp_path)
    # 3 of 11 words shared -> q = 0.2727; a raw-score floor or a threshold of 0.30 would have lost this pair
    path = _draft_and_twin(root, shared=3, own=11)
    r = _run(path, root)
    assert [h.ticket_id for h in r.hits] == ["TCK-20261110-TWIN"] and 0.25 <= r.hits[0].q < 0.30


@pytest.mark.parametrize("shared", [3, 4])  # rows 1 and 8: related pairs at q 0.30 and 0.40
def test_rows_1_and_8_related_controls_are_flagged(tmp_path, shared):
    root = _corpus(tmp_path)
    r = _run(_draft_and_twin(root, shared=shared), root)
    assert [h.ticket_id for h in r.hits] == ["TCK-20261110-TWIN"]


def test_row_10_a_known_false_positive_is_flagged_and_stays_a_documented_must_not_fix(tmp_path):
    # the SimQ anchor-reds ticket vs the slow-regression exit-2 ticket: unrelated causes (deterministic drift vs a wall-clock degraded mode) that share enough
    # vocabulary to pass 0.25. The score cannot tell them apart; the author cites or waives. This test pins that the check DOES flag it.
    root = _corpus(tmp_path)
    r = _run(_draft_and_twin(root, shared=3), root)
    assert r.hits and "locator, not a verdict" in oc.render_line(r)


def test_a_pair_below_the_threshold_is_not_flagged(tmp_path):
    root = _corpus(tmp_path)
    assert _run(_draft_and_twin(root, shared=2), root).hits == ()  # q = 0.2: unrelated enough


# ---- silence
def test_a_cited_hit_is_silent_but_an_uncited_second_one_still_shows(tmp_path):
    root = _corpus(tmp_path)
    path = _draft_and_twin(root, shared=8, related="- TCK-20261110-TWIN (the same defect)")
    r = _run(path, root)
    assert r.hits == () and r.cited_all and oc.render_line(r) is None


def test_the_waiver_line_is_silent_and_is_checked_for_presence_only(tmp_path):
    root = _corpus(tmp_path)
    r = _run(_draft_and_twin(root, shared=8, related="- overlap scan: 1 hits, none duplicate (different layer)"), root)
    assert r.waived and r.hits == () and oc.render_line(r) is None
    bad = _run(_draft_and_twin(root, shared=8, tid="TCK-20261122-DRAFT2", related="- overlap scan: 1 hits, none duplicate ()"), root)  # an empty reason is not a waiver
    assert not bad.waived and bad.hits


def test_ids_in_the_title_and_summary_are_stripped_before_scoring(tmp_path):
    root = _corpus(tmp_path)
    twin = "TCK-20261110-TOKAAAA-TOKBBBB-TOKCCCC-TOKDDDD"
    _ticket(root, "todos", twin, "twin", "tokaaaa tokbbbb tokcccc tokdddd tokeeee")
    # the draft only TYPES the twin's id (its words sit inside the id); stripped, it shares nothing with the twin
    path = _ticket(root, "todos", "TCK-20261122-DRAFT", f"related to {twin}", f"see {twin} and also {twin}")
    r = _run(path, root)
    assert r.hits == ()


def test_only_the_top_two_uncited_hits_are_shown_best_first(tmp_path):
    root = _corpus(tmp_path)
    for i, n in enumerate((9, 7, 5, 4), 1):  # four twins with q 0.9, 0.7, 0.5, 0.4
        _ticket(root, "todos", f"TCK-20261110-TWIN{i}", "t", " ".join(WORDS[:n]), date="2026-11-10")
    r = _run(_ticket(root, "todos", "TCK-20261122-DRAFT", " ".join(WORDS[:2]), " ".join(WORDS[2:10])), root)
    assert [h.ticket_id for h in r.hits] == ["TCK-20261110-TWIN1", "TCK-20261110-TWIN2"]
    assert oc.render_line(r).count("q=") == 2 and "2 candidates:" in oc.render_line(r)


# ---- grandfathering, skipping, failures
def test_a_ticket_dated_before_the_landing_date_is_grandfathered_and_a_done_ticket_is_skipped(tmp_path):
    root = _corpus(tmp_path)
    old = _draft_and_twin(root, shared=8)
    old.write_text(old.read_text(encoding="utf-8").replace("date: 2026-11-22", "date: 2026-11-20"), encoding="utf-8")
    r = _run(old, root)
    assert r.status == "skipped" and "grandfathered" in r.reason and oc.render_line(r) is None
    done = _ticket(tmp_path / "corpus", "done", "TCK-20261122-DONE", "x", "y")
    assert oc.check_file(done, FROM, root / "todos", root / "inprogress").status == "skipped"


def test_a_scanner_failure_is_a_named_warning_never_a_silent_pass_and_the_cli_still_exits_zero(tmp_path, monkeypatch, capsys):
    root = _corpus(tmp_path)
    path = _draft_and_twin(root, shared=8)

    def boom(*a, **k):
        raise RuntimeError("corpus unreadable")
    monkeypatch.setattr(oc, "score_hits", boom)
    r = _run(path, root)
    assert r.status == "errored" and "corpus unreadable" in oc.render_line(r)
    assert oc.main([str(path), "--todos-root", str(root / "todos"), "--inprogress-root", str(root / "inprogress")]) == 0
    out = capsys.readouterr()
    assert "overlap scan: ERROR" in out.out and "errored 1" in out.err


def test_cli_prints_ran_skipped_errored_and_exits_zero_on_a_missing_file(tmp_path, capsys):
    root = _corpus(tmp_path)
    ok = _draft_and_twin(root, shared=8)
    assert oc.main([str(ok), str(tmp_path / "nope.md"), "--todos-root", str(root / "todos"), "--inprogress-root", str(root / "inprogress")]) == 0
    err = capsys.readouterr().err
    assert "ran 1, skipped 0, errored 1" in err


# ---- the report
def test_report_counts_uncited_waived_clean_and_older_tickets(tmp_path):
    root = _corpus(tmp_path)
    _draft_and_twin(root, shared=8)  # uncited
    _ticket(root, "todos", "TCK-20261123-WAIVED", " ".join(WORDS[12:14]), " ".join(WORDS[14:22]), related="- overlap scan: 0 hits, none duplicate (checked by hand)")
    _ticket(root, "todos", "TCK-20261123-CLEAN", "cleanone cleantwo", "cleanthree cleanfour cleanfive")
    rows, tally = oc.report(FROM, root / "todos", root / "inprogress")
    assert tally["uncited"] == 1 and tally["waived"] == 1 and tally["clean"] >= 1 and tally["errored"] == 0
    assert any(r[1] == "uncited" and "TCK-20261110-TWIN" in r[2] for r in rows)


# ---- check H in the pre-push hook
class _Run:
    def __init__(self, diff, rc=0):
        self.diff, self.rc = diff, rc

    def __call__(self, cmd, timeout=30):
        return hook.CommandResult(self.rc, self.diff, "")


def test_check_h_names_a_pushed_ticket_with_an_uncited_candidate(tmp_path, monkeypatch):
    monkeypatch.setattr(oc, "check_files", lambda files, **k: (["overlap scan: x: 1 candidate: TCK-1 (t, q=0.50)."], {"ran": 1, "skipped": 0, "errored": 0}))
    monkeypatch.chdir(tmp_path)
    (tmp_path / "agent-working/tickets/todos").mkdir(parents=True)
    (tmp_path / "agent-working/tickets/todos/TCK-20261122-X.md").write_text("x")
    out = hook.check_ticket_overlap(_Run("agent-working/tickets/todos/TCK-20261122-X.md\ndocs/x.md\nagent-working/tickets/todos/TCK-20261122-GONE.md\n"))
    assert out == ["pre-push: overlap scan: x: 1 candidate: TCK-1 (t, q=0.50)."]


def test_check_h_says_nothing_without_a_pushed_open_ticket_or_on_a_git_failure():
    assert hook.check_ticket_overlap(_Run("docs/x.md\nagent-working/tickets/done/TCK-20261122-X.md\n")) == []
    assert hook.check_ticket_overlap(_Run("", rc=1)) == []


def test_check_h_names_a_failing_scanner_instead_of_staying_silent(monkeypatch, tmp_path):
    def boom(files, **k):
        raise RuntimeError("scanner down")
    monkeypatch.setattr(oc, "check_files", boom)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "agent-working/tickets/inprogress").mkdir(parents=True)
    (tmp_path / "agent-working/tickets/inprogress/TCK-20261122-X.md").write_text("x")
    out = hook.check_ticket_overlap(_Run("agent-working/tickets/inprogress/TCK-20261122-X.md\n"))
    assert out and "overlap scan: ERROR" in out[0] and "scanner down" in out[0]


def test_check_h_is_part_of_run_all_checks_and_never_changes_the_exit_code(monkeypatch):
    seen = []
    monkeypatch.setattr(hook, "check_ticket_overlap", lambda *a, **k: seen.append("h") or [])
    hook.run_all_checks(run_command=_Run(""), tickets_root=Path("/nonexistent"))
    assert seen == ["h"]
