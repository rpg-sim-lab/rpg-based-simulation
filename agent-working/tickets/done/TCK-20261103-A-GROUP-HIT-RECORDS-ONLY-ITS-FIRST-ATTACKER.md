---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER
phase: done
date: 2026-11-03
tags: []
---

# TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER

## Title
A simultaneous group hit records only its first attacker, so row 88's act test reads the others as not acting

## Status
DONE

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

2026-11-15 rpg-designer ruling (#634 6883450273, filed as staging rpg_designer_ruling_2026-11-14.md): shape C accepted (`last_hit_attackers: tuple[int, ...]` sharing `last_hit_tick`); felt_swing option (b) with a per-attacker share tuple.
Departure the ruling invited: the share tuple `last_hit_damages` is typed `tuple[int, ...]`, not float, because hp, last_hit_damage and calculate_damage are int, so the shares sum exactly to last_hit_damage (rpg-planner-ubuntu checked combat.py:53 and state.py:417 and is putting it on record with the designer).

### Known gaps (measured, disclosed)
- Long felt-lethal holds on frontier s42, new arm: e36 held 107 ticks from t3754; e12 was held at the last tick. Both are untraced. The one traced, e7 (a2 re-run, spy fb478ec8, #634 6905649093): e7's 56-tick hold: its only felt attacker, e30, stayed engaged (orthogonally adjacent) throughout without targeting it. The free swing runs with is_lethal=False, so stepping away would have ended in a terminal DEFEAT rather than a COMBAT death; the felt estimate was right that stepping away was terminal. e7 died COMBAT at t4222 from e30's hit of 23 against hp 6. These are the existing 2.204 hold reached more often on ticket 2's trajectory; ticket 1 alone is byte-identical to base (a1).
- Urban fight deaths 34 -> 43, mostly seed 45 (people deaths 10 -> 20). Up in 2 of 5 seeds; no Tier 1 trip.
- Worker fight deaths up in every world: frontier 17 -> 25, urban 3 -> 11, crowded 36 -> 39. Untraced. Observed only; they are NOT ticket 2's intent.
- Urban flee episodes 64 -> 233, and perceived-hostile samples 1859 -> 3815.
- Measurement: base 5ba65854c vs new 437160ac3, ghpair Phase 1 PASS (D76 no drift in all 3 worlds), Phase 2 HOLD_STOP at frontier s42 (new 3 qualifying holds vs base 0); rpg-designer #634 6893463789; owner chose land-and-disclose, #715 6906659466. Hot-loop timing is NOT MEASURED (perf pause #715 6556861718).

## Test Summary
Run on merge head (origin/main c9279925b merged), pinned to CPUs 4-5, `-m "not slow"`: tests/architecture, tests/mechanic_scenarios, tests/unit/{ai,engine,movement,perf,progression,strategic,tactical}: 2790 passed, 3 skipped, 1 xfailed, 2 failed (run twice, same result).
- tests/architecture/test_no_name_switches_in_decision_paths.py: 58 passed (now gates src/world and src/core).
- Fail 1: tests/unit/perf/test_benchmark_record.py cpu_affinity case: the test's changed value "4-5" equals the pin used for the run; passes unpinned (67 passed). Environment artefact of the pin.
- Fail 2: tests/unit/tactical/test_low_hp_retreat_gate.py::test_a_held_retreat_does_not_walk_a_stored_target_through_the_kernel: seen before merging main; fixed on main by #932 (TCK-20261116-A-TEST-KERNEL-DOES-NOT-DEGRADE-BECAUSE-AN-EARLIER-TEST-USED-MEMORY); the failing pair passes at this head.
- Code identity: the src/tests diff differs from the measured one (5ba65854c..437160ac3, 5b91a901...) only by the code-health refactor 69c840b1e..750e9a242 (combat.py `_hit_outcome`, patches.py `_hit_attackers_and_damages`), hash-proven neutral (owner #715 6907423637: s42, 5000 ticks, identical final hashes on frontier/urban/crowded). `git diff origin/main <head> -- src tests` = `git diff c9279925b 750e9a242 -- src tests` = bc5169fb826696334aaba3d737df75675f77b53b4b5d7448fe58c8c379f72535.
- Gates at the merged head (origin/main dc2f4c07e): codebase.health check OK; name-switch test plus paths guard plus the batch's tests 131 passed.
Known gap: hot-loop timing NOT MEASURED (perf pause #715 6556861718).
Known gap: tests/unit/perf/test_benchmark_record.py cpu_affinity case fails only under a taskset 4-5 pin (its changed value equals the pin); passes unpinned.

## Files Changed

## Completion Summary
Landed with disclosures (owner #715 6906659466, 'Land, disclose'; rpg-designer #634 6893463789): see Known gaps. Measurement base 5ba65854c vs new 437160ac3: ghpair Phase 1 PASS, Phase 2 HOLD_STOP at frontier s42. Not pushed; push needs an owner ask.
