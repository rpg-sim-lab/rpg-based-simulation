---
status: active
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20261115-PROJECT-SYNC-ALL-LANES
phase: inprogress
date: 2026-11-15
tags: [planning, delivery]
---

# TCK-20261115-PROJECT-SYNC-ALL-LANES

## Title
`project_sync.py` P3b: every lane goes on Project 1, Domain becomes a single-select, the sync can fetch origin/main itself, and each host leaves a last-run file and a cross-host heartbeat

## Status
INPROGRESS

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

## Test Summary

## Files Changed

## Completion Summary
