"""Record which seat holds a hand-added worktree: the same record `launch.py --worktree` writes
(TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED, part (a)).

    python3 tools/sessions/record_seat.py <worktree> <seat> [--replace] [--dry-run]

It calls `state.write_bound_worktree(..., explicit=True)`, the writer the launcher uses, so status.py (`writing_in`) and project_sync
(`_worktree_for`) read it the same way. It never guesses a seat from a branch name and never edits the record by hand. It refuses
an unknown seat, a path that is not a linked git worktree, a worktree already recorded for another seat, and a seat whose existing
record points at a different live worktree (the record holds ONE path per seat; `--replace` overwrites it). Each host's records are
its own: a u24 seat runs this on u24 for u24's worktrees.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if __package__ in (None, ""):  # run as `python3 tools/sessions/record_seat.py`: put the repo root on sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.sessions import state as st  # noqa: E402
from tools.sessions.launch import EXIT_REFUSED, EXIT_USAGE, _worktree_entries, main_checkout  # noqa: E402
from tools.sessions.roster import REPO_ROOT, Roster, load_roster  # noqa: E402


def record_seat(roster: Roster, worktrees: list[Path], main: Path, sroot: Path, worktree: Path, seat: str,
                replace: bool = False, dry_run: bool = False) -> tuple[int, list[str]]:
    """(exit code, lines). `worktrees` are the repo's linked worktree paths; `main` is the main checkout."""
    role = next((r for r in roster.roles if r.role == seat), None)
    if role is None:
        return EXIT_USAGE, [f"unknown seat {seat!r}: known seats are {', '.join(sorted(r.role for r in roster.roles))}"]
    wt = worktree.resolve()
    if wt == main.resolve():
        return EXIT_REFUSED, [f"{wt} is the main checkout, not a lane worktree: nothing recorded"]
    if wt not in {p.resolve() for p in worktrees} or not wt.is_dir():
        return EXIT_REFUSED, [f"{wt} is not a live linked git worktree of this repository: nothing recorded"]
    for other in roster.roles:
        bound = st.read_bound_worktree(sroot, other.role) if sroot.is_dir() else None
        if other.role != seat and bound and bound[1] and Path(bound[0]).resolve() == wt:
            return EXIT_REFUSED, [f"{wt} is already recorded for seat {other.role}: refusing to record it for {seat} (remove the other record first)"]
    existing = st.read_bound_worktree(sroot, seat) if sroot.is_dir() else None
    if existing and existing[1]:
        old = Path(existing[0])
        if old.resolve() == wt:
            return 0, [f"already recorded: {seat} -> {wt}"]
        if old.is_dir() and not replace:
            return EXIT_REFUSED, [f"seat {seat} already has a recorded worktree {old} (one record per seat): refusing to overwrite it; pass --replace to move it to {wt}"]
    if dry_run:
        return 0, [f"would record: {seat} -> {wt}"]
    st.write_bound_worktree(sroot, seat, os.path.realpath(wt), True)
    return 0, [f"recorded: {seat} -> {wt} (status.py shows it as `writing in`; project_sync names the seat on this worktree's branch)"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("worktree", help="path of the linked git worktree")
    ap.add_argument("seat", help="the seat (role name) that holds it")
    ap.add_argument("--replace", action="store_true", help="overwrite the seat's existing record for a different live worktree")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--state-root", type=Path, help="write the record under this existing directory instead of the repo's own session-state (a scratch root for a dry run)")
    a = ap.parse_args(argv)
    root = REPO_ROOT
    try:
        if a.state_root is not None and not a.state_root.is_dir():
            print(f"record_seat: --state-root {a.state_root} is not an existing directory: nothing recorded, no fallback to the real state root.", file=sys.stderr)
            return EXIT_USAGE
        sroot = a.state_root if a.state_root is not None else st.state_root(root)
        paths = [Path(e["worktree"]) for e in _worktree_entries(root) if e.get("worktree")]
        code, lines = record_seat(load_roster(root), paths, main_checkout(root), sroot, Path(a.worktree), a.seat, a.replace, a.dry_run)
    except (st.StateError, OSError) as exc:
        print(f"record_seat: {exc}", file=sys.stderr)
        return EXIT_USAGE
    print("\n".join(lines), file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main())
