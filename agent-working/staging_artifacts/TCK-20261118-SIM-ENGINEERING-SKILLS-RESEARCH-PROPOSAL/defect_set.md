---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL
artifact_type: investigation
tags: [skills, simulation-quality, testing]
---

# Historical defect set (P2)

Source: rpg-designer via the leads, 2026-11-18. Relayed by lead-planner, stored verbatim below. Ids are as rpg-designer logged them. I have not independently re-verified the ticket facts; the planner step in P4 lists which ones the eval needs to re-check against git before use.

---

1. NIGHT CHECK ON RAW world_time (#953)
- Should have caught it: a time-semantics contract (raw tick vs world_time vs derived day phase). None exists, so each reader picked its own clock.
- Missed because: unit fixtures build states at world_time 0 (one phase only), and nothing compared the clocks.
- First sign: REVIEW, while writing the M1 items 2-6 rule text (PERC Q1/Q2a). The urban SOCIAL stop at t551 was first misattributed to night, until the clock arithmetic was done.

2. RESOLVE-BLOCKER RE-CREATED EVERY 80 TICKS (TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION)
- Mechanism: infer_blockers REPLACED the blocker each pass and erased its suppression. There was no lifecycle end, and the timeout was untyped.
- Should have caught it: a durable-record lifecycle checklist (creates, updates, ends, and what survives an update). The durable-state rule says "defined lifecycle", but nothing checks merge vs replace.
- Missed because: tests checked one inference pass, never two in a row.
- First sign: RUN METRIC. The last cooperation_event was stuck near t550, and the trace showed 77/77 ABANDONED with None at age 60.

3. STALEMATE GIVE-UPS (TCK-20261030, F1/F2)
- Mechanism: the way-round count belonged to one stored target, and a one-tile re-target by the task layer reset it (patches.py:297). F1's bounded give-up was then undone by the next re-choose: up to 194 give-ups on one anchor.
- Should have caught it: a tactical/strategic interaction review (does a lower layer's give-up reach the layer that re-chooses?). There is no cross-layer-loop procedure.
- Missed because: each layer's tests passed alone, and the S3 bar measured runs per target, not per pursuit.
- First sign: RUN (a v7 trace of S3 runs on one subject). The own-job exposed the never-exit loop.

4. STALE FAILURE REASON (TCK-20261117-A-NAVIGATION-FAILURE-REASON-IS-NEVER-CLEARED-AND-KEEPS-FEEDING-BLOCKER-INFERENCE)
- Mechanism: last_failure_reason was never cleared. Yield/swap moves wrote failure codes, and the action writers share the field.
- Should have caught it: the lifecycle checklist, plus a "one field, one meaning" check, since step and action outcomes were mixed in one field.
- Missed because: no test asserted the value after a SUCCESSFUL step, and comments falsely claimed "movement is the one writer".
- First sign: REVIEW (the blocker-inference read). The own-job then tripped R1/R3, which exposed the yield/swap defect AND a gap in the designer's own bar (it counted only resolve_move).

5. SUSPENDED PROJECT HELD ITS SLOT FOREVER (#954, N10)
- Mechanism: SUSPENDED had no expiry, and 10-15 of 20 urban subjects sat at the project cap.
- Should have caught it: the lifecycle checklist (every non-terminal state needs an exit).
- Missed because: tests checked the suspend transition, not leaving it.
- First sign: RUN (the urban SOCIAL stall; the cap read showed SUSPENDED at cap). It was first suspected as an effect of the night PR.

6. BIRTHS S9 VACUOUS NEWBORN BRANCH (2000t window vs 2400t gestation)
- Should have caught it: a time-scale sanity step in bar design ("can the case under test occur inside the window?"), checked when the bars are fixed.
- Missed because: the window was fixed before gestation became 2400, and the gate design wasn't re-checked for timing when the model changed.
- First sign: REVIEW of the result (rpg-planner-ubuntu's caveat). The run itself was CLEAR.

Caught by review: 1, 4 (the first defect) and 6. Caught by a run: 2, 3 and 5.

EXTRAS (green tests, with a causal, lifecycle or interaction cause):
- The moved_recently latch was set True and never set False, so 02a's "still" meant "never moved". Caught by planner review.
- A per-tick SOLO cooperation_event fired on unchanged decisions. The event spam skewed SOCIAL's denominator. Caught by reading a run.
- A decaying corpse's non-meat items vanish with no sink, a ch03 conservation breach. Caught by review while designing births risen.
- Perception reads inside ONE decision used different inputs: the hostile set was dated, the prey filter undated. Caught by a failing test after 02a.

rpg-designer's pattern: 4 of the 10 are LIFECYCLE gaps (no clear, no exit, replace vs merge, latch). That makes the strongest case for a binding lifecycle checklist on any new durable field, delivered as a GATE, not as a skill, given the catalog epic's finding.

---

## Planner notes (mine, not rpg-designer's)
- Class counts across the 10 (6 + 4 extras), my reading: lifecycle 5 (2, 4, 5, latch, corpse sink), time/scale 2 (1, 6), cross-layer/interaction 2 (3, perception inputs), measurement/denominator 1 (event spam). Defect 4 is both lifecycle and one-field-one-meaning. Class assignment is mine and open to challenge.
- Note: "Caught by review: 1, 4 (the first defect) and 6" is as relayed; "4 (the first defect)" is ambiguous in the relay. Not resolved here.
- Five of ten were found by review, four by runs, one by a failing test (per the relay's labels).
