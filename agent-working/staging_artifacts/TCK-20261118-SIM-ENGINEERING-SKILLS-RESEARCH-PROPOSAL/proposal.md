---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL
artifact_type: plan
tags: [skills, simulation-quality, testing]
---

# Proposal and eval plan (P4) - for owner approval; nothing here is built

Inputs: `coverage_audit.md`, `research.md`, `defect_set.md`. Rule: skills and checks encode how to reason and verify; they never restate world rules (Bible, `docs/engine/`, `docs/world_rules/` stay authoritative).

## 1. What the evidence supports
Of 10 historical defects (rpg-designer's six plus four extras), my class count is: lifecycle of durable records 5, time/scale 2, cross-layer interaction 2, measurement design 1. The request's four candidate areas are not equally supported. Cross-mechanism consistency and temporal reasoning each rest on 2 cases; mechanism design/review has no case of its own. Do not create a skill per candidate area.

Constraint from the catalog epic: domain skills were almost never invoked (zero for most; advisory suggestions acted on 0 of 20 times), while the one made binding (`security` -> Security-Review phase) works. Figures are from 2026-08 and need re-measuring. So the delivery form is the main design variable.

## 2. Options

| Option | What | For | Against |
|---|---|---|---|
| A. Do nothing new | Rely on current reviewers | Zero cost | Five lifecycle defects and two time defects got through green tests; current reviewer asks only "defined lifecycle?" in one line (`architecture-reviewer.md` line 23) |
| B. Harden an existing binding step (recommended core) | Replace the one-line lifecycle question in `architecture-reviewer` with a concrete checklist run at its existing pre-Implement and post-Implement phases: for each new/changed durable field or record - who creates it, does an update merge or replace (what survives), does every non-terminal state have an exit, is it cleared after success, one writer or one meaning per field. Add a time check: which clock does each reader use, and can the case under test occur inside the window | Binding by construction (the phase already runs); no new description competing for selection; directly maps to defects 2, 4, 5, latch, corpse sink, 1, 6 | Prompt grows; a checklist can raise false positives on ordinary changes; the time-semantics contract (which clock is canonical) is rpg's to define, not this checklist's |
| C. Stateful-property pilot | One `hypothesis` RuleBasedStateMachine for a lifecycle area (two passes in a row, every non-terminal state exits, value after a successful step) | Mechanical; targets the exact "tests checked one pass/one transition" cause; technique already allowed by `test_taxonomy.md` §6; `hypothesis` already a dependency | Seeded-determinism guidance is not in the docs read; bundles unreadable from invariants; needs a testing-track owner; fixture effort |
| D. One reference skill `simulation-verification` | Single skill, SKILL.md under ~150 lines, references one level deep: lifecycle checklist, time/scale check, interaction check, instrument chooser (Sargent traces, degenerate, extreme-condition) loaded by name from `architecture-reviewer`, `investigator`, `test-scoper` | One source of text for several roles; matches Anthropic progressive-disclosure form | Same text as B unless roles differ; a skill nobody calls is dead weight; extra frontmatter in every prompt. Only justified if the eval shows B's inline text is too large or is needed by 3+ roles |
| E. Four skills (design, consistency, temporal, verification) | The request's candidate structure | Matches the request wording | No evidence for the split; two have 2 cases, one has none; four descriptions to maintain and trigger; rejected |
| F. Cross-layer interaction procedure | Review step: does a lower layer's give-up reach the layer that re-chooses | Defect 3 and perception-inputs | 2 cases only; fold one checklist line into B and watch for more |

## 3. Recommendation
1. Do B first (small edit to one agent; binding). It is the cheapest test of the thesis that a concrete checklist at an existing gate catches these defects.
2. Run C as a separate pilot via the testing track (I do not own `tests/architecture/**`; route to testing-planner).
3. Ask rpg-planner whether a short time-semantics contract (raw tick vs world_time vs derived phase) should exist in `docs/engine/`; I do not define it. Add a "can the case occur inside the window" step to the bar/scenario design template.
4. Create skill D only if the eval below shows (a) the checklist measurably helps and (b) it is needed by three or more roles or exceeds what fits in an agent prompt. Default is no new skill.
5. Not now: metamorphic testing (gated on the parked determinism work), NASA credibility scoring, ODD.

## 4. Eval plan (nothing runs before approval)
Question: does the checklist (arm A1) or the skill form (arm A2) beat the current reviewer (arm A0) on defects, false positives and context cost?

- **Arms**: A0 current `architecture-reviewer`; A1 same agent with the checklist inline; A2 same agent told to load the skill (only if D is still in play). Hold model, harness, tools, token budget and scorer constant; run each arm on each model planned for use (Haiku, Sonnet, Opus tiers as S3 advises, where the agent's model setting allows).
- **Positive set**: the 10 defects. For each, rebuild the review input as it stood before the fix: the plan or diff for 2, 3, 4, 5 and the corpse/latch cases; the rule text or bar design for 1 and 6 (found at review, not in a diff, so these test the time check on design text). Anthropic's minimum is three scenarios; ten gives a rate, still small. Extend to 20 by mining `agent-working/tickets/done/` for tickets tagged `escaped-defect` (tag exists in the registry).
- **Negative set**: 10 merged tickets with no later defect, same size mix, to count false positives per ticket.
- **Leak control**: the fix tickets and registry entries name the defects. Run in a checkout or with context that excludes post-fix tickets, `docs/` text mentioning them, and the working log rows; verify with a check that the defect's ticket id does not appear in the agent's tool results.
- **Metrics**: (1) critical findings caught = positive cases where a finding names the real mechanism, judged by a fixed rubric from `defect_set.md`; (2) false positives = findings on negative cases that a reviewer rejects, per ticket; (3) context overhead = extra input tokens and tool calls per run, from run usage; also report the finding's severity label.
- **Scoring**: a finding counts only if it identifies the cause (for example "update replaces the record, erasing suppression"), not merely the file. Two scorers: the rubric, plus a human spot check of a sample by rpg-designer for borderline findings.
- **Decision rule (proposed)**: keep A1 if it catches at least 2 more positive cases than A0 with no more than 1 extra false positive per 5 negatives and under ~10% added tokens; otherwise drop or reshape. Thresholds are mine, for the owner to set.
- **Cost**: LLM review runs only, no simulation runs. Rough scale: (10+10 cases) x 2-3 arms x 1-3 models = 40-180 runs. Token budget needs an owner number. Anthropic notes no built-in eval runner exists, so a small script in the scratchpad or `tools/` is needed; that script is part of the approved work, not this proposal.
- **Reuse**: skill-usage tracking from the catalog epic (`skill_usage_metric.py`) to measure, after any rollout, whether a skill form is invoked at all.

## 5. Risks and unknowns
- Sample is small and rpg-designer's labels (including the ambiguous "4 (the first defect)") were not independently checked against git; the eval build step must re-verify each ticket and commit.
- Selection bias: these ten were remembered because they were costly; quiet defects are not in the set.
- Checklist drift into rules: any item that states a world rule (which clock is canonical) belongs in `docs/engine/`, not in an agent file.
- Attach point not fully verified: I read the `architecture-reviewer` durable-state bullet and `plan_gate_static.py` (which only checks "Unresolved Questions"), not the whole `implement-ticket.js` flow.
- Hand-orchestrated work bypasses the pipeline phases; a gate in `architecture-reviewer` binds only when that agent is run. Need to confirm how often it is.

## 6. Decisions requested from the owner (via the leads)
1. Approve B (checklist in `architecture-reviewer`) as the first implementation, and the eval before any skill.
2. Approve routing C to testing-planner and the time-contract question to rpg-planner.
3. Set the eval token budget and the decision thresholds.
4. Confirm that skill D and the four-skill structure stay off the table until the eval reports.
