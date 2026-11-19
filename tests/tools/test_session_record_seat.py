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
