---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED
phase: open
date: 2026-10-27
tags: []
---

# TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED

## Title
Strategic winner lookup takes the first project of the kind in dict order (often a dead record), so the live SUSPENDED sibling is never resumed, a duplicate is created over the cap and the trim evicts the entity's own suspended project

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by the HUNGER step A capacity-refusal confirm runs (2026-10-27; data
`/mnt/data/scratch-rpg-implementer/stepA/confirm/{R,base}_{42,43}.json`, probe `stepA/confirm_probe.py`,
dump `stepA/proj_dump.py`). Ruled a base defect, its own ticket and its own measured step after step A
(rpg-designer, 2026-10-27).

`src/systems/strategic_systems/intelligence.py:1610` (at 358f4cb7f / 3533fde71):
`existing = next((p for p in strat.projects.values() if p.kind == best_candidate.kind), None)` matches a
project of ANY status and takes the first in dict order. Observed on frontier_living_world, base arm:
- s42 t530 guard 11: first match `proj_combat_engage_129` COMPLETED; s43 t326 scout 15: first match
  `proj_combat_engage_5` ABANDONED.
- `:1612` resumes only when that first match is SUSPENDED, so it does not resume, although 3 SUSPENDED
  combat_engage projects sit later in the dict.
- `:1773` `not existing` is False, so the capacity gate is skipped; `evaluate_project_switch` creates a new
  ACTIVE engage (4 live of max 3).
- `CapacityEnforcementPhase` (`src/engine/pipeline_phases/capacity_enforcement.py` ~103,
  `live_projects_in_the_trim`) then evicts the entity's own oldest SUSPENDED engage (`_449` / `_185`).

Already disclosed (Bible 04 line ~229): "a goal whose kind already has a stored record, of any status, passes
the capacity gate exactly as before". NOT disclosed: the dead-first lookup that blocks resume of the live
sibling, the duplicate over the cap, and the self-eviction.

## Scope
1. The winner lookup resumes the live record of the kind first: a SUSPENDED project of the kind wins over any
   dead (COMPLETED/ABANDONED) record, independent of dict order. Deterministic choice when several live
   records of the kind exist (state the rule, e.g. newest `created_tick`, and test it).
2. Decide, with rpg-designer, whether a kind with ONLY dead records still bypasses the capacity gate. Designer
   lean: no, a dead record is not a reason to pass (then only escalated needs (2.137) pass a full cap).
3. Bible `docs/mechanics/04_strategic_cognition.md` capacity paragraph: rewrite the "of any status" sentence
   to the new rule; update divergences 2.77 and 2.137 (and add a new divergence entry, Bug Fix); parity
   ledger entries for the capacity gate in `strategic_cognition.yaml`.
4. Tests: dead-first-in-dict with a SUSPENDED sibling resumes the sibling (no new project, no eviction);
   the dead-only case per decision 2; escalated need unchanged.
5. Measured step: `tools/rpg_measure` paired run against the step-A-landed base, 3 worlds x s42-46 x 5000t.
   This changes base behaviour for every project kind.

## Out of Scope
- HUNGER step A and its flight. The COMBAT_RETREAT escalated-need exemption is designed but rides with the
  held flight step (rpg-designer 2026-10-27 ruling (ii)), not here.
- Pruning finished records from `StrategicComponent.projects`.

## Acceptance Criteria
1. With a dead record of the kind first in dict order and a SUSPENDED one later, the winner resumes the
   SUSPENDED one; no project is created; `CapacityEnforcementPhase` evicts nothing for it.
2. The dead-only rule matches the decision recorded in the ticket, with a test.
3. Bible 04, divergences 2.77/2.137 plus the new entry, and the parity ledger agree with the code.
4. Paired run reported with the per-kind and extinction lines; any STOP goes to rpg-planner before landing.
5. Mechanism registry check run; `strategic_intelligence_core` entry reviewed.

## Related Tickets
- TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START (2.77)
- TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY (2.137)
- HUNGER step A (`rpg-hunger-retreat-step-a`), which found it

## Related Docs
- docs/mechanics/04_strategic_cognition.md (capacity paragraph)
- docs/guidelines/intentional_divergences.md §2.77, §2.137

## Related Stored Artifacts
- none

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (~1610-1612, ~1773)
- src/core/strategic.py (is_live_project, has_project_capacity, live_projects_in_the_trim)
- src/engine/pipeline_phases/capacity_enforcement.py

## Assumptions / Open Questions
- Not M1-blocking unless it shows in the M1 gate (rpg-designer). Dispatch after step A lands.
- **rpg-designer ruling, 2026-10-28 (decisions 1-3, binding):**
  - Decision 2: NO. "Existing" means a LIVE record of the kind; dead records (COMPLETED/ABANDONED) take no part in
    the lookup or the gate (2.77 "finished records never count"). At a full cap only `escalated_need_wins` (2.137)
    admits a new project.
  - Lookup, stated as behaviour (dict order plays no part anywhere): (1) the current project is of the kind ->
    continue it (no new project, no switch); (2) else the newest live record of the kind by `created_tick`, a
    non-current ACTIVE over SUSPENDED if that state can exist (investigator says whether it can) -> resume it;
    (3) else no live record -> a new project through the cap gate.
  - Decision 3, report BEFORE code: kind-only matching can resume a suspended record whose TARGET differs from the
    winning candidate's (combat_engage on hostile X vs candidate Y; a different harvest node). Designer lean: resume
    only when the live record's target matches the candidate's (`target_entity_id` / `target_id`); a different target
    is a new project through the gate (refused at a full cap; the tactical pass still handles the adjacent fight).
    Count on the confirm seeds (frontier s42 to t531, s43 to t326) how often the resumed record's target differs; if
    common, the numbers go to rpg-designer before the plan is approved.
  - No owner row, on condition: the paired step measures it, and any STOP goes to the owner as step A's did.
- **Records required:** new divergence entry or amendment of 2.77 (rationale Bug Fix); Bible 04 ~l.229 sentence
  rewritten (diff to rpg-designer, who OKs or drafts); parity entry.
- **Measured report must list per-kind capacity-refusal counts, base vs new** (below-onset hunger/sleep,
  combat_engage, harvest at a full cap are now refused where base admitted them: the behaviour shift to watch).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
