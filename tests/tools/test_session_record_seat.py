"""TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED, part (a): tools/sessions/record_seat.py writes the record
launch.py --worktree writes. Real state files in tmp, no git needed (the worktree list is passed in)."""
from pathlib import Path

from tools.sessions import record_seat as rs
from tools.sessions import state as st
from tools.sessions.launch import EXIT_REFUSED, EXIT_USAGE
from tools.sessions.roster import load_roster
from tools.sessions.status import seat_infos

ROSTER = load_roster(Path(__file__).resolve().parents[2])
SEAT, OTHER = "rpg-implementer", "rpg-planner"


def setup(tmp_path):
    main, wt1, wt2 = tmp_path / "main", tmp_path / "lane1", tmp_path / "lane2"
    for d in (main, wt1, wt2):
        d.mkdir(exist_ok=True)
    return main, wt1, wt2, tmp_path / "state"


def go(tmp_path, wt, seat, **kw):
    main, wt1, wt2, sroot = setup(tmp_path)
    sroot.mkdir(exist_ok=True)
    return rs.record_seat(ROSTER, [main, wt1, wt2], main, sroot, wt, seat, **kw)


def test_records_the_same_record_the_launcher_writes_and_status_reads_it_as_writing_in(tmp_path):
    main, wt1, _, sroot = setup(tmp_path)
    code, lines = go(tmp_path, wt1, SEAT)
    assert code == 0 and lines[0].startswith("recorded:")
    assert st.read_bound_worktree(sroot, SEAT) == (str(wt1.resolve()), True)  # (path, explicit): exactly write_bound_worktree(..., True)
    shown = next(s for s in seat_infos(ROSTER, sroot) if s.role == SEAT)
    assert shown.writing_in == str(wt1.resolve())


def test_refuses_an_unknown_seat_and_writes_nothing(tmp_path):
    main, wt1, _, sroot = setup(tmp_path)
    code, lines = go(tmp_path, wt1, "no-such-seat")
    assert code == EXIT_USAGE and "unknown seat" in lines[0] and not any(sroot.glob("*"))


def test_refuses_the_main_checkout_and_a_path_that_is_not_a_worktree(tmp_path):
    main, wt1, _, sroot = setup(tmp_path)
    assert go(tmp_path, main, SEAT)[0] == EXIT_REFUSED
    code, lines = go(tmp_path, tmp_path / "elsewhere", SEAT)
    assert code == EXIT_REFUSED and "not a live linked git worktree" in lines[0] and st.read_bound_worktree(sroot, SEAT) is None


def test_refuses_a_worktree_already_recorded_for_another_seat(tmp_path):
    main, wt1, _, sroot = setup(tmp_path)
    assert go(tmp_path, wt1, OTHER)[0] == 0
    code, lines = go(tmp_path, wt1, SEAT)
    assert code == EXIT_REFUSED and OTHER in lines[0] and st.read_bound_worktree(sroot, SEAT) is None


def test_a_second_worktree_for_the_same_seat_needs_replace_and_the_same_one_again_is_a_no_op(tmp_path):
    main, wt1, wt2, sroot = setup(tmp_path)
    assert go(tmp_path, wt1, SEAT)[0] == 0
    assert "already recorded" in go(tmp_path, wt1, SEAT)[1][0]
    code, lines = go(tmp_path, wt2, SEAT)
    assert code == EXIT_REFUSED and "--replace" in lines[0] and st.read_bound_worktree(sroot, SEAT)[0] == str(wt1.resolve())
    assert go(tmp_path, wt2, SEAT, replace=True)[0] == 0 and st.read_bound_worktree(sroot, SEAT)[0] == str(wt2.resolve())


def test_dry_run_writes_nothing(tmp_path):
    main, wt1, _, sroot = setup(tmp_path)
    code, lines = go(tmp_path, wt1, SEAT, dry_run=True)
    assert code == 0 and lines[0].startswith("would record") and st.read_bound_worktree(sroot, SEAT) is None


# ---- --state-root: a scratch root for a dry run that must not touch live records
def _snapshot(root):
    return sorted((str(p.relative_to(root)), p.stat().st_mtime_ns) for p in root.rglob("*")) if root.is_dir() else None


def test_state_root_flag_writes_only_under_the_given_root_and_leaves_the_real_root_untouched(tmp_path, monkeypatch):
    main, wt1, _, _ = setup(tmp_path)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    real = st.state_root(rs.REPO_ROOT)
    before = _snapshot(real)
    monkeypatch.setattr(rs, "_worktree_entries", lambda root: [{"worktree": str(wt1)}])
    monkeypatch.setattr(rs, "main_checkout", lambda root: main)
    assert rs.main(["--state-root", str(scratch), str(wt1), SEAT]) == 0
    assert st.read_bound_worktree(scratch, SEAT) == (str(wt1.resolve()), True)
    assert _snapshot(real) == before  # the real seat-state directory is byte-for-byte as it was


def test_state_root_flag_pointing_at_nothing_is_a_usage_error_not_a_fallback(tmp_path, capsys):
    main, wt1, _, _ = setup(tmp_path)
    real = st.state_root(rs.REPO_ROOT)
    before = _snapshot(real)
    assert rs.main(["--state-root", str(tmp_path / "missing"), str(wt1), SEAT]) == EXIT_USAGE
    assert "no fallback" in capsys.readouterr().err and _snapshot(real) == before


# ---- instances of a multi-session role (TCK-20261119-RECORD-SEAT-ACCEPTS-A-SESSION-INSTANCE-OF-A-MULTI-SESSION-ROLE)
import pytest  # noqa: E402

INSTANCES = ("rpg-implementer-2", "rpg-implementer-3", "rpg-implementer-4", "rpg-implementer-ubuntu-3")


@pytest.mark.parametrize("name", INSTANCES)
def test_an_instance_is_stored_and_shown_exactly_as_given_never_collapsed_to_the_role(tmp_path, name):
    main, wt1, _, sroot = setup(tmp_path)
    assert go(tmp_path, wt1, name)[0] == 0
    assert st.read_bound_worktree(sroot, name) == (str(wt1.resolve()), True)
    role = name.rsplit("-", 1)[0]
    assert st.read_bound_worktree(sroot, role) is None  # nothing was written under the base role
    shown = {s.role: s for s in seat_infos(ROSTER, sroot)}
    assert shown[name].writing_in == str(wt1.resolve()) and name in shown


@pytest.mark.parametrize("name", ["rpg-implementer-1", "rpg-implementer-0", "rpg-implementer-5", "rpg-implementer-x", "rpg-implementer-ubuntu-5",
                                  "rpg-planner-2", "rpg-implementer-03", "rpg-implementer--3", "rpg-implementer-3-4"])
def test_names_outside_the_instances_the_roster_allows_are_refused_and_write_nothing(tmp_path, name):  # max_sessions is read from the roster: 4 for the two implementers, 1 for the rest
    main, wt1, _, sroot = setup(tmp_path)
    code, lines = go(tmp_path, wt1, name)
    assert code == EXIT_USAGE and "unknown seat" in lines[0] and "rpg-implementer-2.." in lines[0] and not any(sroot.glob("*"))


def test_two_instances_of_one_role_each_hold_their_own_worktree_but_no_worktree_holds_two_seats(tmp_path):
    main, wt1, wt2, sroot = setup(tmp_path)
    assert go(tmp_path, wt1, "rpg-implementer-2")[0] == 0 and go(tmp_path, wt2, "rpg-implementer-3")[0] == 0  # one record per instance
    code, lines = go(tmp_path, wt1, "rpg-implementer-3")
    assert code == EXIT_REFUSED and "rpg-implementer-2" in lines[0]  # a worktree already recorded for another instance
    code, lines = go(tmp_path, wt1, "rpg-implementer")
    assert code == EXIT_REFUSED and "rpg-implementer-2" in lines[0]  # base role onto an instance's worktree
    code, lines = go(tmp_path, wt2, "rpg-implementer-2")
    assert code == EXIT_REFUSED and "rpg-implementer-3" in lines[0]  # the other instance's worktree is not taken either


def test_an_instance_onto_a_base_role_worktree_is_refused(tmp_path):
    main, wt1, _, sroot = setup(tmp_path)
    assert go(tmp_path, wt1, "rpg-implementer")[0] == 0
    code, lines = go(tmp_path, wt1, "rpg-implementer-4")
    assert code == EXIT_REFUSED and "rpg-implementer" in lines[0] and st.read_bound_worktree(sroot, "rpg-implementer-4") is None


def test_list_prints_every_explicit_record_by_its_own_name_with_liveness(tmp_path):
    main, wt1, wt2, sroot = setup(tmp_path)
    go(tmp_path, wt1, "rpg-implementer-3")
    st.write_bound_worktree(sroot, "rpg-implementer-4", tmp_path / "gone", True)
    st.write_bound_worktree(sroot, "rpg-implementer-2", wt2, False)  # a default (non-explicit) record is not listed
    lines = rs.list_records(ROSTER, sroot)
    assert lines == [f"rpg-implementer-3  {wt1.resolve()}  live", f"rpg-implementer-4  {tmp_path / 'gone'}  missing"]
