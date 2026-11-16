---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261115-PAST-THE-STARVING-LINE-THE-TACTICAL-STEP-TURNS-AWAY-FROM-A-MEAL-WITHOUT-WEIGHING-HUNGER
phase: open
date: 2026-11-15
tags: []
---

# TCK-20261115-PAST-THE-STARVING-LINE-THE-TACTICAL-STEP-TURNS-AWAY-FROM-A-MEAL-WITHOUT-WEIGHING-HUNGER

## Title
Past the starving line, with a meal 1-2 ticks away, the tactical fight-or-flee step (a panic retreat or a chase) takes the subject away from the meal without weighing starvation (SURV-07)

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
D1 from the V3 trace. Owner choice: #715 6893303548, "(a) Two defect tickets (Recommended)", on rpg-designer's row .claude/handover/drafts/rpg-designer-v3-trace-owner-row.md. This is the cause of the V3 gate red after #884 (#669: crowded_frontier s45 e5 and s46 e4). Trace: spy b1500149 on tree 824483949, both cells hash-matched with 0 errors (/mnt/data2/rpg-measure/v3trace/cellA.json a0468694…, cellB.json cec87d05…).
- **s45 e5:** at t2155 the decision is PANIC_RETREAT, away from the inn. The subject has hp 1, hunger 100, the inn 2 ticks away, and e35 engaged. It dies of STARVATION at t2161.
- **s46 e4:** at t3226 the decision is a tactical ENTITY_MOVE with target_id 35, the pursuit branch (tactical.py ~:773 on 824483949). The subject has hp 32, hunger 100, the inn 1 tick away. It takes 2 hits at t3237 and dies of STARVATION at t3245, 2 ticks from the inn.
- SURV-07 (row 83) says that past the starving line, starvation is a present threat, weighed against the hostile threat, with neither winning by default. The goal level weighs it; these tactical branches do not.

## Scope
1. The design is rpg-designer's, written before dispatch. It folds in the designer's parked finding on branch order at hp < 15% (tactical ~:508). The planner and implementer plan from it, and the designer reviews.
2. Implement it, through typed state only, with the Bible 02 and 04 text, the parity ledger and a divergence entry in the same change.
3. Measurement: the death bar, 3 worlds × 5 seeds, paired (decision 76), with the §12.5 stop rules.

## Out of Scope
- The V3 way-open rule. The designer parked it as a P3 record-honesty item, with no ticket.
- The felt-lethal hold and its memory (the trace showed it was correct).
- D2, the walk-target reset (its own ticket).

## Acceptance Criteria
- Past the starving line with an open meal in reach, the tactical step weighs starvation against the threat, as SURV-07 says. Unit tests cover the two traced shapes, retreat and pursuit, and a control where the threat must still win.
- The paired run is inside its stop rules. The V3 rows cf/45 e5 and cf/46 e4 are resolved, or re-owned with a stated reason.
- Docs, ledger and divergence entry in the same change.

- SUPERSEDED: the ~30-run paired measurement (3 worlds x s42-46 x 5000t) named in the criteria above is replaced by the section below (owner #715 6912138476). Balance rows r1/r2 are report-only there.

### Own-job counts (HARD, fixed before data; rpg-designer, owner 6912138476)
Copied verbatim from `.claude/handover/drafts/rpg-designer-d1-own-job-counts.md` v2 (sha256 55d94a58db647beb4764aab6f77227f615ac187e3132024ba00a01de2617a43d; supersedes v1 0a1cd679); only the section heading level is lowered by one (`##` to `###`).

Ticket: TCK-20261115-PAST-THE-STARVING-LINE-THE-TACTICAL-STEP-TURNS-AWAY-FROM-A-MEAL-WITHOUT-WEIGHING-HUNGER.
- Owner rulings: M1 pace (a), #715 6912138476; memo row 96.
- Design: drafts/rpg-designer-d1-starving-tactical-design.md.
- These counts are fixed BEFORE any data and are never rewritten after. rpg-planner copies this section into the ticket's Acceptance Criteria verbatim.

### What the fix claims
Past the starving line (hunger ≥ `STARVING_LINE`, 95), a last-attacker hit makes the hitter "acting" only while:
- the hitter is within its own reach of the subject (Manhattan distance ≤ max(1, hitter `combat.range`)); or
- term (a), `_task_acts_on`, holds.

Below the line, memo row 88's 10-tick hit window is unchanged. Every caller (`need_yields`, `_panic_holds`, `acting_threat_to`) reads the same predicate.

**v2, after #933.** The hit test is now membership in `subject.combat.last_hit_attackers` (every body in the last hit), not `last_attacker_id`. The D1 rule applies to each member on its own: each hitter in the set acts past the line only while it is within its own reach, or term (a) holds. Here, "the hitter" means the `hostile` of the call, a member of `last_hit_attackers`. The "old rule" means main's post-#933 rule: member, and the hit within 10 ticks.

### Run shape
- Merged main with D1 (the fix arm) only. The counts compare the new predicate with the old rule on the same call, so the own job needs no base arm.
- frontier_marches, crowded_frontier and urban_political, s42, 5000 ticks.
- Each world gets a spied run plus its plain twin (6 processes).
- The spy wraps the hit-acting predicate (the `_hit_acts_on` path, or `hostile_acts_on` if the fix threads the hunger state there) and each of its 3 callers. It records, per call:
  - tick, subject, hitter;
  - the subject's hunger;
  - distance, and the hitter's range;
  - the term (a) value;
  - the ticks since the hit;
  - `last_hit_attackers` (the full set), whether the hostile is a member, and `last_attacker_id`;
  - the returned value.
- The spy prints inputs and the returned value only. I compute the old-rule value myself (hit within 10 ticks means acting) and assign the classes.

### Own-job counts (HARD: any failure is a trip; one trace cycle, then the owner)
- **J1, below the line unchanged.** Calls with hunger < 95 whose returned value differs from the old rule: **0**.
- **J2, in reach still acts.** Calls with hunger ≥ 95, hit within 10 ticks, and the hitter in reach or term (a) true, that return not-acting: **0**.
- **J3, out of reach stops acting.** Calls with hunger ≥ 95, hit within 10 ticks, the hitter out of reach and term (a) false, that return acting: **0**.
- **J4, one predicate.** For the same (tick, subject, hitter), the 3 callers disagree on the value: **0**.
- **J6, group hits per member.** Past the line, in the same call tick for the same subject, a member in reach must act and a member out of reach (with no term (a)) must not. Any call that breaks this is already counted in J2 or J3. J6 reports how many group-hit cases (set size ≥ 2) occurred, with no separate bar.
- **J5, the line is ≥, not >.** Calls at hunger exactly 95 are classed as past the line in J2 and J3. Reported separately, with no separate bar.

### Not vacuous
- J3 needs at least 1 qualifying call over the 3 worlds.
- If there are 0, crowded_frontier s45 and s46 (the V3 cells, cf/45 e5 and cf/46 e4) run on the fix arm, spied plus twin (4 more processes), before I rule.
- If those still give 0, that's a trip: the fix's own case never occurred.

### HARD evidence checks (as always)
- spied == plain twin hash;
- the spy's exceptions and logging_errors are empty;
- spy and runner pinned at the shas I approve;
- no crash or ENOMEM.

### Reported, not blocking (BALANCE)
- A base arm (merged main, plain) on the same 3 cells gives these rows for the PR body. If it isn't run, they're read at the next pooled reading.
  - **r1:** people STARVATION deaths within 3 ticks of an open food way, base vs fix.
  - **r2:** COMBAT/DEFEAT deaths at or past the starving line, base vs fix. A r2 reading past 2× its Tier-1 bar is a FLAGGED owner line, per the amendment.
- The V3 known-red rows for cf/45 and cf/46 close only if the rpg gate shows both subjects no longer starve. Otherwise they stay, owned by D1.
- **The pooled extinction line:** D1 doesn't remove a food or survival path, so it takes the normal every-3-steps reading, not an extra one.

### Simpler option
Rely only on the unit and real-kernel integration tests, with no 5000-tick run.
- Cost: J1 and J4 are proven only on the built fixtures, not across a real world's callers. A caller that re-derives the predicate (J4) would go unseen.

## Related Tickets
- TCK-20261115-THE-GO-TO-TOWN-STEP-RESETS-THE-WALK-TARGET-ON-A-TOWN-TILE (D2)
- TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING (#884, 2.204, where the V3 rows came from)
- TCK-20261111-FELT-LETHAL-MEMORY-HAS-NO-RECENCY-WINDOW (not reopened)

## Related Docs
- docs/world_rules/life-body/survival-needs.md (SURV-07, row 83)
- docs/mechanics/02_combat_laws.md, docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/tactical.py (PANIC_RETREAT sites ~:279/:535; pursuit ~:773; the branch order ~:508)

## Assumptions / Open Questions
- Landing hold: this moves crowded bases, so it doesn't land while HOLD stage 2 is measuring. The night-wrap ticket and D2 have the same hold.
- Dispatch is the owner's yes, through lead, after the designer's design.

## Implementation Notes
- 2026-11-15 (rpg-planner): rpg-designer's design v1 is FINAL, at main-checkout .claude/handover/drafts/rpg-designer-d1-starving-tactical-design.md. Step 0 (owner #715 6893555631; spy f349e5fd; a.json 15fb056c and b.json 4889b9d4, both REPRO_OK) confirmed the hypothesis:
  - A, t2155: e34 at distance 5 still counts as acting only through the hit term, so the subject panics away from an inn 2 ticks off.
  - B, t3226: e36 at distance 2 acts only through the hit term, so need_yields.
- The fix: past STARVING_LINE only, `_hit_acts_on` requires the hitter to still reach the subject (Manhattan <= max(1, hostile.combat.range)). Term (a) is unchanged, and the memo row 88 window below the line is unchanged. It is one predicate shared by need_yields, _panic_holds and acting_threat_to, and adds no new number.
- Dropped from v0: (i), engage only acting hostiles. B's target order comes from the group shared-target bias in TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET (ubuntu), to be re-checked after that lands. The hp<15% branch order stays parked (0 of 8 attack returns were below 15%).
- Docs: Bible 04 LAW P, a Bug Fix divergence cross-referencing 2.135 and row 88, and a ledger row by COMB-346.
- Tests: 5 unit, 1 tactical and 1 real-kernel integration test (listed in the draft).
- Measurement: the paired 3x5 death bar, plus r1 (people starvation within 3 ticks of an open way) and r2 (COMBAT/DEFEAT of past-line subjects). An r2 Tier 1 rise is a STOP to rpg-designer. Then re-read the V3 cells.
- The plan goes to rpg-designer for review before Implement.
- 2026-11-15 (rpg-implementer-3): implemented in commit 0efe62c12 (not pushed): `_hit_acts_on` reach test past STARVING_LINE; 7 unit tests, a 4-test tactical scene with a discriminating old-predicate control, Bible 04, divergence 2.207, ledger STRAT-300. Real-kernel test 7 is open: four kernel fixtures eat on the inn arrival under the old predicate too, so none discriminates (an untracked draft stays out of the commit; rpg-designer decides between the tactical scene and a crowded_frontier raider fixture). Mechanism-registry changed-code advisory (`tactical_decision`, tactical_threat.py): judged by rpg-planner 2026-11-15 as no entry edit needed (its summary and implemented_by, which already lists hostile_acts_on, still hold). Gates (lanes, mypy, health, import-layers, docs checks) and the paired measurement not yet run.

- J4 static (rpg-designer, at f727390f2): `last_hit_tick` is read only in `tactical_threat` (`_hit_acts_on`, `attacked_me_recently`); `felt_swing` reads `last_hit_attackers` for the 2.204 felt-lethal hold, a different meaning.

## Test Summary
- Unit (single process): tests/unit/engine/test_acting_hostile_is_an_act_not_a_state.py 31 passed (7 new; 3 of them fail on the old predicate, the others are controls). tests/unit/tactical/test_starving_hit_left_behind_does_not_hold_a_panic.py 4 passed (raider 24 five tiles behind: no flight reason and the step heads to the inn; adjacent keeps PANIC_RETREAT; below the line keeps it; the old-predicate control returns PANIC_RETREAT).
- Real kernel: tests/integration/observability/test_starving_subject_eats_past_a_hitter_left_behind_through_the_real_kernel.py 2 passed (crowded_frontier s42, starving wounded worker 2 tiles from inn 20003, raider held idle 5 tiles away with the hit re-stamped 3 ticks old each tick, 40 ticks: eats; old predicate monkeypatched in: does not).
- Related existing set 181 passed, no existing test edited; scoped D1 set 141 passed.
- Gates on head 04018e329, one step at a time under a 3500 MB cap, no xdist: mypy_gate PASS; codebase.health PASS (OK: 2 new, 2 worse, 79 improved; the 2 new and 2 worse are report-only jscpd duplicate blocks in src/observability files this change does not touch); pr_body_lint PASS; ci_lanes unit-core-world PASS (3112 passed, 3 skipped), unit-gameplay PASS (1992 passed, 1 skipped), integration PASS (1133 passed, 6 skipped). perf-cert-arena path-filtered, not touched. Not run locally: pyrefly (not installed, advisory), the known local-only failures (ruff Makefile test, http snapshot, simq drift).
- Known gap: not measured yet. The paired measurement (3 worlds x s42-46 x 5000t, rows r1 and r2, V3 cell re-read crowded/45 and /46, rpg_gate_known.yaml) is pending, after HOLD stage 2.

## Files Changed
src/engine/tactical_threat.py; tests/unit/engine/test_acting_hostile_is_an_act_not_a_state.py; tests/unit/tactical/test_starving_hit_left_behind_does_not_hold_a_panic.py; tests/integration/observability/test_starving_subject_eats_past_a_hitter_left_behind_through_the_real_kernel.py; docs/mechanics/04_strategic_cognition.md; docs/guidelines/intentional_divergences.md (2.207); docs/parity_ledger/strategic_cognition.yaml (STRAT-300); this ticket and its staging artifacts.

## Completion Summary
