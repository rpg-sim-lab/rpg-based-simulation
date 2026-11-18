---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261118-REQUIRED-DURABLE-STATE-LIFECYCLE-CLOCKS-SECTION-IN-TICKETS-AND-PR-BODIES
phase: done
date: 2026-11-18
tags: [skills, process-improvement]
---

# TCK-20261118-REQUIRED-DURABLE-STATE-LIFECYCLE-CLOCKS-SECTION-IN-TICKETS-AND-PR-BODIES

## Title
Tickets carry a required "Durable state, lifecycle and clocks" section, presence-checked at close and rendered into the PR body, with a planner-review advisory line

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Owner approved on #715 (2026-11-18, via lead-planner): placements O2, O3 and O5 of `agent-working/stored_artifacts/TCK-20261118-CHECKLIST-PLACEMENT-PROPOSAL/proposal.md`. Reason: of 374 tickets closed since 2026-10-19 only 1 had an architecture-reviewer pass (0.27%), so a checklist in that agent almost never fires; the ticket file, the working-log row and the PR body are the only points every close passes. Defects behind it: raw `world_time` night check (#953), the suspended project that never exits (#954), the stale failure reason, the `moved_recently` latch, the blocker re-created every 80 ticks (replace vs merge). Owner input relayed the same day (#715 6972036075): prefer executable checks over prose; whatever cannot be checked mechanically goes in one short required section with a non-empty check.

## Scope
1. Ticket template: add the section `## Durable state, lifecycle and clocks` to the required list. Its body is either `N/A: <reason>` or short answers to: what durable fields or records this ticket creates or changes; for each, who creates it, whether an update merges or replaces, how every non-terminal state exits, who clears it; which clock each reader uses. Questions only, no world rules (the clock rule is the planned `docs/engine/time_semantics.md`, PLANNED, not landed). Update every template source: `.claude/workflows/create-tickets.js`, `.claude/agents/ticket-scoper.md`, the `create-tickets` skill and `.agents/rules/ticket.md` (run the router on each path first; implement only paths the router assigns to your seat and file the rest as asks).
2. Presence check: extend `tools/ticket_field_values.py` with a check that the section exists and is non-empty after stripping (for `N/A:` the reason after the colon must be non-empty). Required only for tickets dated on or after the landing date, so closed and open tickets are grandfathered; wire into `done_checker_static.py` the way `check_ticket_field_values` is wired, as a blocking condition.
3. PR body: add the line to the `## Verification` section in `.github/pull_request_template.md` and `tools/delivery/pr_template_spec.json`; `tools/delivery/pr_render.py` renders each ticket's section there (a ticket with no src change renders `N/A: no src change` itself); `tools/delivery/pr_body_lint.py` and its CI job fail a PR body whose Verification section lacks the line. The lint must not fail PRs rendered from the template that touch no src.
4. O5, advisory: add one line to the planner PR-review guidance (`docs/guidelines/session_roles/`; regenerate cards with the generator, do not hand-edit generated files) pointing at the section.
5. Tests for each changed tool (presence check cases: absent, empty, `N/A:` with and without reason, grandfathered date; renderer; lint).
6. Baseline for the prospective measurement: record, at close, the number of tickets created since the landing date (zero) and the fill and `N/A` rate script (`tools/` or the ticket's artifacts), so the owner can read fill rate, `N/A` rate and defects-by-section-state after 4 weeks. Efficacy is measured prospectively on defects first reported after 2026-11-18; the on-hold eval stays PARKED.

## Out of Scope
- Editing `CLAUDE.md`. Its "Ticket Format → Required sections" list must change too. CLAUDE.md edits need the owner's direct yes each time: STOP before that step and ask the owner (via the lead); ship the rest and flag the gap in the PR.
- O6 executable checks (below): not built under this ticket.
- O4, O8 and the parked architecture-reviewer eval.
- Judging answer quality (presence only).

## O6 candidates (designed here, NOT built; each needs the owner's OK first)
The owner prefers executable gates. O6 was approved for (3) plus the latch heuristic only. Candidates, each tied to a real defect, run in CI on the PR diff (every src PR passes there; the closure tool covers only 138 of 374 closes), scanning only the ticket's own diff:
1. Every new non-terminal state or status value has a tested exit transition (#954). Cost: finding new enum members or status constants in the diff, then a test that reaches an exit; moderate, false-positive risk where exits are implicit.
2. Every new durable field has a named clear or end writer, or a declared "never cleared, because ..." (stale reason, latch). Cost: a dataclass/model diff to find new fields, then a writer search; moderate to high, field-name heuristics.
3. No raw `world_time` arithmetic outside `src/core/calendar.py`, as a source scan (#953). Built after `docs/engine/time_semantics.md` lands (rpg-planner's ticket); cheap and low false-positive. APPROVED.
4. A replace-vs-merge declaration on updates to a durable record (blocker churn). Cost: needs a declaration syntax and detection of record replacement; high.
Latch heuristic (field assigned True and never False): APPROVED, high false-positive risk, report-only first.
Keep each check fast (diff-scoped, AST only). `tools/mechanism_registry/mechanism_registry_changed_code_check.py` already diffs a ticket's commits and is a building block. Ask for the owner's OK on (1), (2) and (4) before any build.

## Acceptance Criteria
- A ticket dated on or after the landing date without the section cannot pass `done_checker_static`; older tickets are unaffected.
- A rendered PR body carries the line; the lint fails a body without it and passes one rendered from the template for a no-src ticket.
- Router-assigned template sources updated; others filed as asks; CLAUDE.md flagged for an owner ask, not edited.
- Scoped tests pass; the existing corpus tests over old tickets still pass.
- Fill-rate script exists and its first output is recorded.

## Related Tickets
- TCK-20261118-CHECKLIST-PLACEMENT-PROPOSAL
- TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL
- TCK-20261118-ARCH-REVIEWER-LIFECYCLE-TIME-CHECKLIST-EVAL (parked)
- TCK-20261118-STATEFUL-PROPERTY-PILOT-FOR-RECORD-LIFECYCLES (O7)

## Related Docs
- docs/guides/delivery_process.md (PR template contract), docs/testing/test_taxonomy.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261118-CHECKLIST-PLACEMENT-PROPOSAL/
- agent-working/stored_artifacts/TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL/

## Related Code Areas
- tools/ticket_field_values.py, tools/gate_checks/done_checker_static.py, tools/delivery/{pr_render.py,pr_body_lint.py,pr_template_spec.json}, .github/pull_request_template.md, .github/workflows/pr-body-lint.yml, .claude/workflows/create-tickets.js, .claude/agents/ticket-scoper.md, .claude/skills/create-tickets/, .agents/rules/ticket.md

## Assumptions / Open Questions
- Landing date and the exact "src ticket" rule (Related Code Areas names `src/`, or the branch diff touches `src/`) are the implementer's call; state them in the ticket.
- Whether `.agents/rules/ticket.md` and the other template files route to your seat is unchecked by me.

## Durable state, lifecycle and clocks
N/A: tooling and process text only; no simulation record, field or clock is created or changed.

## Implementation Notes
Dispatch needs normal review (touches a ticket template, the done checker, the renderer and the lint).

## Test Summary
Scoped, no heavy runs: `python3 -m pytest -q tests/tools/test_lifecycle_section.py tests/tools/test_done_checker_static.py tests/tools/test_delivery_pr_render.py tests/tools/test_pr_body_lint.py tests/tools/test_pr_body_lint_workflow_pinned.py tests/tools/test_ticket_field_values.py tests/tools/test_session_cards.py tests/tools/test_session_agent_generator.py tests/tools/test_session_card_citations.py tests/tools/test_ci_workflow_test_coverage.py tests/integrity/test_no_duplicate_content_blocks.py tests/tools/test_generate_registry.py` plus the five test_create_tickets_* files: 630 passed. `python3 -m tools.sessions.generate_agents --check` OK; `python3 -m tools.generate_registry --check` in sync.
Known gap: a hand-written PR body with no `## Tickets` heading skips the lint (a known bypass).
Known gap: advisory first (owner decision #715 6972698325): a missing section is reported, not failed, until the owner promotes the check after the fill-rate baseline.
Known gap: O5 sits in `docs/guidelines/session_roles/functions/planner.md` outside the injected Card, because the planner cards are at the token budget.

## Files Changed
- `CLAUDE.md` (one line), `.agents/rules/ticket.md`, `.claude/workflows/create-tickets.js`, `.claude/skills/create-tickets/SKILL.md`
- `tools/ticket_field_values.py`, `tools/gate_checks/done_checker_static.py`, `tools/gate_checks/lifecycle_section_fill_rate.py` (new)
- `tools/delivery/pr_render.py`, `tools/delivery/pr_body_lint.py`, `tools/delivery/pr_template_spec.json`, `.github/pull_request_template.md`
- `.claude/agents/ticket-scoper.md`, `docs/guidelines/session_roles/functions/planner.md`, `docs/guides/delivery_process.md`
- `tests/tools/test_lifecycle_section.py` (new), `tests/tools/test_done_checker_static.py` (count 8 to 9)

## Completion Summary
Landing date 2026-11-19: tickets dated on or after it need `## Durable state, lifecycle and clocks` (`N/A: <reason>` or answers); older tickets, and tickets with no parseable date, pass as grandfathered. `done_checker_static` runs it as the ADVISORY check `ticket_lifecycle_section` (OK/WARN/NA, shown with the other `[advisory]` lines, never changes the verdict). **Advisory first; promotion to blocking is a later owner decision after the fill-rate baseline.** The PR body gets one `- Durable state, lifecycle and clocks: <ticket>: <text>` Verification line per ticket, `N/A: no src change` when the diff touches no `src/` (the src rule is the PR diff, not the ticket's Related Code Areas); `pr_body_lint.py` reports (warning, exit unchanged) a body whose `## Tickets` table lists an id dated 20261119 or later and has no non-empty line; bodies listing only older tickets are never flagged. Other bodies (Dependabot, hand-written, no `## Tickets` heading) are not checked: a known bypass. CLAUDE.md's Required sections list gained the section line (owner yes #715 6972548742). The three create-tickets template sources are in their own commit. Baseline fill-rate output recorded at close (`python3 tools/gate_checks/lifecycle_section_fill_rate.py`):

```
tickets dated on or after 2026-11-19: 0
  answers: 0
  na_with_reason: 0
  missing_or_invalid: 0
fill rate (section present and valid): n/a (no tickets yet); N/A rate: n/a (no tickets yet)
```

Efficacy is measured prospectively on defects first reported after 2026-11-18; the on-hold architecture-reviewer eval stays parked and untouched. Open items: see the Known gap lines in Test Summary.
