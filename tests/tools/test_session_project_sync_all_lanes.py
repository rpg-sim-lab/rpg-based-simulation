"""TCK-20261115-PROJECT-SYNC-ALL-LANES (P3b): all lanes, the Domain select, --fetch, the last-run file and the heartbeat. No network."""
import json
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.agent_working_paths import TICKETS
from tools.sessions import project_client as pc
from tools.sessions import project_sync as ps
from tools.sessions import session_start_hook as hook
from tools.sessions.roster import load_roster

T = TICKETS.as_posix()
NOW = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
CFG = {"pilot_lanes": ["rpg"], "pilot_start": "2026-11-12", "done_window_days": 14, "stale_host_hours": 24}
HOST = "u24desktop"
ROSTER = load_roster(Path(__file__).resolve().parents[2])
DOMAINS = tuple(d.name for d in ROSTER.domains)


@pytest.fixture(autouse=True)
def _last_run_in_tmp(tmp_path_factory, monkeypatch):
    monkeypatch.setattr(ps, "LAST_RUN_PATH", tmp_path_factory.mktemp("state") / "last-run.json")


def copy(tid="TCK-20261115-X", folder="todos", areas=(), tier="hotfix"):
    return ps.TicketCopy(tid, folder, f"{T}/{folder}/{tid}.md", "A title", tier, False, "2026-11-15", code_areas=tuple(areas))


def extras():
    return ps.Extras(domains=frozenset(DOMAINS) | {ps.UNASSIGNED, ps.UNKNOWN}, code_domain=ps.make_code_domain(ROSTER))


def plan_for(main, branches=(), items=(), host=HOST, ex=None, cfg=CFG):
    index = {tid: [(c.folder, c.path) for c in cs] for tid, cs in main.items()}
    loaded = {c.path: c for cs in main.values() for c in cs}
    return ps.build_plan(index, lambda p: loaded[p], list(branches), [], list(items), host, "abc @ now", cfg, lambda p: None, NOW, ex or extras())


# ---- lanes and Domain
def test_main_only_todos_and_inprogress_become_items_main_only_done_does_not():
    plan = plan_for({"TCK-1": [copy("TCK-1", "todos")], "TCK-2": [copy("TCK-2", "inprogress")], "TCK-3": [copy("TCK-3", "done")]})
    assert sorted(c["Ticket ID"] for c in plan.creates) == ["TCK-1", "TCK-2"]


def test_a_branch_of_any_registered_domain_is_a_candidate_and_pilot_lanes_is_ignored():
    fact = ps.BranchFact(HOST, "platform-x", "/wt", "platform-implementer", "platform", (copy("TCK-9", "inprogress"),))
    plan = plan_for({"TCK-9": [copy("TCK-9", "inprogress")]}, [fact])
    assert plan.creates[0]["Domain"] == "platform"


def test_attribute_takes_the_longest_registered_prefix_else_unknown_and_a_recorded_seat_wins():
    assert ps.attribute("agent-working-x", [], DOMAINS) == ("agent-working (seat not recorded)", "agent-working")
    assert ps.attribute("rpg-planner-seat-8", [], DOMAINS)[1] == "rpg"
    assert ps.attribute("freemeal", [], DOMAINS) == ("unknown", "unknown")
    assert ps.attribute("agentic-thing", [], DOMAINS) == ("unknown", "unknown")  # `agent` is no domain, `agent-working-` is not its prefix
    assert ps.attribute("rpg-x", [("agent-working-implementer", "agent-working")], DOMAINS) == ("agent-working-implementer", "agent-working")
    assert ps.attribute("ab-x", [], ("ab", "ab-x-long")) == ("ab (seat not recorded)", "ab")


def test_main_only_domain_a_segment_beats_code_areas_which_beat_unassigned():
    seg = {"Host facts": "ubuntu: state=progress seat=platform-implementer domain=platform"}
    plan = plan_for({"TCK-1": [copy("TCK-1", areas=["src/core/state.py"])]}, items=[{**seg, "Ticket ID": "TCK-1", "Title": "x"}])
    domain_of = lambda p: (p.updates[0][0] if p.updates else p.creates[0])["Domain"]
    assert domain_of(plan) == "platform"
    plan = plan_for({"TCK-2": [copy("TCK-2", areas=["src/core/state.py", "src/core/registries.py"])]})
    assert plan.creates[0]["Domain"] == "rpg"


def test_mixed_or_unrouted_code_areas_are_unassigned_and_counted_in_one_note():
    main = {"TCK-1": [copy("TCK-1", areas=["src/core/state.py", "tools/sessions/route.py"])], "TCK-2": [copy("TCK-2", areas=["nothing/here.py"])],
            "TCK-3": [copy("TCK-3")], "TCK-4": [copy("TCK-4", areas=["src/core/state.py"])]}
    plan = plan_for(main)
    got = {c["Ticket ID"]: c["Domain"] for c in plan.creates}
    assert got == {"TCK-1": "unassigned", "TCK-2": "unassigned", "TCK-3": "unassigned", "TCK-4": "rpg"}
    assert plan.notes.count("domain: 3 tickets unassigned (no or mixed code-area owners)") == 1
    assert not any("unassigned" in f for f in plan.findings)


def test_code_area_tokens_strip_decorations_and_skip_globs_and_braces():
    text = "- `tools/sessions/project_sync.py`: `attribute`, `build_plan`\n- tools/x.py::main and tools/y.py:12.\n- src/**/*.py, src/{a,b}/c.py\n- plain words"
    assert ps.code_area_paths(text) == ("tools/sessions/project_sync.py", "tools/x.py", "tools/y.py")
    assert ps.parse_copy(f"{T}/todos/TCK-1.md", "## Title\nT\n\n## Related Code Areas\n- `src/core/state.py`\n\n## Other\n- a/b.py\n").code_areas == ("src/core/state.py",)


def test_several_segment_domains_pick_the_sorted_first_with_a_finding_and_an_unknown_option_is_a_finding():
    item, findings = ps.derive_item("TCK-1", [copy("TCK-1")], [], [], {"Host facts": "a: state=progress domain=rpg; b: state=progress domain=perf"},
                                    HOST, "s", None, extras())
    assert item["Domain"] == "perf" and any("held in domains perf, rpg" in f for f in findings)
    item, findings = ps.derive_item("TCK-1", [copy("TCK-1")], [], [], {"Host facts": "a: state=progress domain=mystery"}, HOST, "s", None, extras())
    assert item["Domain"] == "" and any("'mystery' is not an option" in f for f in findings)


def test_epic_rule_a_also_checks_origins_path_for_a_branch_copy_under_inprogress():
    folder_path = f"{T}/todos/epic-x/TCK-E.md"
    member_path = f"{T}/todos/epic-x/TCK-1.md"
    epic = ps.TicketCopy("TCK-E", "todos", folder_path, "e", "epic")
    index = {"TCK-E": [("todos", folder_path)], "TCK-1": [("todos", member_path)]}
    resolve = ps.make_epic_resolver(index, lambda p: epic if p == folder_path else copy("TCK-1"), {})
    assert resolve("TCK-1", f"{T}/inprogress/TCK-1.md", "hotfix")[0] == "TCK-E"  # the chosen copy sits under inprogress/, origin's under the epic folder


# ---- --init: Domain rename
class FakeInit:
    def __init__(self, project):
        self.proj, self.calls = project, []

    def load_project(self):
        return self.proj

    def list_items(self):
        return []

    def create_text_field(self, pid, name): self.calls.append(("create_text", name))
    def create_select_field(self, pid, name, options): self.calls.append(("create_select", name, [n for n, _ in options]))
    def set_select_options(self, fid, options): self.calls.append(("options", fid))
    def rename_field(self, fid, name): self.calls.append(("rename", fid, name))
    def create_date_field(self, pid, name): self.calls.append(("create_date", name))


def _project(domain_type="TEXT", extra=()):
    fields = {"Title": pc.ProjectField("F_Title", "Title", "TITLE"), "Status": pc.ProjectField("F_Status", "Status", "SINGLE_SELECT",
              tuple((n, f"O_{n}") for n in ps.STATUSES))}
    for n in pc.TEXT_FIELDS:
        fields[n] = pc.ProjectField(f"F_{n}", n, "TEXT")
    fields["Tier"] = pc.ProjectField("F_Tier", "Tier", "SINGLE_SELECT", tuple((n, f"O_{n}") for n, _ in pc.TIER_OPTIONS))
    fields["Priority"] = pc.ProjectField("F_Priority", "Priority", "SINGLE_SELECT", tuple((n, f"O_{n}") for n, _ in pc.PRIORITY_OPTIONS))
    fields["Layer"] = pc.ProjectField("F_Layer", "Layer", "SINGLE_SELECT", (("combat", "O_combat"),))
    fields["Domain"] = pc.ProjectField("F_Domain", "Domain", domain_type)
    fields["Filed"] = pc.ProjectField("F_Filed", "Filed", "DATE")
    for f in extra:
        fields[f.name] = f
    return pc.Project("P1", fields)


WANTED = DOMAINS + (ps.UNASSIGNED, ps.UNKNOWN)


def test_init_renames_the_text_domain_creates_the_select_and_a_second_init_does_nothing():
    fake = FakeInit(_project())
    lines, code = pc.init_fields(fake, ps.STATUSES, layers=("combat",), domains=WANTED)
    assert code == 0 and ("rename", "F_Domain", "Domain (old)") in fake.calls
    assert ("create_select", "Domain", list(WANTED)) in fake.calls and "renamed: Domain -> Domain (old) (kept, never deleted)" in lines
    assert not any("delete" in str(c).lower() for c in fake.calls)
    again = FakeInit(_project(domain_type="SINGLE_SELECT", extra=[pc.ProjectField("F_old", "Domain (old)", "TEXT")]))
    again.proj.fields["Domain"] = pc.ProjectField("F_Domain", "Domain", "SINGLE_SELECT", tuple((n, f"O_{n}") for n in WANTED))
    lines, code = pc.init_fields(again, ps.STATUSES, layers=("combat",), domains=WANTED)
    assert code == 0 and again.calls == [] and "left alone: Domain" in lines


def test_init_refuses_with_nothing_written_when_domain_is_text_and_the_old_name_exists():
    fake = FakeInit(_project(extra=[pc.ProjectField("F_old", "Domain (old)", "TEXT")]))
    lines, code = pc.init_fields(fake, ps.STATUSES, layers=("combat",), domains=WANTED)
    assert code == 1 and fake.calls == [] and any("not renaming over it" in line for line in lines)


def test_after_the_rename_there_are_no_false_hand_edits_and_the_domain_is_planned_as_an_update():
    c = copy("TCK-1", "todos", areas=["src/core/state.py"])
    plan0 = plan_for({"TCK-1": [c]})
    derived = plan0.creates[0]
    live = {k: v for k, v in derived.items() if not k.startswith("_")}
    live["Sync hash"] = ps.sync_hash(live)
    renamed = {**live, "Domain": "", "Domain (old)": live["Domain"], "_item_id": "I1", "_draft_id": "D1"}
    plan = plan_for({"TCK-1": [c]}, items=[renamed])
    assert plan.hand_edits == [] and [ch for _, ch in plan.updates] == [["Domain"]]


# ---- --fetch
def test_fetch_origin_runs_only_the_fixed_argv_and_reports_failure_and_timeout():
    seen = []

    def ok(args, **kw):
        seen.append((args, kw))
        return SimpleNamespace(returncode=0, stderr="")

    assert ps.fetch_origin(Path("/r"), ok) is None and seen[0][0] == ["git", "fetch", "origin", "main"] and seen[0][1]["timeout"] == ps.FETCH_TIMEOUT_S
    bad = lambda a, **k: SimpleNamespace(returncode=128, stderr="fatal: could not read\nfatal: no network")
    assert ps.fetch_origin(Path("/r"), bad) == "fatal: no network"

    def hang(a, **k):
        raise subprocess.TimeoutExpired(a, 60)

    assert "timed out" in ps.fetch_origin(Path("/r"), hang)
    with pytest.raises(ps.WriteRefused):
        ps._guard(["git", "fetch", "origin", "main"])  # the read-only guard still refuses fetch


# ---- last-run file, heartbeat, stale hosts
def test_the_last_run_file_has_mode_600_a_failed_streak_and_never_raises(tmp_path):
    path = tmp_path / "d" / "last-run.json"
    ps.write_last_run({"rc": 1, "error": "boom"}, path)
    ps.write_last_run({"rc": 1, "error": "boom"}, path)
    assert ps.read_last_run(path)["failed_streak"] == 2 and stat.S_IMODE(path.stat().st_mode) == 0o600
    ps.write_last_run({"rc": 0}, path)
    assert ps.read_last_run(path)["failed_streak"] == 0
    ps.write_last_run({"rc": 1}, tmp_path / "file" / "x" / "y.json" if (tmp_path / "file").write_text("x") else path)  # parent is a file: swallowed


def test_the_start_hook_warns_after_two_failed_runs_only(tmp_path):
    path = tmp_path / "last-run.json"
    assert hook._sync_line(path) == ""
    path.write_text(json.dumps({"failed_streak": 1, "host": "h", "error": "e"}))
    assert hook._sync_line(path) == ""
    path.write_text(json.dumps({"failed_streak": 2, "host": "h", "time": "t", "error": "GitHub refused"}))
    assert "last 2 --apply runs on h failed" in hook._sync_line(path) and "GitHub refused" in hook._sync_line(path)
    path.write_text("not json")
    assert hook._sync_line(path) == ""


def test_main_writes_last_run_on_apply_even_when_refused_and_not_on_a_dry_run(monkeypatch, tmp_path):
    (tmp_path / "registries").mkdir()
    (tmp_path / "registries" / "session_project.yaml").write_text("project: {owner: o, number: 1}\n")
    monkeypatch.setattr(ps, "_client", lambda cfg, notes=None: SimpleNamespace(list_items=lambda: [], load_project=lambda: _project()))  # a read
    monkeypatch.setattr(ps, "origin_info", lambda root: ("abc", None))
    monkeypatch.setattr(ps, "read_branch_facts", lambda *a, **k: ([], 0))
    monkeypatch.setattr(ps, "read_open_prs", lambda root, notes, run=None: ps.PrList())
    assert ps.main(["--root", str(tmp_path)]) == 0
    assert not ps.LAST_RUN_PATH.exists()
    monkeypatch.setattr(ps, "read_open_prs", lambda root, notes, run=None: None)
    assert ps.main(["--root", str(tmp_path), "--apply"]) == 1
    data = ps.read_last_run()
    assert data["rc"] == 1 and data["failed_streak"] == 1 and "nothing written" in data["error"]


class FakeClient:
    def __init__(self, fail_heartbeat=False):
        self.calls, self.fail, self.proj = [], fail_heartbeat, _project()
        self.proj.fields["Last run"] = pc.ProjectField("F_Last", "Last run", "TEXT")

    def add_draft(self, pid, title, body):
        if self.fail:
            raise pc.ProjectError("rate limit hit")
        self.calls.append(("add_draft", title))
        return "I-new", "D-new"

    def set_text(self, pid, iid, fid, text):
        if self.fail:
            raise pc.ProjectError("rate limit hit")
        self.calls.append(("set_text", iid, text))


def test_the_heartbeat_is_created_or_rewrites_only_this_hosts_segment_of_the_oldest_item():
    plan = ps.Plan()
    client = FakeClient()
    assert ps.write_heartbeat(client, client.proj, plan, HOST, "2026-11-20T12:00Z", 0) is None
    assert client.calls == [("add_draft", ps.HEARTBEAT_TITLE), ("set_text", "I-new", "u24desktop: 2026-11-20T12:00Z rc=0")]
    old = {"_item_id": "H1", "Title": ps.HEARTBEAT_TITLE, "Last run": "ubuntu: 2026-11-20T11:30Z rc=0; u24desktop: 2026-11-19T10:00Z rc=1"}
    extra = {"_item_id": "H2", "Title": ps.HEARTBEAT_TITLE, "Last run": "ubuntu: 2026-11-18T00:00Z rc=1"}
    plan = plan_for({}, items=[old, extra])
    client = FakeClient()
    ps.write_heartbeat(client, client.proj, plan, HOST, "2026-11-20T12:00Z", 0)
    assert client.calls == [("set_text", "H1", "u24desktop: 2026-11-20T12:00Z rc=0; ubuntu: 2026-11-20T11:30Z rc=0")]  # the oldest item, the other host kept
    assert plan.archives == [] and any("2 '_sync heartbeat' items" in f for f in plan.findings)


def test_a_failed_heartbeat_write_is_one_attempt_returns_the_reason_and_never_raises():
    client = FakeClient(fail_heartbeat=True)
    reason = ps.write_heartbeat(client, client.proj, ps.Plan(), HOST, "2026-11-20T12:00Z", 1)
    assert "rate limit hit" in reason and client.calls == []
    missing = FakeClient()
    del missing.proj.fields["Last run"]
    assert "run --init" in ps.write_heartbeat(missing, missing.proj, ps.Plan(), HOST, "t", 0)


def test_main_apply_writes_the_heartbeat_last_and_keeps_rc_and_the_error_when_the_heartbeat_fails(monkeypatch, tmp_path, capsys):
    (tmp_path / "registries").mkdir()
    (tmp_path / "registries" / "session_project.yaml").write_text("project: {owner: o, number: 1}\n")
    client = FakeClient(fail_heartbeat=True)
    client.list_items = lambda: []
    client.load_project = lambda: client.proj
    monkeypatch.setattr(ps, "_client", lambda cfg, notes=None: client)
    monkeypatch.setattr(ps, "origin_info", lambda root: ("abc", None))
    monkeypatch.setattr(ps, "read_branch_facts", lambda *a, **k: ([], 0))
    monkeypatch.setattr(ps, "read_open_prs", lambda root, notes, run=None: ps.PrList())
    monkeypatch.setattr(pc, "apply_plan", lambda *a, **k: (["update TCK-1: set Status"], ["update TCK-1: set Source"], "update TCK-1: set Source: boom"))
    assert ps.main(["--root", str(tmp_path), "--apply"]) == 1  # the plan's stop decides rc, not the heartbeat
    err = capsys.readouterr().err
    assert "heartbeat: not written (rate limit hit)" in err and "error: update TCK-1: set Source: boom" in err
    data = ps.read_last_run()
    assert data["rc"] == 1 and data["error"].endswith("boom") and "rate limit hit" in data["heartbeat"] and data["done"] == 1 and data["left"] == 1


def test_the_stale_host_flag_reports_other_hosts_only_and_changes_nothing():
    beat = {"Title": ps.HEARTBEAT_TITLE, "_item_id": "H", "Last run": "ubuntu: 2026-11-18T12:00Z rc=0; u24desktop: 2026-11-01T00:00Z rc=0"}
    plan = plan_for({}, items=[beat])
    assert len(plan.stale_hosts) == 1 and plan.stale_hosts[0].startswith("ubuntu (last run 2026-11-18T12:00Z rc=0")
    assert f"stale-host: {plan.stale_hosts[0]}" in plan.notes and plan.creates == [] and plan.updates == [] and plan.archives == []
    fresh = plan_for({}, items=[{**beat, "Last run": "ubuntu: 2026-11-20T11:00Z rc=0"}])
    assert fresh.stale_hosts == []


def test_the_heartbeat_item_is_never_archived_or_counted_as_a_ticket_though_it_has_no_ticket_id():
    beat = {"Title": ps.HEARTBEAT_TITLE, "_item_id": "H", "Last run": ""}
    stray = {"Title": "hand made", "Ticket ID": "", "_item_id": "S"}
    plan = plan_for({}, items=[beat, stray])
    assert plan.archives == [("hand made", "no Ticket ID")] and plan.archive_item_ids == ["S"] and plan.heartbeats == [beat]


def test_convergence_a_then_b_then_a_over_all_lanes_reaches_nothing_to_do():
    main = {"TCK-1": [copy("TCK-1", areas=["src/core/state.py"])], "TCK-2": [copy("TCK-2", areas=["tools/sessions/route.py"])]}
    items = []
    for host in ("u24desktop", "ubuntu", "u24desktop"):
        plan = plan_for(main, host=host, items=items)
        last = plan
        by_id = {i["Ticket ID"]: i for i in items}
        for d in plan.creates:
            by_id[d["Ticket ID"]] = {**d, "_item_id": "I-" + d["Ticket ID"], "_draft_id": "D"}
        for d, _ in plan.updates:
            by_id[d["Ticket ID"]] = d
        items = list(by_id.values())
    assert last.creates == [] and last.updates == [] and last.archives == []
    assert {i["Ticket ID"]: i["Domain"] for i in items} == {"TCK-1": "rpg", "TCK-2": "agent-working"}


def test_the_header_says_what_the_fetch_did():
    for label in ("no fetch", "fetched", "fetch FAILED"):
        assert f", {label})" in ps.render(ps.Plan(), HOST, "abcdef123", 0.5, 0, 0, 0, fetch=label).splitlines()[0]
    assert ", no fetch)" in ps.render(ps.Plan(), HOST, "abcdef123", 0.5, 0, 0, 0).splitlines()[0]


def test_a_branch_with_no_registered_domain_has_seat_plain_unknown_not_unknown_seat_not_recorded():
    fact = ps.BranchFact(HOST, "free-meal-step4", "/wt", *ps.attribute("free-meal-step4", [], DOMAINS), (copy("TCK-7", "inprogress"),))
    plan = plan_for({"TCK-7": [copy("TCK-7", "inprogress")]}, [fact])
    assert plan.creates[0]["Seat"] == "unknown" and plan.creates[0]["Domain"] == "unknown"


# ---- Tier leading token and the whole-plan option check
def _tier_item(tier):
    c = ps.TicketCopy("TCK-T", "todos", f"{T}/todos/TCK-T.md", "t", tier)
    return ps.derive_item("TCK-T", [c], [], [], None, HOST, "s", None, extras())


def test_a_provisional_tier_is_its_leading_token_and_a_junk_tier_is_empty_with_a_finding():
    item, findings = _tier_item("standard (provisional)")
    assert item["Tier"] == "standard" and not any("tier" in f for f in findings)
    assert _tier_item("epic")[0]["Tier"] == "epic" and _tier_item("")[0]["Tier"] == ""
    item, findings = _tier_item("standardish")
    assert item["Tier"] == "" and any("TCK-T: tier 'standardish' is not one of hotfix, standard, epic: Tier left empty" in f for f in findings)


def _plan_with(creates=(), updates=()):
    return SimpleNamespace(creates=list(creates), updates=list(updates), archives=[], archive_item_ids=[])


def test_check_plan_options_names_every_bad_select_value_in_creates_and_changed_update_fields():
    project = _project(domain_type="SINGLE_SELECT")
    project.fields["Domain"] = pc.ProjectField("F_Domain", "Domain", "SINGLE_SELECT", tuple((n, f"O_{n}") for n in WANTED))
    ok = {"Ticket ID": "TCK-OK", "Tier": "standard", "Status": "To do", "Domain": "rpg", "Layer": "combat", "Priority": "P1"}
    bad_create = {**ok, "Ticket ID": "TCK-A", "Tier": "standard (provisional)", "Priority": "P9"}
    bad_update = {**ok, "Ticket ID": "TCK-B", "Layer": "nonesuch", "Tier": "weird"}
    plan = _plan_with([ok, bad_create], [(bad_update, ["Layer"]), ({**ok, "Ticket ID": "TCK-C", "Tier": "weird"}, ["Status"])])
    assert pc.check_plan_options(project, plan) == ["TCK-A Tier 'standard (provisional)'", "TCK-A Priority 'P9'", "TCK-B Layer 'nonesuch'"]
    assert pc.check_plan_options(project, _plan_with([ok])) == []


def test_apply_skips_the_item_with_a_value_that_has_no_option_and_names_every_problem():
    # was: the whole run was refused before the first mutation (TCK-20261119-PROJECT-SYNC-APPLY-SKIPS-ITEMS-WITH-A-MISSING-STATUS-OPTION-...): now only that item is left alone
    fake = FakeClient()
    project = _project(domain_type="SINGLE_SELECT")
    bad = {"Ticket ID": "TCK-A", "Title": "t", "Body": "b", "Tier": "weird", "Priority": "P9", "Status": "To do"}
    plan = _plan_with([bad])
    done, not_done, error = pc.apply_plan(fake, project, plan)
    assert error is None and done == [] and fake.calls == []  # the only item was skipped: nothing written
    assert plan.skipped == {"TCK-A": ["Tier 'weird'", "Priority 'P9'"]}


def test_a_live_dry_run_prints_apply_would_refuse_findings_and_nothing_else_changes(monkeypatch, tmp_path, capsys):
    (tmp_path / "registries").mkdir()
    (tmp_path / "registries" / "session_project.yaml").write_text("project: {owner: o, number: 1}\n")
    project = _project(domain_type="SINGLE_SELECT")
    project.fields["Domain"] = pc.ProjectField("F_Domain", "Domain", "SINGLE_SELECT", tuple((n, f"O_{n}") for n in WANTED))
    client = SimpleNamespace(list_items=lambda: [], load_project=lambda: project)
    monkeypatch.setattr(ps, "_client", lambda cfg, notes=None: client)
    monkeypatch.setattr(ps, "origin_info", lambda root: ("abc", None))
    monkeypatch.setattr(ps, "read_branch_facts", lambda *a, **k: ([], 0))
    monkeypatch.setattr(ps, "read_open_prs", lambda root, notes, run=None: ps.PrList())
    monkeypatch.setattr(ps, "read_main_index", lambda root: {"TCK-W": [("todos", f"{T}/todos/TCK-W.md")]})
    monkeypatch.setattr(ps, "read_main_copy", lambda root, path, **k: ps.TicketCopy("TCK-W", "todos", path, "w", "standard"))
    monkeypatch.setattr(ps, "done_date", lambda root, path: None)
    assert ps.main(["--root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "create  TCK-W" in out and "finding: apply would skip" not in out  # Tier 'standard' and Domain 'unassigned' are options
    project.fields["Domain"] = pc.ProjectField("F_Domain", "Domain", "SINGLE_SELECT", (("rpg", "O_rpg"),))  # Domain options lack the derived value
    assert ps.main(["--root", str(tmp_path)]) == 0
    assert "finding: apply would skip the item (no option on the Project; run --init): TCK-W Domain 'unassigned'" in capsys.readouterr().out
