"""TCK-20261115-PROJECT-SYNC-FILED-DATE-AND-BACKLOG-VIEW: the `Filed` date field and hash v4. No network."""
from dataclasses import replace

from tests.tools.test_session_project_sync_all_lanes import HOST, WANTED, FakeInit, _project, copy, plan_for
from tools.sessions import project_client as pc
from tools.sessions import project_sync as ps


def _with(c, date):
    return replace(c, date=date)


def test_filed_is_the_frontmatter_date_and_joins_the_v4_hash():
    plan = plan_for({"TCK-1": [copy("TCK-1", "todos")]})
    d = plan.creates[0]
    assert d["Filed"] == "2026-11-15" and d["Sync hash"] == ps.sync_hash(d) and d["Sync hash"].startswith("v5:")
    assert "Filed" in ps.HASH_VERSIONS["v4"] and "Filed" not in ps.HASH_VERSIONS["v3"]


def test_a_bad_or_missing_date_leaves_filed_empty_and_adds_a_finding():
    for raw, word in (("", "missing"), ("2026-13-45", "not a valid"), ("next week", "not a valid")):
        plan = plan_for({"TCK-1": [_with(copy("TCK-1", "todos"), raw)]})
        assert plan.creates[0]["Filed"] == ""
        assert any("TCK-1" in f and word in f and "Filed left empty" in f for f in plan.findings)


def test_the_v3_to_v4_migration_rewrites_filed_and_hash_with_no_hand_edits_and_the_keep_rule_keeps_it():
    first = plan_for({"TCK-1": [copy("TCK-1", "todos")]}).creates[0]
    v3 = {k: v for k, v in first.items() if k not in ("Filed", "Body", "Source", "_code_unassigned")}
    v3["Sync hash"] = ps.sync_hash(v3, "v3")  # what the P3b load stored
    v3["Source"] = "abc"
    plan = plan_for({"TCK-1": [copy("TCK-1", "todos")]}, items=[{**v3, "_item_id": "I1", "_draft_id": "D1"}])
    assert plan.hand_edits == [] and len(plan.updates) == 1
    assert plan.updates[0][1] == ["Filed"] and plan.updates[0][0]["Sync hash"].startswith("v5:")
    settled = plan_for({"TCK-1": [copy("TCK-1", "todos")]}, items=[{**first, "_item_id": "I1", "_draft_id": "D1"}])
    assert settled.updates == [] and settled.hand_edits == []


def test_init_creates_a_date_field_a_second_init_does_nothing_and_a_wrong_type_is_refused():
    base = _project()
    del base.fields["Filed"]
    fake = FakeInit(base)
    lines, code = pc.init_fields(fake, ps.STATUSES, layers=("combat",), domains=WANTED)
    assert code == 0 and ("create_date", "Filed") in fake.calls and "created: Filed" in lines
    again = FakeInit(_project(extra=[pc.ProjectField("F_Filed", "Filed", "DATE")]))
    lines, code = pc.init_fields(again, ps.STATUSES, layers=("combat",), domains=WANTED)
    assert not any(c[0] == "create_date" for c in again.calls) and "left alone: Filed" in lines
    wrong = FakeInit(_project(extra=[pc.ProjectField("F_Filed", "Filed", "TEXT")]))
    lines, code = pc.init_fields(wrong, ps.STATUSES, layers=("combat",), domains=WANTED)
    assert code == 1 and wrong.calls == [] and "wanted DATE" in lines[0]


def test_apply_writes_a_date_value_and_clears_an_empty_one():
    calls = []

    class C:
        def set_date(self, pid, iid, fid, v): calls.append(("date", iid, v))
        def clear_value(self, pid, iid, fid): calls.append(("clear", iid))
        def set_text(self, *a): pass
        def set_option(self, *a): pass
        def add_draft(self, *a): return "I", "D"
    proj = _project(extra=[pc.ProjectField("F_Filed", "Filed", "DATE"), pc.ProjectField("F_Last", "Last run", "TEXT"),
                           pc.ProjectField("F_Domain", "Domain", "SINGLE_SELECT", tuple((n, f"O_{n}") for n in WANTED))])
    plan = plan_for({"TCK-1": [copy("TCK-1", "todos")]})
    plan.updates.append(({**plan.creates[0], "_item_id": "I1", "_draft_id": "D1", "Filed": ""}, ["Filed"]))
    plan.creates[0]["Filed"] = "2026-11-15"
    done, not_done, err = pc.apply_plan(C(), proj, plan, lambda d: "b")
    assert err is None and ("date", "I", "2026-11-15") in calls and ("clear", "I1") in calls
