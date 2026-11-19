---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261119-FILED-TICKETS-ARE-SCANNED-FOR-OVERLAP-WITH-OPEN-TODOS
phase: done
date: 2026-11-19
tags: [create-tickets, ticket-scoper]
---

# TCK-20261119-FILED-TICKETS-ARE-SCANNED-FOR-OVERLAP-WITH-OPEN-TODOS

## Title
A ticket filed by hand into todos/ or inprogress/ is scanned for overlap with open tickets, and each hit is cited or explained (report-only)

## Status
DONE

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
Decided by agent-working-planner on the measured labels (origin/main 5bedb5ff0; 151 tickets filed in 21 days; a 20-pair stratified sample, precision about 50%, Wilson 95% roughly 28 to 72%):
1. Rule: the draft's title and Request Summary are scored with every `TCK-...` id removed; a hit is an open ticket whose weighted overlap is at least 0.25 of the draft's own total term weight (`q`; no raw-score floor, no epic exemption); at most the top 2 uncited hits are shown, ranked by `q`. About 47% of new tickets see a line: the price of keeping the owner-named inn-meal pair (q 0.259).
2. Output: one advisory line per ticket, `overlap scan: <path>: N candidate(s): <id> (<title>, q=<value>), ...`. A ticket that cites the hit in `## Related Tickets`, or carries `overlap scan: <n> hits, none duplicate (<why>)` there, is silent; the line is checked for presence only. Exit 0 always; `ran / skipped / errored` per run; a scanner failure is a named warning.
3. Hook: check H in `tools/delivery/pre_push_advisory_hook.py` calling the standalone `tools/gate_checks/ticket_overlap_check.py`, which is also run by hand before committing a ticket (a sentence in `docs/guides/delivery_process.md` and a pointer in `docs/guidelines/session_roles/functions/planner.md`, outside the injected Card). No `settings.json` or hook-registration edit. No `pr_render.py` change (decided later, after a prospective measure).
4. `ticket_overlap_check.py --report --since <date>` lists the open tickets filed since a date with their state (uncited candidate, waived, clean, errored): the prospective efficacy measure.
5. `.claude/agents/ticket-scoper.md` lists `todos/` in its scan and runs the checker on its draft. `.claude/workflows/create-tickets.js` and `.agents/rules/ticket.md` stay as they are (they do not restate the scan list).
6. Grandfathering: only tickets dated on or after 2026-11-21 (the day after the landing) are checked.
7. Docs: a section in `docs/guides/delivery_process.md` naming the check, the line format, that it is a locator and not a duplicate verdict, and the measured precision.

## Out of Scope
- Deciding whether a flagged pair is a duplicate (rpg-planner rules on the fixture pairs; an agent or person judges every future hit).
- Blocking a commit, a push or a close.
- Retroactive citation of existing overlaps.
- Changing the `open_ticket_overlap.py` scoring, except where the threshold measurement shows a defect (then a separate finding).

## Acceptance Criteria
1. Frozen synthetic fixtures flag the controls (label-sample rows 15 duplicate, 2 inn-meal, 1 and 8 related) and flag row 10 as a documented known false positive; a pair below 0.25 is not flagged.
2. The check reports ran / skipped / errored per run; a scanner failure prints a named warning and the exit code stays 0.
3. A cited hit is silent; a waiver line is silent; an uncited hit warns; ids in the title and summary are stripped before scoring; only the top 2 are shown.
4. The hook point's reach is stated next to the alternatives (357 ticket files in 21 days; done_checker_static reaches at most the closed ones, validate_frontmatter and pre-commit reach none at filing, the push advisory reaches every pushed ticket), and `--report --since` measures the effect prospectively.
5. `ticket-scoper.md` lists `todos/`; the tests that pin that file still pass.
6. Scoped tests only; no change to how a ticket is written beyond a line in `## Related Tickets`.

## Related Tickets`, or carries `overlap scan: <n> hits, none duplicate (<why>)` there, is silent; the line is checked for presence only. Exit 0 always; `ran / skipped / errored` per run; a scanner failure is a named warning.
3. Hook: check H in `tools/delivery/pre_push_advisory_hook.py` calling the standalone `tools/gate_checks/ticket_overlap_check.py`, which is also run by hand before committing a ticket (a sentence in `docs/guides/delivery_process.md` and a pointer in `docs/guidelines/session_roles/functions/planner.md`, outside the injected Card). No `settings.json` or hook-registration edit. No `pr_render.py` change (decided later, after a prospective measure).
4. `ticket_overlap_check.py --report --since <date>` lists the open tickets filed since a date with their state (uncited candidate, waived, clean, errored): the prospective efficacy measure.
5. `.claude/agents/ticket-scoper.md` lists `todos/` in its scan and runs the checker on its draft. `.claude/workflows/create-tickets.js` and `.agents/rules/ticket.md` stay as they are (they do not restate the scan list).
6. Grandfathering: only tickets dated on or after 2026-11-21 (the day after the landing) are checked.
7. Docs: a section in `docs/guides/delivery_process.md` naming the check, the line format, that it is a locator and not a duplicate verdict, and the measured precision.

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
`tests/tools/test_ticket_overlap_check.py` (18 tests on frozen synthetic corpora), the existing hook, scoper-pin, session-card and pr_render suites unchanged and passing.

## Files Changed
`tools/gate_checks/ticket_overlap_check.py` (new), `tools/delivery/pre_push_advisory_hook.py` (check H), `.claude/agents/ticket-scoper.md`, `docs/guides/delivery_process.md`, `docs/guidelines/session_roles/functions/planner.md`, `tests/tools/test_ticket_overlap_check.py` (new).

## Completion Summary
Built to the planner's decision: q >= 0.25, no raw floor, no exemption, ids stripped, top 2 uncited hits, one line per ticket; check H in the pre-push hook plus a standalone checker run by hand and by ticket-scoper; `--report --since` for the prospective measure. Precision about 50% (Wilson 28 to 72% on 20 labels), about 47% of new tickets see a line: stated in the docs. Open items: the inn-meal ticket ids (rpg-planner), the PR-body line (decided after a prospective measure), the likely duplicate pair TCK-20261101-CLEAR-TARGET-IS-NEVER-APPLIED and TCK-20261114-NAVIGATION-CLEAR-TARGET-FLAG-IS-NEVER-APPLIED (labelled DUP, rpg-planner to rule). Hand-orchestrated close.

Dated follow-up (owner: "Accept, measure after a week", #715): date 2026-11-28 (the landing date 2026-11-21, the first day tickets are checked, plus 7 days; if the merge lands later than 2026-11-21, `OVERLAP_CHECK_REQUIRED_FROM` in `tools/gate_checks/ticket_overlap_check.py` and this date are corrected before the merge). Runner: agent-working-planner. Command, on a named origin/main SHA: `python3 tools/gate_checks/ticket_overlap_check.py --report --since 2026-11-21`. The report goes to lead-planner for the owner and states: the tickets filed since the landing date, how many carry an uncited candidate, how many a waiver line, how many a citation, and any duplicate the planner or rpg-planner caught that the check did not flag.
