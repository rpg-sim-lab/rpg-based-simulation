---
status: historical
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20261115-PROJECT-SYNC-ALL-LANES
phase: done
date: 2026-11-15
tags: [planning, delivery]
---

# TCK-20261115-PROJECT-SYNC-ALL-LANES

## Title
`project_sync.py` P3b: every lane goes on Project 1, Domain becomes a single-select, the sync can fetch origin/main itself, and each host leaves a last-run file and a cross-host heartbeat

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child P3b of TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW.
- **Owner decisions:** #715 6881411615, on the options draft (main-checkout
  `.claude/handover/drafts/project-sync-p3-timer-options-2026-11-15.md`). Item 3: "P3a now, then P3b, P3c (Recommended)". Item 4:
  "Rename now, delete later (Recommended)". Item 1 accepts `git fetch origin main` on every timer run.
- **Order:** this ticket is dispatched only **after P3a (TCK-20261114-PROJECT-CLIENT-WRITE-PACING) merges**. Its first load needs
  the pacing.
- **Runs on:** u24, seat agent-working-implementer-u24. Dispatch is from agent-working-planner-u24. Push, PR and merge go to the
  owner through lead-planner-u24.

## Scope
1. **All lanes.** `pilot_lanes` gives way to every registered domain in `registries/session_roles.yaml`. There are 9 today: rpg,
   agent-working, codebase, testing, asset, perf, lead, platform, architecture. To do tickets in origin/main's `todos/` become
   items, which ends the design's "To do items from main wait for P3".
2. **Domain of a main-only ticket**, first match wins:
   - the domain of a branch copy on any host (a `Host facts` segment, or this host's branch);
   - else the domain of the seat that filed the folder's SEQUENCE.md, if the plan finds a reliable carrier (the plan says which, or
     drops this rule);
   - else `unassigned`.
   Never guess the domain from `layer`.
3. **Prefix-mapping fix in `attribute()`.** Today `agent-working-…` gives domain `agent`. Fix: the longest registered domain that
   is a prefix of the branch name, followed by `-`. Else `unknown`, with seat `unknown`.
4. **Domain as a single-select.**
   - `--init` renames the text field `Domain` to `Domain (old)`. It then creates a single-select `Domain` whose options are the 9
     domains plus `unassigned` and `unknown`.
   - **The old field is not deleted.** That is a separate owner ask once P3 is proven (6881411615 item 4).
   - A domain value with no option is a finding. The run carries on and leaves the field empty.
   - The Layer option-id caveat from P1c applies.
5. **Epic rule (a) fix.** Rule (a) checks origin's path for the same ID as well as the chosen copy's path. Then an open ticket whose
   chosen copy is a branch copy under `inprogress/` still resolves to its epic folder.
6. **`--fetch`.** Run `git fetch origin main` first. On failure, carry on: print the age of origin/main and add a finding. The timer
   (P3c) sets this flag; a hand run doesn't need to.
7. **A last-run file.**
   - Every `--apply` writes `~/.local/state/rpg-project-sync/last-run.json`: UTC time, host, rc, steps done and left, and the first
     error with secrets removed. A dry run writes nothing.
   - `tools/sessions/session_status.py`, or the SessionStart hook that already prints host warnings, warns after 2 failed runs in a
     row. The plan picks which, at the lowest cost.
8. **A heartbeat and the stale-host flag.**
   - One draft item titled `_sync heartbeat`, with a text field `Last run` holding one segment per host:
     `u24desktop: 2026-11-15T10:00Z rc=0`.
   - Each `--apply` rewrites only its own segment. That is 1 extra mutation, using the `merge_host_facts` pattern.
   - Each run flags any other host whose segment is older than `stale_host_hours`. The flag goes in the output and in the last-run
     file.
   - The flag only reports. It never changes Status and never archives.
   - The heartbeat item is never archived and never counted as a ticket.
9. **Docs:** `docs/guidelines/session_roles/project_sync_dry_run.md` covers all lanes, the Domain rules, `--fetch`, the last-run
   file and the heartbeat. Also write the limits lines.
10. **Tests, no network** (about 14):
    - lanes from the registry;
    - main-only domain, each rule;
    - the `attribute()` prefix (agent-working, rpg, unknown);
    - the single-select Domain, with an unknown value as a finding;
    - the `--init` rename and a second `--init` that does nothing;
    - Epic (a) through origin's path;
    - `--fetch` success and failure;
    - the last-run file, written on apply and not on a dry run;
    - the 2-failure warning;
    - heartbeat: own segment only;
    - the stale-host flag;
    - the heartbeat is never archived;
    - convergence A→B→A with all lanes.

## Out of Scope
- The timer itself, unit files and install: P3c (TCK-20261115-PROJECT-SYNC-HOST-TIMER).
- Deleting `Domain (old)`, or any other delete.
- Pacing: P3a.
- The claim-rule change: P4.

## Acceptance Criteria
1. Staging artifacts exist, and agent-working-designer-u24 reviews plan.md before code.
2. Scope items 1-9 are built, and the scoped tests pass: test_session_project_sync*, test_project_client, test_session_status*.
3. **First load by hand.** Stop with the error on any refusal, secrets removed.
   1. A live dry run goes to agent-working-planner-u24, with counts per domain. Expect about 155 new To do items, and no archive of
      any existing item.
   2. `--init`: the rename plus the new Domain. A second `--init` must do nothing.
   3. `--apply`, only after the planner's OK. It is paced (P3a). The run's rate-limit answers and its real point cost are recorded
      for the study.
   4. A final dry run must show nothing to do.
   5. ubuntu then runs one dry run on this code. It must touch only its own segments.
   - The `--apply` is a write the permission check may block. It runs under the owner's allow rule (6881411615 item 2) or in the
     owner's terminal, never around a denial.
4. The PR body carries the plan and the outputs of the final runs, with secrets removed. A grep finds no token value.
5. Any delete (none is expected) goes to the owner through lead-planner-u24 first.

## Related Tickets
- TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW (parent)
- TCK-20261114-PROJECT-CLIENT-WRITE-PACING (P3a, goes first)
- TCK-20261115-PROJECT-SYNC-HOST-TIMER (P3c, follows)
- TCK-20261114-PROJECT-SYNC-SECOND-HOST (P2, #913)

## Related Docs
- `docs/guidelines/session_roles/project_sync_dry_run.md`
- Options draft (main checkout): `.claude/handover/drafts/project-sync-p3-timer-options-2026-11-15.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261114-PROJECT-SYNC-SECOND-HOST/`

## Related Code Areas
- `tools/sessions/project_sync.py`: `attribute`, `make_epic_resolver`, `in_pilot_lane`, `build_plan`, `main`
- `tools/sessions/project_client.py`: `init_fields`, `apply_plan`
- `registries/session_project.yaml`, `registries/session_roles.yaml` (read only)
- `tests/tools/test_session_project_sync*.py`, `tests/tools/test_project_client.py`

## Assumptions / Open Questions
- The first load is about 1,700-2,000 mutations, about 30-35 min at 1 a second. This is estimated from 155 To do tickets on
  origin/main on 2026-11-15, and is unconfirmed until it runs.
- **Simpler-fix check (6698958617):** the stale-host flag could be left out, which saves about 40 lines and 4 tests. The owner took
  the heartbeat in P3 (6881411615 item 1), because a dead timer is otherwise unseen.
- Whether SEQUENCE.md has a reliable filing-seat carrier (scope 2, second rule) is for the investigation.

## Implementation Notes
- Plan amendments from the designer (A-F) and the planner: the SEQUENCE.md filing-seat rule was **dropped** (no reliable carrier: 4-5 of 6 SEQUENCE.md name a filer in free text, 140 flat todos sit in no folder); a main-only ticket's Domain is its host segment, else the owner of the code it names (`## Related Code Areas` routed through `route()`), else `unassigned`. Measured on origin/main: 124 of 161 resolve (120 rpg, 2 agent-working, 1 asset, 1 platform); 37 stay unassigned (21 mixed, 10 no path, 6 not routed).
- Heartbeat: written last in `--apply`, one paced attempt, oldest item, nothing archived; the first load wrote it.
- Found during the first load: `## Tier` of one ticket read "standard (provisional)", which the dry run never validated, so `--apply` refused (rc 2, nothing written). Fixed in the same ticket: the leading token is the Tier, and `check_plan_options` runs in both the live dry run (a finding) and `--apply` (refuse before the first write, naming all).
- Gate lesson: the plan-diff gate did its job twice: the plan changes whenever a branch appears or disappears between the OK'd dry run and the apply, so a stop there is information, not an obstacle. The dry run could not show attempt 1's refusal, which is why it now checks option values.
- The sync sees only branches checked out in a worktree on this host; a branch with no worktree (parked) falls back to main's copy.
- Known limits are in the guide (retry-after rarely shown; pre-P3b `--apply` archives the heartbeat; Domain from code areas needs the same roster on both hosts).

## Test Summary
- 21 + 7 new no-network tests in `tests/tools/test_session_project_sync_all_lanes.py` (lanes from the roster, main-only Domain rules, `attribute()` prefix, Domain select findings, `--init` rename / second `--init` / refusal, Epic (a), `--fetch` success/failure/timeout, last-run file and the start-hook line, heartbeat own segment / two heartbeats / failed write, stale hosts, heartbeat never archived, A→B→A convergence, no false hand edits after the rename, Tier leading token, whole-plan option check in both modes). Scoped runs: test_project_client + test_session_project_sync (+second_host, all_lanes) + test_session_status = 172 passed; registry no-drift 71 passed.
- **AC3 first load (by hand, in the lead's terminal, #715 6881411615 / 6883251620):** round 1 `--init` rc 0, second `--init` all "left alone". Dry run: 140 creates, 41 updates (Domain only), 0 archives, 0 hand edits. **Three stopped attempts, nothing written by any of them:** attempt 1 was the `--apply` refusal on Tier "standard (provisional)" (rc 2; #715 6883316665); attempts 2 and 3 were stopped by the plan-diff gate (`pre.txt` against the OK'd plan) on branch drift (#715 6883415582 and the next one), e.g. a parked branch with no worktree on this host falling back to main's copy (testing-planner's epic in attempt 3). The Tier fix and the option check came out of attempt 1. Round 2 `--apply`: **rc 0, 1608 steps, "nothing left", 2232 s (20:05:12-20:42:24Z, about 1.4 s per step with the 1 s pacing), final dry run "nothing to do", last-run.json rc 0, failed_streak 0, no token leak.**
- **Rate-limit evidence (for the study):** no secondary-limit wait and no stop in `apply.err` (it holds only progress lines). The GraphQL `rateLimit` primary budget (5,000/hour) read used=114 before; the window reset at 20:23:38Z mid-run, and used=17 after (about 800 steps in the new window), so mutations count at most a few points each against that budget: it was never close to its limit. Real per-mutation point cost is therefore not measurable from these two readings beyond that bound.
- Final state: items-in=183 (42 + 140 + the heartbeat), 6 expected findings, last-run.json rc 0, failed_streak 0.
- **Not done at close (follow-up):** AC3.5, ubuntu's one convergence dry run on the pushed sha, goes via the leads; it is pending.

## Files Changed
`tools/sessions/project_sync.py`, `tools/sessions/project_client.py`, `tools/sessions/session_start_hook.py`, `registries/session_project.yaml`, `docs/guidelines/session_roles/project_sync_dry_run.md`, `tests/tools/test_session_project_sync_all_lanes.py`, `tests/tools/test_session_project_sync.py`, `tests/tools/test_session_project_sync_second_host.py`, `tests/tools/test_project_client.py`, ticket and stored artifacts, REGISTRY.yaml, monitoring shards.

## Completion Summary
Every registered domain is now a lane on Project 1; Domain is a single-select (the old text field is kept as `Domain (old)`); the first load wrote 140 new items and 41 Domain updates in 1608 paced steps with no rate-limit stop. `--fetch`, a last-run file with a two-failure start-hook warning, a cross-host heartbeat with a stale-host flag, the Tier leading-token rule and a whole-plan option check (live dry run and `--apply`) are built, tested and documented. The SEQUENCE.md filing-seat rule was dropped (no reliable carrier). Open: AC3.5 (ubuntu dry run), the owner's `has:status` view filter, deleting `Domain (old)` (separate owner ask).
