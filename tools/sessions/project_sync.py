#!/usr/bin/env python3
"""Derive the GitHub Project items for ticket state, dry run only (TCK-20261112-PROJECT-SYNC-DRY-RUN, P0 of
TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW).

The Project is a generated, read-only VIEW of ticket state: the ticket files stay authoritative. This tool reads ticket files on
origin/main (no fetch), the worktrees and seats of this host (the builders in `tools/sessions/status.py`), each worktree's ticket
changes against the merge base (read-only), and open PRs, then prints the create / update / archive plan. It writes nothing to
GitHub and nothing to the repo; `--apply` and `--init` are P1 and are refused. Every subprocess goes through `_guard`, which only
lets read verbs through.

Status, first match wins (design section 3): Done -> In review -> Blocked -> In progress -> To do. A `todos/` copy on a branch or in a
PR is filing, not progress, and never moves a ticket past To do.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import socket
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

from tools.agent_working_paths import TICKETS
from tools.sessions import state as st
from tools.sessions.launch import _worktree_entries as worktree_entries
from tools.sessions.launch import main_checkout
from tools.sessions.roster import REPO_ROOT, load_roster

# Deliberate reuse of status.py's private `_worktree_for` (seat -> physical worktree): same package, and renaming it would only
# churn status.py's unchanged tests (designer review of plan.md, 2026-11-12).
from tools.sessions.status import _worktree_for, inspect_worktree, seat_infos  # noqa: F401

CONFIG_REL = Path("registries") / "session_project.yaml"
DEFAULTS = {
    "project": {"owner": "PLACEHOLDER", "number": 0},
    "pilot_lanes": ["rpg"],
    "pilot_start": "2026-11-12",
    "done_window_days": 14,
    "stale_host_hours": 24,
}
PR_LIMIT = 300  # the value of ticket_queue.PR_LIMIT: gh's own default is 30
FOLDERS = ("todos", "inprogress", "done")
PROGRESS_FOLDERS = ("inprogress", "done")  # only these count as progress; todos/ on a branch or PR is filing
HASH_FIELDS = ("Title", "Ticket ID", "Status", "Domain", "Seat", "Host", "Branch", "PR", "Tier")
STATUSES = ("To do", "In progress", "In review", "Blocked", "Done")
FILING_SUFFIX = "[filing]"
BODY = "Generated from {path} by tools/sessions/project_sync.py — edits are overwritten."
_TICKET_RE = re.compile(r"(TCK-[A-Z0-9][A-Z0-9-]*)\.md$")
READ_GIT = {"ls-tree", "show", "merge-base", "diff", "status", "log", "rev-parse", "worktree"}

Runner = Callable[[list[str], Path | None], "subprocess.CompletedProcess[str]"]


class WriteRefused(Exception):
    """A command that could write was about to run; the dry run never does."""


def _guard(args: list[str]) -> None:
    """Only read verbs: git ls-tree/show/merge-base/diff/status/log/rev-parse/worktree-list; gh `pr list` and GET `api`."""
    if not args:
        raise WriteRefused("empty command")
    tool, rest = args[0], [a for a in args[1:] if a != "--no-optional-locks"]
    if tool == "git":
        verb = rest[0] if rest else ""
        if verb not in READ_GIT or (verb == "worktree" and rest[1:2] != ["list"]):
            raise WriteRefused(f"git {verb}")
        return
    if tool == "gh":
        if rest[:2] == ["pr", "list"]:
            return
        if rest[:1] == ["api"] and not any(a in ("-X", "--method", "-f", "-F", "--field", "--raw-field", "--input") for a in rest):
            return
        raise WriteRefused("gh " + " ".join(rest[:2]))
    raise WriteRefused(tool)


def run_command(args: list[str], cwd: Path | None = None) -> "subprocess.CompletedProcess[str]":
    _guard(args)
    try:
        return subprocess.run(args, cwd=None if cwd is None else str(cwd), capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        return subprocess.CompletedProcess(args, 1, "", str(exc))


# ---------------------------------------------------------------- data


@dataclass(frozen=True)
class TicketCopy:
    id: str
    folder: str
    path: str
    title: str = ""
    tier: str = ""
    blocked: bool = False
    date: str = ""


@dataclass(frozen=True)
class BranchFact:
    host: str
    branch: str
    worktree: str
    seat: str
    domain: str
    copies: tuple[TicketCopy, ...]


@dataclass(frozen=True)
class PrFact:
    number: int
    url: str
    paths: frozenset[str]  # ticket file paths the PR adds or changes


@dataclass
class Plan:
    creates: list[dict] = field(default_factory=list)
    updates: list[tuple[dict, list[str]]] = field(default_factory=list)
    archives: list[tuple[str, str]] = field(default_factory=list)  # (ticket id or item title, reason)
    hand_edits: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- ticket files


def ticket_id_of(path: str) -> str | None:
    m = _TICKET_RE.search(path)
    return m.group(1) if m else None


def folder_of(path: str) -> str | None:
    prefix = TICKETS.as_posix() + "/"
    if not path.startswith(prefix):
        return None
    head = path[len(prefix):].split("/", 1)[0]
    return head if head in FOLDERS else None


def parse_copy(path: str, text: str) -> TicketCopy:
    def section(name: str) -> str:
        m = re.search(rf"^## {name}\s*\n+([^\n#][^\n]*)", text, re.M)
        return m.group(1).strip() if m else ""

    fm = re.search(r"^date:\s*(\S+)", text, re.M)
    return TicketCopy(
        id=ticket_id_of(path) or "", folder=folder_of(path) or "", path=path, title=section("Title"), tier=section("Tier").lower(),
        blocked=section("Status").upper() == "BLOCKED", date=fm.group(1) if fm else "",
    )


def read_main_index(root: Path, run: Runner = run_command, ref: str = "origin/main") -> dict[str, list[tuple[str, str]]]:
    """ticket id -> [(folder, path)] on `ref`. Names only: the 3,000+ done files are never opened."""
    out = run(["git", "ls-tree", "-r", "--name-only", ref, "--", TICKETS.as_posix()], root)
    index: dict[str, list[tuple[str, str]]] = {}
    for path in out.stdout.splitlines() if out.returncode == 0 else []:
        tid, folder = ticket_id_of(path), folder_of(path)
        if tid and folder:
            index.setdefault(tid, []).append((folder, path))
    return index


def read_main_copy(root: Path, path: str, run: Runner = run_command, ref: str = "origin/main") -> TicketCopy:
    shown = run(["git", "show", f"{ref}:{path}"], root)
    return parse_copy(path, shown.stdout if shown.returncode == 0 else "")


def origin_info(root: Path, run: Runner = run_command, ref: str = "origin/main") -> tuple[str, float | None]:
    sha = run(["git", "rev-parse", ref], root)
    when = run(["git", "log", "-1", "--format=%ct", ref], root)
    stamp = float(when.stdout.strip()) if when.returncode == 0 and when.stdout.strip().isdigit() else None
    return (sha.stdout.strip() if sha.returncode == 0 else "unknown"), stamp


def done_date(root: Path, path: str, run: Runner = run_command, ref: str = "origin/main") -> datetime | None:
    """When the ticket file reached done/ on `ref` (git, not frontmatter: the `date` field is the filing date)."""
    out = run(["git", "log", "-1", "--diff-filter=A", "--format=%cI", ref, "--", path], root)
    text = out.stdout.strip() if out.returncode == 0 else ""
    try:
        return datetime.fromisoformat(text) if text else None
    except ValueError:
        return None


# ---------------------------------------------------------------- worktrees


def attribute(branch: str, seats: list[tuple[str, str]]) -> tuple[str, str]:
    """(Seat, Domain): the status.py seat mapping; else `<domain> (unmapped)` from the branch prefix; else `unknown`."""
    if seats:
        return "/".join(s for s, _ in seats), seats[0][1]
    prefix = branch.split("-", 1)[0]
    return (f"{prefix} (unmapped)", prefix) if "-" in branch else ("unknown", "")


def read_branch_facts(root: Path, host: str, lanes_note: list[str], run: Runner = run_command) -> tuple[list[BranchFact], int]:
    """(branch facts for this host, count of detached worktrees skipped). Read-only: status.py's builders, then per worktree
    `git diff --name-status <merge-base> HEAD` and `git status --porcelain`, both limited to the ticket folders."""
    roster = load_roster(root)
    main = main_checkout(root)
    try:
        state_root = st.state_root(root)
    except st.StateError:
        state_root = root / ".git" / "session-roles-unavailable"
    infos = [inspect_worktree(e, main, lambda b, c: "none", lambda p: 0) for e in worktree_entries(root) if e.get("worktree")]
    seat_of: dict[Path, list[tuple[str, str]]] = {}
    for role in roster.roles:
        wt = _worktree_for(role, infos, main, state_root)
        if wt is not None:
            seat_of.setdefault(wt.path.resolve(), []).append((role.role, role.domain))
    facts, detached = [], 0
    for info in infos:
        if info.prunable or info.is_main and info.branch in (None, "main"):
            continue
        copies = _worktree_ticket_copies(info.path, run)
        if info.branch is None:
            detached += 1
            if copies:
                lanes_note.append(f"unattributed: detached worktree {info.path} changes {', '.join(sorted(c.id for c in copies))}")
            continue
        if not copies:
            continue
        seat, domain = attribute(info.branch, seat_of.get(info.path.resolve(), []))
        facts.append(BranchFact(host, info.branch, str(info.path), seat, domain, tuple(copies)))
    return facts, detached


def _worktree_ticket_copies(wt: Path, run: Runner) -> list[TicketCopy]:
    folder = TICKETS.as_posix()
    base = run(["git", "--no-optional-locks", "merge-base", "origin/main", "HEAD"], wt)
    changed: set[str] = set()
    if base.returncode == 0 and base.stdout.strip():
        diff = run(["git", "--no-optional-locks", "diff", "--name-status", base.stdout.strip(), "HEAD", "--", folder], wt)
        for line in diff.stdout.splitlines() if diff.returncode == 0 else []:
            parts = line.split("\t")
            if parts and parts[0][:1] in ("A", "M", "R", "C") and len(parts) >= 2:
                changed.add(parts[-1])
    # -z: NUL-separated entries, no quoting and no line splitting, so a leading-space ` M <path>` (unstaged-only) is read exactly
    status = run(["git", "--no-optional-locks", "status", "--porcelain", "-z", "--untracked-files=all", "--", folder], wt)
    on_disk: set[str] = set()
    entries = status.stdout.split("\0") if status.returncode == 0 else []
    i = 0
    while i < len(entries):
        entry = entries[i]
        i += 1
        if len(entry) < 4:
            continue
        code, path = entry[:2], entry[3:]
        if code[0] in "RC":
            i += 1  # the next entry is the rename or copy source
        if "D" not in code:
            changed.add(path)
            on_disk.add(path)
    out = []
    for path in sorted(changed):
        if not (ticket_id_of(path) and folder_of(path)):
            continue
        if path in on_disk and (wt / path).is_file():
            text = (wt / path).read_text(encoding="utf-8", errors="replace")
        else:
            shown = run(["git", "show", f"HEAD:{path}"], wt)
            text = shown.stdout if shown.returncode == 0 else ""
        out.append(parse_copy(path, text))
    return out


# ---------------------------------------------------------------- pull requests


def read_open_prs(root: Path, notes: list[str], run: Runner = run_command) -> list[PrFact] | None:
    """Open PRs and the ticket files each adds or changes; GETs only. None when gh cannot answer (rule 2 is then skipped)."""
    listed = run(["gh", "pr", "list", "--state", "open", "--limit", str(PR_LIMIT), "--json", "number,url"], root)
    if listed.returncode != 0:
        notes.append("open PRs unknown (gh failed): rule 2 (In review) is skipped this run")
        return None
    try:
        prs = json.loads(listed.stdout or "[]")
    except ValueError:
        notes.append("open PRs unknown (gh answered badly): rule 2 (In review) is skipped this run")
        return None
    if len(prs) >= PR_LIMIT:
        notes.append(f"gh returned {PR_LIMIT} open PRs, the limit: some PRs may be missing")
    facts = []
    for pr in prs:
        files = run(["gh", "api", "--paginate", f"repos/{{owner}}/{{repo}}/pulls/{pr['number']}/files", "--jq", ".[].filename"], root)
        names = files.stdout.split() if files.returncode == 0 else []
        facts.append(PrFact(int(pr["number"]), pr["url"], frozenset(n for n in names if ticket_id_of(n) and folder_of(n))))
    return facts


# ---------------------------------------------------------------- derivation (pure)


def sync_hash(fields: dict) -> str:
    blob = json.dumps([[k, fields.get(k, "")] for k in HASH_FIELDS], ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _split(value: str) -> list[str]:
    return [p.strip() for p in (value or "").split(",") if p.strip()]


def merge_host_entries(current: str, mine: list[str], tag: str) -> str:
    """Replace only this host's entries (`tag` is `host:` for Branch, the bare host name for Host), keep the other hosts'."""
    kept = [e for e in _split(current) if not (e.startswith(tag) if tag.endswith(":") else e == tag)]
    return ", ".join(sorted(set(kept) | set(mine)))


def derive_status(tid: str, main: list[TicketCopy], branches: list[BranchFact], prs: list[PrFact] | None,
                  other_host_branches: list[str]) -> tuple[str, list[str], list[str]]:
    """(status, PR urls, findings). First match wins; see the module docstring."""
    findings = []
    folders = {c.folder for c in main}
    if len(folders) > 1:
        findings.append(f"{tid}: in two folders on origin/main ({', '.join(sorted(folders))}); the higher status is used")
    if "done" in folders:
        return "Done", [], findings
    review = [pr for pr in prs or [] if any(ticket_id_of(p) == tid and folder_of(p) in PROGRESS_FOLDERS for p in pr.paths)]
    if review:
        return "In review", [pr.url for pr in review], findings
    branch_copies = [c for b in branches for c in b.copies if c.id == tid]
    if any(c.blocked for c in branch_copies) or (not branch_copies and any(c.blocked for c in main)):
        return "Blocked", [], findings
    progressing = any(c.folder in PROGRESS_FOLDERS for c in branch_copies) or any(not e.endswith(FILING_SUFFIX) for e in other_host_branches)
    if progressing:
        return "In progress", [], findings
    if "inprogress" in folders and not branch_copies and not other_host_branches:
        findings.append(f"{tid}: in inprogress/ on origin/main with no branch seen (orphaned in-progress ticket)")
    return "To do", [], findings


def derive_item(tid: str, main: list[TicketCopy], branches: list[BranchFact], prs: list[PrFact] | None, current: dict | None,
                host: str, source: str) -> tuple[dict, list[str]]:
    mine = [b for b in branches if any(c.id == tid for c in b.copies)]
    other = [e for e in _split((current or {}).get("Branch", "")) if not e.startswith(f"{host}:")]
    status, pr_urls, findings = derive_status(tid, main, mine, prs, other)
    branch_copies = [c for b in mine for c in b.copies if c.id == tid]
    # Seat names who is working on the ticket: only a branch holding it in inprogress/ or done/, never one that merely filed it
    working = [b for b in mine if any(c.id == tid and c.folder in PROGRESS_FOLDERS for c in b.copies)]
    best = (branch_copies or sorted(main, key=lambda c: FOLDERS.index(c.folder), reverse=True))[0] if (branch_copies or main) else None
    entries = [f"{host}:{b.branch}" + ("" if any(c.id == tid and c.folder in PROGRESS_FOLDERS for c in b.copies) else f" {FILING_SUFFIX}")
               for b in mine]
    title = best.title if best else ""
    fields = {
        "Title": f"{tid}: {title}".rstrip(": ") if title else tid,
        "Ticket ID": tid,
        "Status": status,
        "Domain": ", ".join(sorted({b.domain for b in mine if b.domain})) or (current or {}).get("Domain", ""),
        "Seat": ", ".join(sorted({b.seat for b in working})) or ("" if status == "To do" else (current or {}).get("Seat", "")),
        "Host": merge_host_entries((current or {}).get("Host", ""), [host] if mine else [], host),
        "Branch": merge_host_entries((current or {}).get("Branch", ""), entries, f"{host}:"),
        "PR": ", ".join(pr_urls),
        "Tier": best.tier if best else "",
        "Body": BODY.format(path=best.path if best else "agent-working/tickets/"),
        "Source": source,
    }
    fields["Sync hash"] = sync_hash(fields)
    return fields, findings


def hand_edits(item: dict, derived: dict) -> list[str]:
    """The item's fields no longer hash to the Sync hash the sync stored: someone edited it. One line per differing field."""
    if not item.get("Sync hash") or sync_hash(item) == item["Sync hash"]:
        return []
    return [f"hand edit: {derived['Ticket ID']} {f} '{item.get(f, '')}' -> '{derived[f]}'" for f in HASH_FIELDS if item.get(f, "") != derived[f]]


def in_pilot_lane(fact: BranchFact, lanes: list[str]) -> bool:
    return fact.domain in lanes or any(fact.branch.startswith(f"{lane}-") for lane in lanes)


def build_plan(main_index: dict[str, list[tuple[str, str]]], load_main: Callable[[str], TicketCopy], branches: list[BranchFact],
               prs: list[PrFact] | None, items: list[dict], host: str, source: str, config: dict,
               done_at: Callable[[str], datetime | None], now: datetime) -> Plan:
    plan = Plan()
    by_id = {i.get("Ticket ID"): i for i in items if i.get("Ticket ID")}
    pilot_start = date.fromisoformat(str(config["pilot_start"]))
    window = int(config["done_window_days"])
    candidates = {c.id for b in branches if in_pilot_lane(b, config["pilot_lanes"]) for c in b.copies} | set(by_id)
    known = set(main_index) | {c.id for b in branches for c in b.copies}
    for tid in sorted(candidates):
        if tid not in known:
            continue
        main = [load_main(path) for _, path in main_index.get(tid, [])]
        derived, findings = derive_item(tid, main, branches, prs, by_id.get(tid), host, source)
        plan.findings += findings
        done_path = next((c.path for c in main if c.folder == "done"), None)
        finished = done_at(done_path) if done_path else None
        current = by_id.get(tid)
        if derived["Status"] == "Done":
            if finished is None or finished.date() < pilot_start and current is None:
                continue
            if finished is not None and (now - finished).days > window:
                if current is not None:
                    plan.archives.append((tid, f"Done more than {window} days ago ({finished.date()})"))
                continue
        if current is None:
            plan.creates.append(derived)
            continue
        plan.hand_edits += hand_edits(current, derived)
        changed = [f for f in HASH_FIELDS if current.get(f, "") != derived[f]]
        if changed:
            plan.updates.append((derived, changed))
    for item in items:
        tid = item.get("Ticket ID", "")
        if not tid:
            plan.archives.append((item.get("Title", "(untitled item)"), "no Ticket ID"))
        elif tid not in known:
            plan.archives.append((tid, "no ticket file for this ID"))
    return plan


# ---------------------------------------------------------------- output / CLI


def load_config(root: Path, notes: list[str]) -> dict:
    cfg = dict(DEFAULTS)
    try:
        loaded = yaml.safe_load((root / CONFIG_REL).read_text(encoding="utf-8")) or {}
        cfg.update({k: v for k, v in loaded.items() if k in DEFAULTS})
    except (OSError, yaml.YAMLError):
        notes.append(f"{CONFIG_REL.as_posix()} unreadable: built-in defaults used")
    return cfg


def render(plan: Plan, host: str, sha: str, age_hours: float | None, detached: int, items_n: int, prs_n: int | None) -> str:
    age = "unknown age" if age_hours is None else f"{age_hours:.1f} h old"
    lines = [f"project_sync DRY RUN (no GitHub or repo write) host={host} origin/main={sha[:9]} ({age}, no fetch) "
             f"items-in={items_n} open-PRs={'unknown' if prs_n is None else prs_n} detached-skipped={detached}"]
    for item in plan.creates:
        lines.append(f"create  {item['Ticket ID']}  {item['Status']}  seat={item['Seat'] or '-'}  branch={item['Branch'] or '-'}  pr={item['PR'] or '-'}")
    for item, changed in plan.updates:
        lines.append(f"update  {item['Ticket ID']}  {item['Status']}  changed: {', '.join(changed)}")
    for ident, reason in plan.archives:
        lines.append(f"archive {ident}  ({reason})")
    lines += plan.hand_edits + [f"finding: {f}" for f in plan.findings] + [f"note: {n}" for n in plan.notes]
    if not (plan.creates or plan.updates or plan.archives):
        lines.append("nothing to do")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Derive the ticket-state Project plan (dry run only; writes nothing).")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--host", default=socket.gethostname(), help="this host's tag for Branch/Host entries (default: hostname)")
    parser.add_argument("--items", type=Path, help="JSON file of the current Project items (P1 replaces this with a live read)")
    parser.add_argument("--dry-run", action="store_true", help="accepted; the only mode in P0")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--init", action="store_true")
    args = parser.parse_args(argv)
    if args.apply or args.init:
        print("project_sync: --apply and --init are P1 and are not built; P0 is a dry run only.", file=sys.stderr)
        return 2
    plan_notes: list[str] = []
    config = load_config(args.root, plan_notes)
    items = json.loads(args.items.read_text(encoding="utf-8")) if args.items else []
    sha, stamp = origin_info(args.root)
    now = datetime.now(timezone.utc)
    branches, detached = read_branch_facts(args.root, args.host, plan_notes)
    prs = read_open_prs(args.root, plan_notes)
    index = read_main_index(args.root)
    source = f"{sha[:9]} @ {now.strftime('%Y-%m-%dT%H:%MZ')}"
    plan = build_plan(index, lambda path: read_main_copy(args.root, path), branches, prs, items, args.host, source, config,
                      lambda path: done_date(args.root, path), now)
    plan.notes = plan_notes + plan.notes
    print(render(plan, args.host, sha, None if stamp is None else (time.time() - stamp) / 3600, detached, len(items),
                 None if prs is None else len(prs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
