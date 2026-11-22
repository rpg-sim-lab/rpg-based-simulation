---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261122-A-STARVING-PREDATOR-HAS-NO-FALLBACK-WAY-TO-EAT
phase: open
date: 2026-11-22
tags: []
---

# TCK-20261122-A-STARVING-PREDATOR-HAS-NO-FALLBACK-WAY-TO-EAT

## Title
A starving predator has no fallback way to eat (no carcass, no food node, and its hunt belief says it cannot win)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Exposed by PR #992 (TCK-20261122-A-PREY-MAY-NOT-STRIKE-ITS-PREDATOR-BETWEEN-THE-PREDATORS-BLOWS). #992's gate re-run (dffe0a6e1 vs main 67c65321) shows two NEW unowned V3 rows: wolves starving with HUNT_EAT_RAW and SCAVENGE untried.

| world | seed | entity | kind | tick |
|---|---|---|---|---|
| frontier_living_world | 42 | 47 | wolf | 3553 |
| frontier_living_world | 45 | 49 | wolf | 3969 |

rpg-designer ruled them EXPOSED and pre-existing, not a #992 regression (#715 7081215688; the sealed read at /mnt/data2/rpg-measure/wolfstarve_992_run/, SEAL fd4aae34…). Its evidence (executed, the 4 spy cells):
- The wolves' hunts were NOT refused by permission. s42 wolf 47 against goblin 30: 4 LEGAL and 11 OUT_OF_RANGE. s45 wolf 49: 4 LEGAL and 16 OUT_OF_RANGE. No FRIENDLY_FIRE against the prey.
- The 3 NEW-only FRIENDLY_FIRE rows (s42) are swings at a HUMAN while the HUNT step was closed. They were correctly refused under CONFLICT-03's pair rule. BASE has about 25 such refusals for wolf 49.
- At death, both wolves have hunger 100, hp 1, and EVERY food step closed: FORAGE (no food node with charges), SCAVENGE (no carcass in reach; 0 carcasses), HUNT ("no creature it can eat and believes it can overcome"), EARN / ASK.
- In BASE, the same wolf 49 is at hunger 100 with no ways open at t4069 (hp 39), heading the same way, only slower.
- #992's lawful change (the goblin strikes back: 2-3 hits taken) makes its hp fall faster, so it dies inside the window.

## Scope
1. Read why a starving predator has no fallback: is it the ecology (no carcasses, no meat source), the hunt belief (CONFLICT-03 can_overcome, which the power-judgement seam will host), or the step ladder (no last-resort step for a starving body)?
2. A fix ruled by rpg-designer, kind-neutral and from properties, with mechanic-scenario tests and a failing control.
3. Re-run the gate: the two wolf rows are gone or re-attributed with a cause.

## Out of Scope
- #992's permission rule (correct, owner-accepted).
- Any other V3 row.

## Acceptance Criteria
1. The cause is read (inspected/executed) and named.
2. The fix lands with its tests; the gate re-run shows the 2 rows gone or re-attributed.
3. The scoped known entry for these 2 rows is removed.

## Known entry (testing-planner drafts it)
- It names exactly the 2 rows above and cites this ticket.
- It expires on the EARLIER of this ticket's fix landing or 2026-12-15.
- Separately, #994's entry SHRINKS when #992 lands, to CF/45 goblin 30 only. FLW/42 goblin 30 and FLW/45 human 5 are retired with "no longer occurs after #992 (#715 <id>); the cause ticket stays open".

## Related Tickets
- TCK-20261122-A-PREY-MAY-NOT-STRIKE-ITS-PREDATOR-BETWEEN-THE-PREDATORS-BLOWS (#992, the exposer)
- TCK-20261122-AN-ARENA-OF-PREDATORS-AND-PREY-SHOWS-HOW-ATTACKED-BODIES-REACT
- TCK-20261122-EVERY-CAN-I-WIN-JUDGEMENT-GOES-THROUGH-ONE-POWER-SEAM (the hunt belief's home)
- TCK-20261122-THREE-STARVING-BODIES-DIE-WITH-WAYS-UNTRIED-ONCE-THE-TOWN-HEAL-STOPS-HIDING-THEM

## Related Docs
- docs/world_rules/capability-progression/conflict-combat.md (CONFLICT-03); docs/world_rules/life-body/survival-needs.md (SURV-02, SURV-07)

## Related Stored Artifacts
- /mnt/data2/rpg-measure/wolfstarve_992_run/ (sealed; transit 87849eb3c); #715 7081215688

## Related Code Areas
- src/ai/goals/opening_steps.py (HUNT, SCAVENGE, HUNT_EAT_RAW steps); src/engine/appraisal.py (can_overcome)

## Assumptions / Open Questions
- Whether 0 carcasses is a world-content fact or a lifecycle effect is unknown.

## Durable state, lifecycle and clocks
None.

## Implementation Notes
- The read kit's next version stores the first NON-null DeathRecord, and classifies hunt ends by reason (OUT_OF_RANGE as out of range). Both are disclosed defects of kit ecd6f8d8 (rpg-designer).

## Test Summary

## Files Changed

## Completion Summary
