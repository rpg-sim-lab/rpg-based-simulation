---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER
phase: open
date: 2026-11-03
tags: []
---

# TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER

## Title
A simultaneous group hit records only its first attacker, so row 88's act test reads the others as not acting

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by lane A's unit rows on 2026-11-03, written at rpg-designer's request while ruling the ENG urban s44 deaths. The rows are in a scratch file, not committed. They exercise the real code paths: the subject is a human worker, adjacent goblins have an IDLE task (so only hit test (b) can make them acting), the hit lands at tick 5, and NEED_WAKE_CADENCE is 10.

The writer of `last_attacker_id` and `last_hit_tick` is src/engine/patches.py:330-337. It sets them only when attacker_id is set, damage_taken > 0 and hit_tick_set is set. `hostile_acts_on` (src/engine/tactical_threat.py:141-143) is task test (a) or hit test (b).

`resolve_multi_attack` (src/engine/combat.py:315-410) returns `attacker_id=valid_attackers[0].id` (:403, rpg-planner read it on main). So only the first attacker of a simultaneous group hit is recorded. The second and later attackers, whose swings lowered hp, read as not acting unless their own task still targets the subject. The unit row "second attacker reads True after the hit" fails.

Passing, by the same rows:
- attack (combat.py:146-229);
- opportunity hit (:242-250);
- skill (:252-312);
- area damage, primary and each splash victim (:416-520);
- hazard (world_dynamics.py:104): fields untouched, acting False;
- starvation and passive self-damage (apply.py:123-130): fields untouched, acting False.

This is a defect in row 88's act test (TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE, shared code on main, predating ENG). ENG leans on it hardest. Per rpg-designer, it lands before or with ENG, and ENG re-measures on top. ENG's owner row then gets the line "the act test missed group hits since row 88; fixed in TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER".

Open: whether it explains the s44 victims. They were hit by scout 17 alone as far as the trace shows, so it may not. lane A's re-run of urban s44 on e844 decides, recording the path of each hit.

## Scope
1. Counts: how often multi-attacks land with two or more attackers, per world, on main.
2. Fix shape (rpg-designer, after counts). It probably records every attacker of a group hit for test (b). The typed record holds one last_attacker_id today, so a set or per-attacker tick may need a typed field with checkpoint coverage.
3. Unit rows from the scratch file become real tests, one per hp-lowering path, plus the failing multi-attack row.

## Out of Scope
- Victim 11's execution wait (INSUFFICIENT_READINESS), a separate later question.
- ENG's group-defence option (an owner choice in ENG's row).

## Acceptance Criteria
- Every attacker of a group hit reads as acting at the subject's next decision, within the cadence window.
- Row 88's behaviour is otherwise unchanged; a test pins the single-attacker paths.
- Bible ch.04 and the parity entry for row 88's act test are updated; a divergence entry if the behaviour changes (u24 id block: 2.159, then 2.200-2.249).
- Hot-loop: yes (combat resolution and the act test). Under the perf pause (#715 6556861718), timing is NOT MEASURED; say so at close.

## Related Tickets
- TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE (done)
- TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED (ENG)

## Related Docs
- docs/plans/systemic_world/owner_decision_memo.md row 88; docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- lane A's scratch test file (path in its session scratchpad; to be committed with the fix)

## Related Code Areas
- src/engine/combat.py:315-410, src/engine/patches.py:330-337, src/engine/tactical_threat.py:141-143

## Assumptions / Open Questions
- Dispatch needs an owner yes.

## Implementation Notes
2026-11-03 rpg-designer, two ties for the fix shape:
- The self-defence rider (TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET, lane C, unpushed, `self_defence_rank` via `hostile_hit_subject_within`) reads the same `last_attacker_id`. A group hit would make the rider favour the first hitter and ignore the rest. Whatever the fix, the rider's key and row 88 (b) read the same field, and both get a grid row with a two-attacker group hit.
- A typed per-attacker field is new durable state: it needs the digest (TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ), a checkpoint field rule (append-only; FIELD_RULES derive-or-refuse; restore can't derive it, so it is refused or defaulted per the checkpoint ruling), and parity rows. Prefer a smaller fix if counts allow it: each attacker of a group hit writes last_attacker_id in a fixed order, so the latest wins, as for single hits.

## Test Summary

## Files Changed

## Completion Summary
