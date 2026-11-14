#!/usr/bin/env python3
"""A printed, read-only view of the open-ticket queue (TCK-20261102-A-PRINTED-QUEUE-VIEW-OF-OPEN-TICKETS).

One row per `TCK-*.md` under `agent-working/tickets/todos/` and `inprogress/` at a git ref (`origin/main` by default,
read through git, so the working tree is never read; `--worktree` reads the working tree instead). Every state column is
backed by evidence shown in the row, or reads `unknown` / `mention`. Nothing is written, no ticket moves, and no second
order exists: the position comes from the roadmap's order line (docs/plans/systemic_world/roadmap.md, section 12.5) and a
ticket only names a step in an optional `## Order Ref` section. Report-only: exit 0 unless the tool itself fails.

    python3 tools/delivery/ticket_queue.py [--ref origin/main | --worktree] [--json] [--no-gh]

The tool does not fetch, so `origin/main` can be stale: the header prints the commit date beside the sha.
`parked: yes` is a narrow line match shown with `path:line`; a pause that was lifted but left in the text still reads
`yes`, so check the line. F4 lands "as soon as it is ready, independent of this order", so its position is nominal.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_REPO_ROOT), str(_REPO_ROOT / "tools"), str(_REPO_ROOT / "tools" / "delivery")):
    if _p not in sys.path:
        sys.path.append(_p)
from generate_registry import _strip_frontmatter, parse_body_section  # noqa: E402
from pr_status import CommandResult, default_run_command  # noqa: E402
from repo_name import current_repo  # noqa: E402
from validate_frontmatter import extract_frontmatter  # noqa: E402

TICKET_DIRS = ("agent-working/tickets/todos", "agent-working/tickets/inprogress")
DONE_DIR = "agent-working/tickets/done"
ROADMAP = "docs/plans/systemic_world/roadmap.md"
PR_LIMIT = 300  # gh's GraphQL node cap rejects a larger list when each PR also returns up to 100 files
PR_FILES_CAP = 100
CLAIMS_ISSUE = 634

_TICKET_ID = re.compile(r"TCK-\d{8}-[A-Z0-9][A-Z0-9-]*")
_ORDER_SENTENCE = re.compile(r"order is (?:then )?([^.\n]*→[^.\n]*)\.")
_PARKED_YES = (
    re.compile(r"^#{1,6}\s*(?:Parked|Paused)\b"),
    re.compile(r"^\*\*Paused \(owner,"),
    re.compile(r"^\*\*Parked by explicit user decision"),
    re.compile(r"^\*\*Parked\*\*"),
)
_PARKED_WORD = re.compile(r"\bparked\b", re.IGNORECASE)


# ---------------------------------------------------------------- collect

def _git(run_command, *args) -> CommandResult:
    return run_command(["git", *args])


def read_ticket_sources(run_command, ref: str):
    """([(path, text)], header dict, roadmap text or None, warnings) for the ticket files at `ref`, read through git only."""
    warnings = []
    sha = _git(run_command, "rev-parse", ref)
    if sha.returncode != 0:
        raise RuntimeError(f"cannot resolve {ref}: {sha.stderr.strip()}")
    date = _git(run_command, "show", "-s", "--format=%cI", ref)
    header = {"source": ref, "sha": sha.stdout.strip(), "commit_date": date.stdout.strip() if date.returncode == 0 else "unknown"}
    listing = _git(run_command, "ls-tree", "-r", "--name-only", ref, *TICKET_DIRS)
    if listing.returncode != 0:
        raise RuntimeError(f"git ls-tree failed: {listing.stderr.strip()}")
    sources = []
    for path in sorted(p for p in listing.stdout.splitlines() if re.search(r"/TCK-[^/]*\.md$", p)):
        shown = _git(run_command, "show", f"{ref}:{path}")
        if shown.returncode != 0:
            warnings.append(f"{path}: could not be read at {ref}")
            continue
        sources.append((path, shown.stdout))
    roadmap = _git(run_command, "show", f"{ref}:{ROADMAP}")
    return sources, header, (roadmap.stdout if roadmap.returncode == 0 else None), warnings


def read_done_ids(run_command, ref: str, worktree_root: Path | None = None):
    """(ticket ids with a file under done/ at the same source, warnings): a ticket also there is in two status folders."""
    if worktree_root is not None:
        return {p.stem for p in (worktree_root / DONE_DIR).rglob("TCK-*.md")}, []
    listing = _git(run_command, "ls-tree", "-r", "--name-only", ref, DONE_DIR)
    if listing.returncode != 0:
        return set(), [f"could not list {DONE_DIR} at {ref}: the done/ copy check was skipped"]
    return {Path(p).stem for p in listing.stdout.splitlines() if re.search(r"/TCK-[^/]*\.md$", p)}, []


def read_worktree_sources(root: Path):
    sources = []
    for d in TICKET_DIRS:
        for path in sorted((root / d).rglob("TCK-*.md")):
            sources.append((path.relative_to(root).as_posix(), path.read_text(encoding="utf-8")))
    road = root / ROADMAP
    header = {"source": "worktree", "sha": "uncommitted working tree", "commit_date": "n/a"}
    return sources, header, (road.read_text(encoding="utf-8") if road.exists() else None), []


# ---------------------------------------------------------------- order

def parse_order(roadmap_text: str | None):
    """(steps, 'path:line' | None, warnings). Searches only section 12.5 (its `### 12.5` heading up to the next heading of
    level 3 or higher) and takes the LAST `... the order is A → B → ... .` sentence. No match, or fewer than 3 steps: no
    order, one warning, and every ticket reads `unknown` (never a text-match guess)."""
    if roadmap_text is None:
        return [], None, [f"{ROADMAP} could not be read: every order reads unknown"]
    lines = roadmap_text.splitlines()
    start = next((i for i, l in enumerate(lines) if l.startswith("### 12.5")), None)
    if start is None:
        return [], None, ["roadmap section 12.5 not found: every order reads unknown"]
    end = next((i for i in range(start + 1, len(lines)) if re.match(r"#{1,3}\s", lines[i])), len(lines))
    section = "\n".join(lines[start:end])
    matches = list(_ORDER_SENTENCE.finditer(section))
    steps = [s.strip() for s in matches[-1].group(1).split("→")] if matches else []
    if len(steps) < 3:
        return [], None, ["roadmap section 12.5 has no parseable order line (need a 'the order is A → B → C ...' sentence): "
                          "every order reads unknown"]
    where = f"{ROADMAP}:{start + 1 + section[:matches[-1].start()].count(chr(10))}"
    warnings = []
    after = section[matches[-1].end():].split("\n", 1)[0]  # the rest of the same line
    if "→" in after or "Amended" in after:
        warnings.append(f"roadmap 12.5 mentions '→' or 'Amended' after the order line at {where}: the order may be superseded")
    return steps, where, warnings


def _norm(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().strip("`*").casefold())


def order_for(ref_text: str, steps: list[str]) -> str:
    """`<position>` (1-based), `stale-ref` (a ref not in the line) or `unknown` (no ref, or no parsed order)."""
    first = next((l.strip() for l in ref_text.splitlines() if l.strip()), "")
    if not steps:
        return "unknown"
    if not first:
        return "unknown"
    wanted = _norm(first)
    for i, step in enumerate(steps, start=1):
        if _norm(step) == wanted:
            return str(i)
    return "stale-ref"


# ---------------------------------------------------------------- rows

def _first_token(text: str) -> str:
    tokens = text.split()
    return tokens[0].strip("*`:,;()").upper() if tokens else "UNKNOWN"


def parked_state(text: str, path: str):
    """('yes', 'path:line') on a narrow line match outside code fences; ('mention', None) when the word only appears; else (None, None)."""
    fenced, mention = False, False
    for n, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        if any(p.search(line) for p in _PARKED_YES):
            return "yes", f"{path}:{n}"
        if _PARKED_WORD.search(line):
            mention = True
    return ("mention", None) if mention else (None, None)


def build_row(path: str, text: str, steps: list[str]) -> dict:
    fm = {}
    try:
        fm = extract_frontmatter(text) or {}
    except ValueError:
        pass
    body = _strip_frontmatter(text)
    status_text = parse_body_section(body, "Status")
    status = _first_token(status_text)
    tier = parse_body_section(body, "Tier").split()
    priority = parse_body_section(body, "Priority").split()
    tier = tier[0].strip("*`:,;").lower() if tier else "unknown"
    priority = priority[0].strip("*`:,;").upper() if priority else "unknown"
    parked, parked_at = parked_state(text, path)
    blocked = None
    if status == "BLOCKED":
        ids = sorted(set(_TICKET_ID.findall(status_text)))
        blocked = {"on": ids if ids else "unknown"}
    return {
        "id": Path(path).stem, "path": path, "folder": path.split("/")[2], "layer": str(fm.get("layer") or "unknown"),
        "priority": priority, "tier": tier, "status": status,
        "epic": status == "EPIC_SCOPED" or tier == "epic",
        "order": order_for(parse_body_section(body, "Order Ref"), steps),
        "blocked": blocked, "parked": parked, "parked_at": parked_at, "flight": ["unknown"], "flags": [],
    }


# ---------------------------------------------------------------- flight

def fetch_flight(run_command, ids: list[str]):
    """({id: [labels]}, warnings). `pr #N closes` when the PR's files include done/<ID>.md, else `pr #N touches` (a changed
    file or the PR title names the ID); `#634 comment <id>` for the latest #634 comment naming the ID (a mention, not
    necessarily a claim). `gh` failing gives None and a warning: flight then reads `unknown`."""
    warnings = []
    repo = current_repo(run_command)
    prs = run_command(["gh", "pr", "list", "--repo", repo, "--state", "open", "--limit", str(PR_LIMIT),
                       "--json", "number,title,files"])
    if prs.returncode != 0:
        return None, [f"gh unavailable ({(prs.stderr or '').strip()[:100] or 'failed'}): flight reads unknown"]
    try:
        pr_list = json.loads(prs.stdout or "[]")
    except ValueError:
        return None, ["gh pr list returned unreadable output: flight reads unknown"]
    if len(pr_list) >= PR_LIMIT:
        warnings.append(f"gh pr list reached its limit of {PR_LIMIT}: some PRs may be missing from flight")
    flight = {i: [] for i in ids}
    for pr in pr_list:
        files = [f.get("path", "") for f in pr.get("files") or []]
        if len(files) >= PR_FILES_CAP:
            warnings.append(f"PR #{pr.get('number')} lists {len(files)} files (gh caps at {PR_FILES_CAP}): its flight labels may be incomplete")
        title = pr.get("title") or ""
        for ticket_id in ids:
            if any("/done/" in f and f.endswith(f"/{ticket_id}.md") for f in files):
                flight[ticket_id].append(f"pr #{pr['number']} closes")
            elif any(Path(f).name == f"{ticket_id}.md" for f in files) or ticket_id in title:
                flight[ticket_id].append(f"pr #{pr['number']} touches")
    comments = run_command(["gh", "api", f"repos/{repo}/issues/{CLAIMS_ISSUE}/comments", "--paginate", "--jq",
                            ".[] | [.id, (.body|tostring)] | @json"])
    if comments.returncode != 0:
        warnings.append(f"#634 comments unavailable ({(comments.stderr or '').strip()[:100] or 'failed'}): no #634 labels")
    else:
        latest: dict = {}
        for line in comments.stdout.splitlines():
            try:
                cid, body = json.loads(line)
            except ValueError:
                continue
            for ticket_id in set(_TICKET_ID.findall(body)) & set(ids):
                latest[ticket_id] = cid
        for ticket_id, cid in latest.items():
            flight[ticket_id].append(f"#634 comment {cid}")
    return flight, warnings


# ---------------------------------------------------------------- view

def build_view(run_command=default_run_command, ref: str = "origin/main", worktree_root: Path | None = None, use_gh: bool = True):
    if worktree_root is not None:
        sources, header, roadmap, warnings = read_worktree_sources(worktree_root)
    else:
        sources, header, roadmap, warnings = read_ticket_sources(run_command, ref)
    steps, order_at, order_warnings = parse_order(roadmap)
    warnings += order_warnings
    header["order_line"] = {"steps": steps, "at": order_at}
    rows = [build_row(path, text, steps) for path, text in sources]
    done_ids, done_warnings = read_done_ids(run_command, ref, worktree_root)
    warnings += done_warnings
    folders: dict = {}
    for row in rows:
        folders.setdefault(row["id"], set()).add(row["folder"])
        if row["id"] in done_ids:
            folders[row["id"]].add("done")
    for row in rows:
        if len(folders[row["id"]]) > 1:
            row["flags"].append("two-folders")
    if use_gh:
        flight, gh_warnings = fetch_flight(run_command, sorted({r["id"] for r in rows}))
        warnings += gh_warnings
        for row in rows:
            row["flight"] = ["unknown"] if flight is None else (flight[row["id"]] or ["none"])
    else:
        warnings.append("--no-gh: flight reads unknown")
    rows.sort(key=lambda r: (int(r["order"]) if r["order"].isdigit() else 10**6, r["priority"], r["id"]))
    return {"header": header, "rows": rows, "summary": summarize(rows), "warnings": warnings}


def summarize(rows: list[dict]) -> dict:
    work = [r for r in rows if not r["epic"]]
    p1 = [r for r in work if r["priority"] == "P1"]
    flights = Counter()
    for r in work:
        kinds = {("closes" if f.endswith("closes") else "touches" if f.endswith("touches") else "comment" if "comment" in f else f)
                 for f in r["flight"]}
        flights.update(kinds)
    return {
        "tickets": len(rows), "epic_tracking_rows": len(rows) - len(work), "work_rows": len(work),
        "status": dict(Counter(r["status"] for r in work)),
        "blocked_on_unknown": sum(1 for r in work if r["blocked"] and r["blocked"]["on"] == "unknown"),
        "parked": {"yes": sum(1 for r in work if r["parked"] == "yes"), "mention": sum(1 for r in work if r["parked"] == "mention")},
        "order": {"positioned": sum(1 for r in work if r["order"].isdigit()), "stale-ref": sum(1 for r in work if r["order"] == "stale-ref"),
                  "unknown": sum(1 for r in work if r["order"] == "unknown")},
        "flight": dict(flights),
        "two_folders": sum(1 for r in rows if "two-folders" in r["flags"]),
        "p1": {"total": len(p1), "by_status": dict(Counter(r["status"] for r in p1)), "by_tier": dict(Counter(r["tier"] for r in p1)),
               "by_layer": dict(Counter(r["layer"] for r in p1))},
    }


def render_text(view: dict) -> str:
    h = view["header"]
    out = [f"Ticket queue at {h['source']} ({h['sha'][:12]}, committed {h['commit_date']}); {view['summary']['tickets']} tickets.",
           "Order line: " + (" → ".join(h["order_line"]["steps"]) + f"  [{h['order_line']['at']}]" if h["order_line"]["steps"] else "unknown"),
           ""]
    out.append("order  id | folder | layer | prio | tier | status | blocked | parked | flight")
    for r in view["rows"]:
        blocked = "" if not r["blocked"] else "on: " + (", ".join(r["blocked"]["on"]) if r["blocked"]["on"] != "unknown" else "unknown")
        parked = "" if not r["parked"] else (f"yes {r['parked_at']}" if r["parked"] == "yes" else "mention")
        tags = (" [epic]" if r["epic"] else "") + "".join(f" [{f}]" for f in r["flags"])
        out.append(f"{r['order']:>9} {r['id']}{tags} | {r['folder']} | {r['layer']} | {r['priority']} | {r['tier']} | {r['status']} | "
                   f"{blocked} | {parked} | {'; '.join(r['flight'])}")
    s = view["summary"]
    out += ["", "Summary (epic tracking rows are left out of the work counts):",
            f"  work rows {s['work_rows']}, epic tracking rows {s['epic_tracking_rows']}, in two folders {s['two_folders']}",
            f"  status {s['status']}", f"  blocked with unknown dependency: {s['blocked_on_unknown']}",
            f"  parked yes {s['parked']['yes']}, mention {s['parked']['mention']} (mention is not parked)",
            f"  order positioned {s['order']['positioned']}, stale-ref {s['order']['stale-ref']}, unknown {s['order']['unknown']}",
            f"  flight {s['flight']}",
            f"  P1 {s['p1']['total']}: by status {s['p1']['by_status']}; by tier {s['p1']['by_tier']}; by layer {s['p1']['by_layer']}"]
    if view["warnings"]:
        out += ["", "Warnings:"] + [f"  - {w}" for w in view["warnings"]]
    return "\n".join(out)


def main(argv: list[str] | None = None, run_command=default_run_command) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--ref", default="origin/main", help="git ref to read the tickets and roadmap from")
    parser.add_argument("--worktree", action="store_true", help="read the working tree instead of a git ref")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-gh", action="store_true", help="skip gh: flight reads unknown")
    args = parser.parse_args(argv)
    try:
        view = build_view(run_command, args.ref, _REPO_ROOT if args.worktree else None, not args.no_gh)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(json.dumps(view, indent=2) if args.json else render_text(view))
    return 0


if __name__ == "__main__":
    sys.exit(main())
