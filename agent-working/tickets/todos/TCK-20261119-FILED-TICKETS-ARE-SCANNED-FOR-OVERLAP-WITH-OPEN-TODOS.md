---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261119-FILED-TICKETS-ARE-SCANNED-FOR-OVERLAP-WITH-OPEN-TODOS
phase: open
date: 2026-11-19
tags: [create-tickets, ticket-scoper]
---

# TCK-20261119-FILED-TICKETS-ARE-SCANNED-FOR-OVERLAP-WITH-OPEN-TODOS

## Title
A ticket filed by hand into todos/ or inprogress/ is scanned for overlap with open tickets, and each hit is cited or explained (report-only)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Owner (#715 7003894694, words logged there): "is the process of creating tickets from findings ... actually check the duplication or confliction with the existing todos, or just blindly creating one, this is a serious issue if it happen". Relayed by lead-planner from lead-planner-u24's evidence (#715 7003841278; not re-measured by the planner): `create-tickets` ran 0 times in W45-W47 while `implement-ticket` ran 179, so finding-tickets are filed by hand; `tools/open_ticket_overlap.py` runs only inside `concern-investigator` and `implement-ticket.js` step 3c; `.claude/agents/ticket-scoper.md` line 13 searches only `inprogress/`, `done/` and `backlogs/`. Real misses, used here as regression fixtures:
- `TCK-20261117-THE-SLOW-CORPUS-GRADE-PINS-ARE-STALE-ON-MAIN` overlaps `TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT` (score 81.5) and does not link `TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE`.
- The inn-meal tickets are not linked to #781's ticket (ids to be filled by rpg-planner, who also rules on whether each pair is a real duplicate).

## Scope
1. Re-measure the evidence on a named ref and SHA: how many open tickets filed in the last N weeks have an overlap hit above the candidate threshold and no citation of it. Decide a threshold from that, with the two fixture pairs as positive controls and a sample of unrelated pairs as must-not. `open_ticket_overlap.py` states that an absolute score cutoff is not robust across queries and that its `top_n` cap bounds output, so the threshold must be shown against the real corpus, not asserted.
2. A check run on each new or changed `todos/` or `inprogress/` ticket file: it runs `tools/open_ticket_overlap.py` on it. Each hit above the threshold must appear as a ticket id in the ticket's `## Related Tickets`, or `## Related Tickets` carries the line `overlap scan: <n> hits, none duplicate (<why>)`. The check looks for the id or the line only; it never judges the reason. It WARNS and never blocks (advisory, exit code unchanged), and reports ran / skipped / errored.
3. Pick the hook point from a measured comparison of: `validate_frontmatter`, the pre-commit hook, the push advisory, and `done_checker_static`. The hook must fire at filing, not only at close (a hand-filed ticket may never reach a closer), and the plan states how many of the tickets filed in the last N weeks would have been reached by each candidate, since an earlier checklist placement was retracted for missing exactly this.
4. Add `todos/` to ticket-scoper's mandatory scan list (`.claude/agents/ticket-scoper.md`, step 1) and tell it to run `open_ticket_overlap.py` on its draft. `.claude/workflows/create-tickets.js` and `.agents/rules/ticket.md` wording follow only if they restate the scan list.
5. Grandfathering: only tickets new or changed on or after the landing date are checked; the existing corpus is not scanned retroactively.
6. A short guide paragraph in `docs/guides/delivery_process.md` naming the check, the line format, and that the scan is a locator, not a duplicate verdict.

## Out of Scope
- Deciding whether a flagged pair is a duplicate (rpg-planner rules on the fixture pairs; an agent or person judges every future hit).
- Blocking a commit, a push or a close.
- Retroactive citation of existing overlaps.
- Changing the `open_ticket_overlap.py` scoring, except where the threshold measurement shows a defect (then a separate finding).

## Acceptance Criteria
1. On a named SHA, the two fixture pairs are flagged by the new check (positive controls) and a sample of at least 10 unrelated pairs is not (must-not); both lists are shown.
2. The check reports ran / skipped / errored for each file, and a failure of the scanner itself is a warning that names the error, never a silent pass.
3. A ticket citing its hits, and a ticket carrying the `overlap scan:` line, both pass; a ticket with an uncited hit and no line warns; the exit code is 0 in every case.
4. The chosen hook point's reach is measured on the tickets filed in the last N weeks and stated next to the alternatives.
5. `ticket-scoper.md` lists `todos/`; the session-card and agent tests that pin that file still pass.
6. Scoped tests only; no change to how a ticket is written beyond a line in `## Related Tickets`.

## Related Tickets
- TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER (built `open_ticket_overlap.py`)
- TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED (sequencing: this ticket is dispatched behind it)
- TCK-20261117-THE-SLOW-CORPUS-GRADE-PINS-ARE-STALE-ON-MAIN, TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT, TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE (fixture pairs)
- overlap scan: 5 hits, none duplicate (run by the planner with tools/open_ticket_overlap.py on this draft: top hit TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT at 50.9 is a fixture this ticket names; the other four score 21-25 on generic shared words, TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2, TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT, TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS, TCK-20260915-SIMQ-CORPUS-BLIND-TO-SCALE-DEPENDENT-BEHAVIOR)

## Related Docs
- `docs/guides/delivery_process.md`
- `agent-working/stored_artifacts/TCK-20261118-CHECKLIST-PLACEMENT-PROPOSAL/proposal.md` (the lesson: measure which placement fires on hand-filed work before choosing it)

## Related Stored Artifacts
- none yet

## Related Code Areas
- `tools/open_ticket_overlap.py`
- `.claude/agents/ticket-scoper.md`, `.claude/agents/concern-investigator.md`
- `tools/validate_frontmatter.py`, `tools/gate_checks/done_checker_static.py`, the pre-commit hook
- `tests/tools/test_open_ticket_overlap_real_corpus.py`, `tests/tools/test_ticket_scoper_relevance_check.py`

## Assumptions / Open Questions
- The evidence numbers (0 create-tickets runs, 179 implement-ticket runs) are lead-planner-u24's and unchecked by the planner.
- The inn-meal ticket ids are not yet known.
- Observed on this very draft: ids a ticket cites in its own body raise the score of the tickets it cites (the fixture pair scored 50.9 here). Step 1 must decide whether the check scores the draft with its Related Tickets ids removed.
- `.claude/agents/**` is the planner role's own path; check whether the governing-file edit rule applies to `ticket-scoper.md`.
- Sequencing: behind the Project view ticket; RPG first for the slot and memory.

## Durable state, lifecycle and clocks
N/A: no src change; a tools check and agent wording only, no stored state.

## Implementation Notes
Filed by agent-working-planner on lead-planner's relay of an owner request (#715 7003894694). Standard tier: plan, investigation and test_plan before build.

## Test Summary

## Files Changed

## Completion Summary
