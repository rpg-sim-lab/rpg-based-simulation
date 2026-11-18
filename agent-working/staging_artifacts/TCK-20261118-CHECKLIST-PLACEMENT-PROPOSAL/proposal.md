---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261118-CHECKLIST-PLACEMENT-PROPOSAL
artifact_type: plan
tags: [skills, process-improvement]
---

# Placement proposal: lifecycle and clock checklist

Checklist content is the 8-item draft in `TCK-20261118-ARCH-REVIEWER-LIFECYCLE-TIME-CHECKLIST-EVAL` (creation, update merge-vs-replace, exit for every non-terminal state, clear after success, one writer/one meaning, which clock, window, cross-layer reset). It states questions only, never world rules; the clock rule belongs to the planned `docs/engine/time_semantics.md`.

## 1. What fires today (measured, origin/main 169deedc0, 374 tickets closed since 2026-10-19)
| Point | Fires on | Source |
|---|---|---|
| Ticket filing (template sections, `ticket_field_values.py`) | every ticket, by construction | all closed tickets have a ticket file |
| Working-log row at close | every closed ticket, by definition of "closed" | working_log |
| PR body (template, `pr_render.py`, `pr-body-lint` CI) | every PR | .github/pull_request_template.md |
| Closure tool events | 138 of 374 (37%) | events present; 236 closed with no phase events at all |
| Plan phase | 60 (16%) | non-skipped events |
| Review phase event | 28 (7.5%) | non-skipped events |
| Architecture-Verify | 1 (0.27%; Wilson 0.05% to 1.5%) | 62 skipped `no_hand_tool` |
Even the closure tool is not universal (37%), and its phase events are self-reported ("Scope ok" is written by whoever closes), so event presence is not proof that a check happened. The universal points are the ticket, the working-log row and the PR.

## 2. Options
| # | Placement | Binding? | Fires on | Context cost | False-positive risk | Main weakness |
|---|---|---|---|---|---|---|
| O1 | `architecture-reviewer` prompt (original B) | Advisory inside a phase that rarely runs | ~0.3% of closes | ~12 lines per review | Medium (whole-tree audits flag a lot; smoke run gave 9 findings on a negative) | Almost never invoked |
| O2 | Ticket template: required section "Durable state, lifecycle and clocks" (or `N/A: <reason>`), checked for presence by `ticket_field_values.py` | Binding on presence, advisory on quality | Every new ticket, before code | ~8 lines per ticket authoring; read again by planner at review | Low for the check (presence only); the cost is rote "N/A" | Does not judge quality; most tickets do not touch durable state, so most answers are N/A |
| O3 | PR body: `pr_render.py` copies the ticket's section into "Verification"; `pr-body-lint` fails a PR whose body lacks it when the body lists src tickets | Binding on presence in CI | Every PR | Near zero (rendered) | Low | Same as O2; lint sees the body, not the diff |
| O4 | `done_checker_static` condition "lifecycle_section_present_or_na" | Binding at close, but only if the close runs the checker (not recorded as universal) | Unknown share of hand closes | Near zero | Low | Late: after the code exists |
| O5 | Planner PR review duty: checklist added to the planner role guideline and used when reviewing src PRs | Advisory (human or LLM judgment) | Every src PR the planner reviews | Planner context per PR | Medium | Depends on the reviewer remembering; the review event is recorded for only 7.5% of closes |
| O6 | Deterministic source-scan tests for the checkable parts: raw `world_time` arithmetic outside `calendar.py` (rpg-planner already plans this for `time_semantics.md`); a latch-style check (field assigned True, never False) as a heuristic | Binding in CI | Every PR touching src | None for agents | Time scan: low; latch heuristic: high | Covers only the mechanical subset; cannot see merge-vs-replace or missing exits |
| O7 | Stateful property tests for lifecycle (pilot ticket TCK-20261118-STATEFUL-PROPERTY-PILOT-FOR-RECORD-LIFECYCLES) | Binding in CI once written | Per lifecycle area | Authoring cost | Low | One area at a time |
| O8 | Mechanism registry `lifecycle:` block validated by the completeness check | Binding for registered mechanisms | New or changed mechanisms | High | Low | Heavy; covers only registered mechanisms |

## 3. Recommendation (layered, smallest first)
1. O2 plus O3: the ticket section, rendered into the PR body, checked for presence. It is the only candidate that is both early and present on every ticket and PR, and it needs no new agent.
2. O6 for the clock rule once `time_semantics.md` lands (rpg-planner's source-scan test), which makes the time check binding without an LLM.
3. O7 pilot as already routed to testing-planner (lifecycle defects, binding in CI).
4. O5 as a low-cost advisory: one line in the planner review guidance pointing at the same section.
5. Keep O1 only as a later option if pipeline use grows; do not spend further effort on it now.
Not recommended now: O4 (late), O8 (heavy).

## 4. Trade-offs the owner should weigh
- Presence checks are gameable ("N/A: no durable state"). O2/O3 make the author state the answer before coding; they do not prove it is right. Quality needs the reviewer (O5) or tests (O6, O7).
- Most tickets touch no durable state; an always-present section adds noise. Mitigation: a one-line `N/A` is accepted, and only tickets touching `src/` are required to have it.
- Cost of O2 scales with ticket volume (about 87 closed tickets a week, from 374 in 30 days).

## 5. Measuring each option (honest limits)
- Coverage (fires?): O2/O3/O4/O6 by construction or by counting; measure with the same pinned-ref method used above (fill rate, `N/A` rate, share of src tickets with a non-N/A section).
- Efficacy (catches defects?): a retrospective replay is limited by the same data problem as before: for defects 2, 4 and the latch no plan or diff exists, and all 3 usable positives were checklist sources (held-out = 0). So the real test is prospective: defects first reported after 2026-11-18 (holdout_candidates.md in the on-hold eval branch), counted by whether the ticket that introduced them had the section filled, N/A, or absent. Needs time; the base rate is unknown (about 10 remembered defects over a few weeks).
- Quality of the filled section: a blind judge reads the section and the diff on a sample and rates whether the answer is true; this can reuse the on-hold harness (`run.py`, rubric, Amendment A's known-defect handling) with a different input and no A0/A1 arms. Not run.
- False-positive / noise cost: share of sections answered `N/A`, time added per ticket (sampled), and planner-reported rework.
- Reuse of the committed pre-registration (ee0674e06 + a50176364): the holdout rule, the known-defect column, the Wilson-interval reporting and the "coverage bounds expected benefit" statement carry over unchanged; the A0/A1 arms and the 38-run count do not apply to O2/O3.

## 6. Decisions for the owner
1. Which of O2+O3, O5, O6, O7 to approve (recommendation: O2+O3 first, O6 when the contract lands, O7 as routed, O5 as a one-line advisory).
2. Whether a `src/`-only requirement is acceptable for O2.
3. Whether the on-hold eval stays parked (my suggestion) or is closed without a run.
No file outside this ticket's artifacts is changed by this proposal.
