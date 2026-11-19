"""Record which seat (a role or one of its session instances) holds a hand-added worktree: the same record `launch.py --worktree` writes
(TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED, part (a)).

    python3 tools/sessions/record_seat.py <worktree> <seat> [--replace] [--dry-run] [--state-root DIR]
    python3 tools/sessions/record_seat.py --list [--state-root DIR]     # read only: every explicit record, with whether its worktree is live

It calls `state.write_bound_worktree(..., explicit=True)`, the writer the launcher uses, so status.py (`writing_in`) and project_sync
(`_worktree_for`) read it the same way. It never guesses a seat from a branch name and never edits the record by hand. `<seat>` is a roster role or an instance
`<role>-<n>` with 2 <= n <= that role's `placement.max_sessions` (`rpg-implementer-3`, `rpg-implementer-ubuntu-2`): the name is the record's key and is stored and shown exactly as
given, never collapsed to the role; one record per instance. It refuses
an unknown seat (an instance number outside 2..max_sessions, `-1`, a suffix on a one-session role), a path that is not a linked git worktree, a worktree already recorded for another seat, and a seat whose existing
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
from tools.sessions.launch import EXIT_REFUSED, EXIT_USAGE, _worktree_entries, main_checkout, resolve_target  # noqa: E402
from tools.sessions.resolve import instance_ids  # noqa: E402
from tools.sessions.roster import REPO_ROOT, Roster, load_roster  # noqa: E402


def record_seat(roster: Roster, worktrees: list[Path], main: Path, sroot: Path, worktree: Path, seat: str,
                replace: bool = False, dry_run: bool = False) -> tuple[int, list[str]]:
    """(exit code, lines). `worktrees` are the repo's linked worktree paths; `main` is the main checkout."""
    if resolve_target(seat, roster) is None:
        multi = {r.role: r.max_sessions for r in roster.roles if r.max_sessions > 1}
        hint = "; roles with instances: " + ", ".join(f"{k}-2..{k}-{n}" for k, n in sorted(multi.items())) if multi else ""
        return EXIT_USAGE, [f"unknown seat {seat!r}: a roster role or an instance <role>-<n> with 2 <= n <= max_sessions{hint}"]
    wt = worktree.resolve()
    if wt == main.resolve():
        return EXIT_REFUSED, [f"{wt} is the main checkout, not a lane worktree: nothing recorded"]
    if wt not in {p.resolve() for p in worktrees} or not wt.is_dir():
        return EXIT_REFUSED, [f"{wt} is not a live linked git worktree of this repository: nothing recorded"]
    for other in (name for r in roster.roles for name in instance_ids(r.role, r.max_sessions)):  # every role AND every instance, so a base role and an instance never share a worktree
        bound = st.read_bound_worktree(sroot, other) if sroot.is_dir() else None
        if other != seat and bound and bound[1] and Path(bound[0]).resolve() == wt:
            return EXIT_REFUSED, [f"{wt} is already recorded for seat {other}: refusing to record it for {seat} (remove the other record first)"]
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


def list_records(roster: Roster, sroot: Path) -> list[str]:
    """One line per explicit record of any role or instance: `<seat>  <path>  live|missing`; read only. The count of instance-keyed lines is the number of
    instance records this host's readers will show."""
    lines = []
    for name in (n for r in roster.roles for n in instance_ids(r.role, r.max_sessions)):
        bound = st.read_bound_worktree(sroot, name) if sroot.is_dir() else None
        if bound and bound[1]:
            lines.append(f"{name}  {bound[0]}  {'live' if Path(bound[0]).is_dir() else 'missing'}")
    return lines


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("worktree", nargs="?", help="path of the linked git worktree")
    ap.add_argument("seat", nargs="?", help="the seat that holds it: a role, or an instance <role>-<n>")
    ap.add_argument("--list", action="store_true", help="read only: print every explicit record and whether its worktree is live")
    ap.add_argument("--replace", action="store_true", help="overwrite the seat's existing record for a different live worktree")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--state-root", type=Path, help="write the record under this existing directory instead of the repo's own session-state (a scratch root for a dry run)")
    a = ap.parse_args(argv)
    root = REPO_ROOT
    if not a.list and not (a.worktree and a.seat):
        ap.error("give <worktree> <seat>, or --list")
    try:
        if a.state_root is not None and not a.state_root.is_dir():
            print(f"record_seat: --state-root {a.state_root} is not an existing directory: nothing recorded, no fallback to the real state root.", file=sys.stderr)
            return EXIT_USAGE
        sroot = a.state_root if a.state_root is not None else st.state_root(root)
        paths = [Path(e["worktree"]) for e in _worktree_entries(root) if e.get("worktree")]
        if a.list:
            lines = list_records(load_roster(root), sroot)
            print("\n".join(lines) if lines else "no explicit seat records", file=sys.stdout)
            print(f"{len(lines)} record(s) under {sroot}", file=sys.stderr)
            return 0
        code, lines = record_seat(load_roster(root), paths, main_checkout(root), sroot, Path(a.worktree), a.seat, a.replace, a.dry_run)
    except (st.StateError, OSError) as exc:
        print(f"record_seat: {exc}", file=sys.stderr)
        return EXIT_USAGE
    print("\n".join(lines), file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main())
