---
status: historical
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20261112-PROJECT-SYNC-DRY-RUN
phase: done
date: 2026-11-12
tags: [planning, delivery]
---

# TCK-20261112-PROJECT-SYNC-DRY-RUN

## Title
`tools/sessions/project_sync.py --dry-run`: derive each rpg-lane ticket's Project item from ticket files, u24 worktree branches and open PRs, and print the plan without writing to GitHub

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child P0 of TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW. The owner's go to start it is #715 6813165811 ("I think you can
try"). P0 needs no token and no owner action, per the lead's addendum. The design is the main-checkout draft
`.claude/handover/drafts/github-project-ticket-view-2026-11-12.md` (§1-§5, §8, addendum). Read the draft before planning.
This ticket restates only what P0 must do.

## Scope
1. **New `tools/sessions/project_sync.py`**, with a CLI that is dry by default. `--dry-run` is the only mode in P0.
   - There's no `--apply` or `--init` yet. If either is given, the tool says P1 isn't built.
   - It writes nothing to GitHub and nothing to the repo.
   - Inputs:
     - ticket files on origin/main (`git ls-tree`/`git show`; no fetch, and print the sha used and its age);
     - worktrees and seats through `tools/sessions/status.py` `collect()` and `seat_infos()`, reused, with no second
       scanner;
     - per-worktree ticket changes, against the merge base with origin/main plus `git status --porcelain`, read-only
       (`--no-optional-locks`);
     - open PRs and their file lists through the existing `gh` login, paginated past 100 files.
   - Current Project items come from a JSON fixture file (`--items <path>`), empty by default. P1 replaces this with the live
     read.
2. **Derivation, pure functions:**
   - Status, by the design §3 rules, first match wins: Done → In review → Blocked → In progress → To do.
     - An `inprogress/` ticket on main with no branch is reported as an orphan finding.
     - A ticket in two folders is reported and gets the higher status.
     - A squash-merged branch never shows as In progress.
   - Fields (design §2): Ticket ID, Status, Domain, Seat, Host, Branch (`host:branch`), PR, Tier, Source, Sync hash.
     - Seat comes from the status.py mapping. If that fails, it's `<domain> (unmapped)` from the branch prefix, and otherwise
       `unknown`.
     - Title is `<ID>: <## Title>`, with the one-line generated body from §1.
3. **Plan:** create, update or archive per item, keyed by Ticket ID.
   - Sync hash is sha256 over the written fields. An item whose current fields don't match its stored hash is reported as
     `hand edit: <id> <field> '<theirs>' -> '<derived>'`.
   - An item with no ticket ID, or an ID with no ticket file, is reported as to-archive.
   - Host-tagged Branch/Host entries (design §5): this host replaces only its own entries and keeps the other host's.
4. **Pilot lanes:** tickets found on an rpg worktree branch (domain rpg from status.py, else an `rpg-` prefix), plus tickets
   already in the item fixture. To-do items from main wait for P3. Done covers only tickets after the pilot start date, and
   items are archived after 14 days.
5. **New `registries/session_project.yaml`:** the Project owner and number (placeholders until P1), the pilot lanes, the pilot
   start date, the Done window (14 days) and the stale-host age (24 h). It holds no field ids.
6. **Tests** in `tests/tools/test_session_project_sync.py`, about 13, with fixture inputs only and no network:
   - derivation rules 1-5, one each;
   - a ticket in two folders;
   - a squash-merged branch;
   - an uncommitted ticket file in a worktree;
   - an unmapped seat;
   - the sync hash, plus hand-edit detection;
   - an orphaned inprogress ticket;
   - the addendum case: In progress through a ubuntu-tagged branch entry plus an open PR seen from u24 → In review, with
     both host entries kept;
   - `--apply` refused.

## Out of Scope
- Anything that writes to the Project, field creation (`--init`) and tokens. These are P1.
- ubuntu runs (P2), all lanes and timers (P3), and the claim-rule change (P4).
- Changes to `tools/sessions/status.py` beyond what reuse needs. If a small public helper is needed, say so in plan.md.
- Everything in the epic's Out of Scope.

## Acceptance Criteria
1. The ~13 tests pass. The existing `tests/tools/test_session_status*.py` tests pass unchanged.
2. A real `project_sync.py --dry-run` on u24 prints a plan for the current rpg-lane tickets, with the origin/main sha and its
   age. Its output goes into the PR body, and agent-working-designer-u24 checks it against `git worktree list` by hand.
3. No network write. The tool makes no `gh` call except PR reads (`gh pr list` / `gh api` GET).
4. The staging artifacts plan.md, investigation.md and test_plan.md exist, and agent-working-designer-u24 reviews plan.md
   before any code.
5. Scoped tests only, never full `pytest tests/`.

## Related Tickets
- TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW (parent)

## Related Docs
- none yet (README section comes with P1)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261112-PROJECT-SYNC-DRY-RUN/{investigation,plan,test_plan}.md
- Designer draft (main checkout): `.claude/handover/drafts/github-project-ticket-view-2026-11-12.md`

## Related Code Areas
- tools/sessions/status.py, tools/sessions/project_sync.py (new), registries/session_project.yaml (new),
  tests/tools/test_session_project_sync.py (new; the tests/tools/ owner split is rpg/agent-working)

## Assumptions / Open Questions
- Simpler-fix check (6698958617): a dry run with fixture items is the cheapest way to prove the derivation. Cost: about 250
  lines and 13 tests, no measurement runs. It leaves out any live Project read or write.
- Branch names don't reliably name the seat (design §0), so Seat comes from status.py, not from the branch.

## Implementation Notes
Owner go #715 6813165811 (read by me); dispatched by agent-working-planner-u24. plan.md reviewed by agent-working-designer-u24 (OK with amendments A-E, all folded into plan.md and test_plan.md before code). New tools/sessions/project_sync.py: pure derivation (derive_status, derive_item, merge_host_entries, sync_hash, hand_edits, build_plan) plus thin readers; every subprocess goes through `_guard` (git read verbs, gh `pr list` and GET `api` only). Reuses status.py's inspect_worktree (size and PR readers stubbed), seat_infos and the private `_worktree_for` (deliberate, commented). A todos/ copy on a branch or PR is filing, not progress. Done timing comes from `git log --diff-filter=A` on origin/main. `--apply` and `--init` exit 2 (P1). New registries/session_project.yaml (no field ids). Default `--host` is socket.gethostname() (here `u24desktop-Virtual-Machine`); the PR's dry run passes `--host u24desktop`.

Follow-up from the designer's AC-2 check against `git worktree list` (planner relay): the porcelain read now uses `git status --porcelain -z`, so a leading-space ` M <ticket path>` entry (unstaged-only) is read exactly and rename sources are skipped. I could not reproduce a lost character with the earlier line-based parse in a real repo; the one worktree in question had since committed its change, so the earlier miss is unconfirmed, and the `-z` read is hardening plus two tests (a fake-runner case whose first entry is ` M <ticket path>`, and a real-git rename/unstaged case). Seat now comes only from branches holding the ticket in inprogress/ or done/ (never a filing branch), and a To do item has an empty Seat. Re-run of the dry run: the set of 24 creates is unchanged; NON-FLIGHT lists both `u24desktop:rpg-felt-lethal-recency` and `u24desktop:rpg-non-flight-free-swing`; THE-API-EMITS has the single seat `rpg (unmapped)`.

## Test Summary
tests/tools/test_session_project_sync.py: 40 passed (rules 1-5, two folders, squash-merged branch, filing on a branch and in a PR, branch-only content, unmapped seat, hash and hand edit, archives and Done ageing, pre-pilot Done, pilot lanes, the ubuntu+PR addendum case, filing entry from another host, --apply/--init refused, guard refuses write verbs, porcelain vs committed reads, detached worktrees, PR limit note, gh failure, registry file). With test_session_status.py and test_agent_working_paths_guard.py: 64 passed, scoped, single process. Real dry run on u24 (--host u24desktop): rc 0, origin/main 5e58ae857, 5 open PRs, 8 detached worktrees skipped, 24 creates (13 In progress, 7 To do, 2 Done, 1 In review, 1 Blocked), 5 unattributed notes; `git worktree list` shows 60 entries. The CI lane tools-f-z was not run locally.

## Files Changed
tools/sessions/project_sync.py (new); registries/session_project.yaml (new); tests/tools/test_session_project_sync.py (new); the epic folder agent-working/tickets/todos/github-project-ticket-view/ (taken from the planner's a08bb770d: SEQUENCE.md, the epic, and this ticket moved to done/); stored artifacts; docs/REGISTRY.yaml; W46 shards.

## Completion Summary
P0 is built: `python3 -m tools.sessions.project_sync --dry-run` prints the create / update / archive plan for rpg-lane tickets with no GitHub or repo write. Known gaps: To do items from main wait for P3; the live Project read, `--init`, `--apply`, tokens, ubuntu and timers are P1-P3; Seat is `<domain> (unmapped)` for batch worktrees that no roster seat is bound to.
