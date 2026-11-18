---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261118-ARCH-REVIEWER-LIFECYCLE-TIME-CHECKLIST-EVAL
phase: open
date: 2026-11-18
tags: [skills, simulation-quality, testing]
---

# TCK-20261118-ARCH-REVIEWER-LIFECYCLE-TIME-CHECKLIST-EVAL

## Title
Eval a concrete lifecycle and time checklist for architecture-reviewer, and adopt it only if the keep rule passes

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Owner decision on #715 (logged via lead-planner, 2026-11-18): approve Option B plus an eval first. Turn the one-line "defined lifecycle" question in `.claude/agents/architecture-reviewer.md` (durable-state rule bullet) into a concrete lifecycle and time checklist, but measure it first. A skill (Option D) is built only if the eval shows a gain; the four-skill structure is rejected. Decision record: `agent-working/stored_artifacts/TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL/proposal.md` (§2-§6).

## Scope
1. Re-verify the defect set against git. For each of the 10 defects in `defect_set.md`, find the ticket, the introducing commit and the fixing commit; record which input the reviewer would have seen before the fix (plan, diff, or rule/bar text). Resolve the ambiguous relayed label "4 (the first defect)" with rpg-designer (via the leads) before scoring. Defects with no recoverable pre-fix input are dropped and the count reported.
2. Build the case set: positives (up to 10, extend toward 20 from `escaped-defect`-tagged tickets only if cheap) and 10 negatives (merged tickets with no later defect, similar size mix). Fix the scoring rubric (a finding counts only if it names the cause, not just the file) before any run.
3. Build the harness: a script that replays each case through `architecture-reviewer` under two arms and records findings, input tokens and tool calls. Leak control: the agent must not see the fix tickets, working-log rows or docs naming the defect; verify the defect ticket id never appears in the agent's tool results.
4. Pre-registered design (fixed now, before data):
   - One model: `claude-sonnet-5-5` for both arms. Chosen before any data; recorded in the run output.
   - Arms: A0 = current `architecture-reviewer`; A1 = same agent with the checklist below inline (as an eval variant file, NOT yet the live agent file).
   - About 40 runs: 20 cases x 2 arms x 1 model. Heavy simulation runs are not involved.
   - Keep rule, exactly: A1 is kept only if it catches at least 2 more positives than A0, adds at most 1 false positive per 5 negatives, and adds under 10% input tokens.
5. If the keep rule passes: apply the checklist to `.claude/agents/architecture-reviewer.md` (this file routes to agent-working-planner; commit through the implementer) and close. If it fails: record the result, do not edit the agent, and close with the data. Either outcome is a valid close.
6. Report the result to the leads with: counts per arm, per-case table, tokens, and a recommendation on Option D (build a skill only if the checklist helped AND three or more roles need it).

## Out of Scope
- Writing any skill, running a larger or multi-model eval, or changing the keep rule after seeing data.
- Defining which clock is canonical (raw tick vs world_time vs derived phase): that is a `docs/engine/` contract routed to rpg-planner by lead-planner. The checklist only asks which clock each reader uses.
- The stateful-property pilot (separate ticket `TCK-20261118-STATEFUL-PROPERTY-PILOT-FOR-RECORD-LIFECYCLES`).
- Restating any Mechanics Bible, engine or world_rules law in the checklist.

## Acceptance Criteria
- A defect-to-git table exists for all 10 defects, with dropped cases and reasons, and the "4 (first defect)" ambiguity resolved in writing.
- Rubric, case set and arm files are committed before the first run; the keep rule and model are unchanged from this ticket.
- Results table per case and arm, token overhead, and a PASS/FAIL against the keep rule are stored under `agent-working/stored_artifacts/<this ticket>/`.
- The live agent file is changed if and only if the keep rule passed.
- Leaked-context check recorded.

## Related Tickets
- TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL (source of the decision)
- TCK-20261118-STATEFUL-PROPERTY-PILOT-FOR-RECORD-LIFECYCLES (sibling)
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (usage-tracking tooling to reuse)

## Related Docs
- docs/engine/time_semantics.md: PLANNED (rpg-planner confirmed via lead-planner 2026-11-18; new file linked from kernel.md and deterministic_execution.md; core rule is one named clock per reader: cadences and keyed draws use the absolute kernel tick, world_time only through calendar helpers, no raw world_time arithmetic outside src/core/calendar.py, pinned by a source-scan test; rpg-designer rules the text, rpg-planner files the ticket after M1 Phase 1). Not yet landed: the checklist item 6 states the question only and must not restate that rule.
- docs/testing/test_taxonomy.md (§6 technique criteria)
- agent-working/stored_artifacts/TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL/ (proposal, defect_set, research, coverage_audit)

## Related Stored Artifacts
- as above

## Related Code Areas
- .claude/agents/architecture-reviewer.md, tools/gate_checks/architecture_reviewer_static.py

## Assumptions / Open Questions
- Pre-fix inputs for defects 1 and 6 are design/rule text, not diffs; they test the time check only on text. If unrecoverable, drop and say so.
- The defect labels came from rpg-designer's memory (relay), not git; Scope step 1 verifies them.
- Whether the harness can be run by a subagent given context-leak limits is to be confirmed; if not, a local script with fresh sessions is used.
- Hand-orchestrated work bypasses the Architecture-Verify phase; how often that happens is not measured here.

## Implementation Notes
Draft checklist for arm A1 (review prompts only; no world rules). For each new or changed durable field, record or state:
1. Creation: who creates it, under what condition, and is creation idempotent across two consecutive passes?
2. Update: does an update merge or replace? What survives a replace (suppression, counters, timestamps)?
3. Exit: does every non-terminal state have a way out (expiry, completion, abandon)? What bounds how many can exist?
4. Clearing: is the value cleared or reset after a successful step, and is there a test of the value after success?
5. Writers and meaning: how many code paths write it, and does it carry exactly one meaning?
6. Clock: which clock does each reader use (raw tick, world_time, derived phase)? Do fixtures cover more than one phase? (Cite `docs/engine/time_semantics.md` once it lands: PLANNED, not yet landed.)
7. Window: for a gate, bar or scenario with a time window, can the case under test occur inside it given current durations?
8. Layers: does a lower layer's give-up or reset reach the layer that re-chooses?

## Test Summary
(filled at close)

## Files Changed
(filled at close)

## Completion Summary
(filled at close)
