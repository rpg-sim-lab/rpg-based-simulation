---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261007-EPIC-DECISION-CORE-LIVE-MOTIVATION-AND-HONEST-FIGHT-OR-FLEE-INPUTS
phase: done
date: 2026-10-07
tags: [simulation-quality, combat]
---

# TCK-20261007-EPIC-DECISION-CORE-LIVE-MOTIVATION-AND-HONEST-FIGHT-OR-FLEE-INPUTS

## Title
Decision core: make motivation live for compiled characters, make biology follow each kind's needs, and give fight-or-flee honest inputs (Tier 1 of the owner's layer-by-frequency ranking)

## Status
DONE

## Disposition
SUPERSEDED

## Disposition Rationale
Closed by the owner's ruling #715 6875278006 (owner, via lead-planner-u24; audit asked under #715 6875225978): "Move 2/4/5 to M1 (Recommended)".

- Done children: 1 `TCK-20260921-BIOLOGICAL-PRESSURE-ACCUMULATION-UNIFORM-ACROSS-ENTITIES` (`0647a2eeb` #402, `0a03c2448` #407); 3 `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` (`3a9f93c33` #412); `TCK-20261007-SAFETY-DISPOSITION-TRIGGERS-RETREAT-ON-SIGHT-AGENCY-07` (`d9fc65e8c` #398).
- Moved under `TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC`, re-scoped at dispatch:
  - child 2 `TCK-20261007-COMPILED-ENTITIES-GET-DEFAULT-NEED-AND-DRIVE-PROFILES-WITH-VISIBLE-PROVENANCE` reads species and occupation, not role (`TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD`; MONSTER drive with `TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS`);
  - child 4 `TCK-20260913-NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER` and child 5 `TCK-20260915-COMBAT-RISK-EVALUATION-ACCEPTABLE-AT-3X-MISMATCH` are measured in `TCK-20261109-M1-COARSE-PROPERTY-BANDS-AND-THE-APPRAISAL`.
- **Dropped by the owner: child 2's role-based drive defaults** (WORKER/GUARD/HERO/SHOPKEEPER → drive), since milestone 1 retires role as a kind (decision 63). The epic's remaining ACs are carried by milestone 1, not met here.

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
On 2026-10-07 the owner ranked RPG work by LAYER × FREQUENCY, relayed by world-rule-catalog-design: low-layer mechanisms that run for every entity every tick come first. This epic is Tier 1. Dispatch belongs to rpg-feature-planning.

Measured by Lane A on main `f8f1b69fd` (read-only, seed 42, all 24 corpus worlds compiled at tick 0):
- **666 of 666 compiled entities carry no need or drive profile.** `MotivationPressureResolver` returns `no_profile` for every one of them, so the safety, territory and duty pressures read by `tactical.py` are always 0. Profile ids are set only by the archetype resolver (`src/worldassembly/resolver.py:1163-1164`); `WorldCompiler` never sets them. Campaign (archetype-spawned) entities do carry profiles.
- **Biological needs accumulate identically for every entity** (`src/engine/apply.py:90-91`: constants, no per-entity or per-species term). At t=500 every survivor in frontier_living_world is at exactly hunger 50.0, and nobody has eaten or slept. Undead and elementals, whose catalog hunger is `none`, get hungry too. The starvation line (`apply.py:100`, 95) is reached around t≈950 by everyone together. Whether that becomes synchronised starvation is being measured, and it may be the root of the behavioral_5k alive collapse.
- Only `tactical.py` reads the pressure set. Five of its eight dimensions have no reader at all.

Rules, decided by world-rule-catalog-design under the owner's delegation on 2026-10-07 (memo row 22, catalog SURV-05 and AGENCY-08, docs PR pending):
- **NEED** comes from the species' catalog need_profile. A person with no species falls back to humanoid_survival. A non-person with no species is a content defect: report it, don't guess.
- **DRIVE** comes from the most specific DECLARED source: (a) an archetype matching the (species, role) pair; (b) the civil role (WORKER→cautious_commoner, GUARD and HERO→disciplined_protector, SHOPKEEPER→profit_seeker); (c) for MONSTER, a per-species default drive DECLARED in content and never computed.
- **Defaults are visible:** a typed provenance per profile (explicit, defaulted:species, defaulted:role, defaulted:species_drive, defaulted:person_fallback).
- **Biology follows the kind's need profile (SURV-05):** a kind whose catalog hunger is `none` never becomes hungry, and accumulation rates differ wherever the profiles differ.
- AGENCY-07 (#398) already makes flight need a present threat.

## Scope
Children, in dispatch order:
1. `TCK-20260921-BIOLOGICAL-PRESSURE-ACCUMULATION-UNIFORM-ACROSS-ENTITIES`: re-scoped to SURV-05, owner Lane B (body). It becomes a row-7 hard bug if synchronised starvation is confirmed. Before/after on one tree.
2. `TCK-20261007-COMPILED-ENTITIES-GET-DEFAULT-NEED-AND-DRIVE-PROFILES-WITH-VISIBLE-PROVENANCE`: owner Lane A. Compile-path defaults, per-species default_drive declarations in content, and typed provenance. Before/after on one tree, because 615+ entities go from pressure 0 to real pressure and that moves the AGENCY-07 gate and the territory/duty sort (`tactical.py:459-463`).
3. `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY`, owner Lane B.
4. `TCK-20260913-NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER`, owner Lane A.
5. `TCK-20260915-COMBAT-RISK-EVALUATION-ACCEPTABLE-AT-3X-MISMATCH`, owner Lane A.
Done: `TCK-20261007-SAFETY-DISPOSITION-TRIGGERS-RETREAT-ON-SIGHT-AGENCY-07` (`d9fc65e8c` #398).

## Out of Scope
- Wiring the five pressure dimensions that have no reader (hunger, wealth, curiosity, aggression, purpose). Under SURV-04 they stay inert bookkeeping until a consumer exists.
- Tier 2 (one stat model, body recovery, XP threshold) and Tier 3.
- Tuning thresholds (parked by owner decision 7).

## Acceptance Criteria
- [ ] Every compiled entity across the 24 corpus worlds has need and drive profiles with typed provenance, and the coverage report shows explicit vs defaulted counts.
- [ ] Biological accumulation follows the need profile: no hunger for `none` kinds, rates differ by profile, and no synchronised starvation.
- [ ] Each child's behaviour change is measured before and after on one tree and recorded as a divergence entry.
- [ ] Fight-or-flee reads non-empty region enemy data and a per-kind danger record, and the 3x-mismatch risk case is resolved.

## Related Tickets
- `TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS` (its xfail may flip as these land)
- `TCK-20261006-BEHAVIORAL-5K-REGRESSION-URBAN-POLITICAL-DRIFTED-FROM-THE-2026-08-19-BASELINE-ATTRIBUTE-EACH-METRIC`
- `TCK-20260918-MOTIVATION-DOCTRINE-STALE-AGAINST-RETIRED-DOCTRINE-VALUES-CHAIN` (Child B, `domains/motivation`)

## Related Docs
- `docs/plans/systemic_world/owner_decision_memo.md` rows 21-22; catalog AGENCY-06, AGENCY-07, AGENCY-08, SURV-04, SURV-05

## Related Stored Artifacts

## Related Code Areas
`src/world/motivation/pressure_resolver.py`, `src/engine/apply.py`, `src/engine/tactical.py`, `src/engine/tactical_threat.py`, `src/worldbuilding/compiler.py`, `src/worldassembly/`, `data/content/living/`

## Assumptions / Open Questions

## Implementation Notes

## Test Summary

## Files Changed
none — decision-only

## Completion Summary
Closed SUPERSEDED on 2026-11-14 by rpg-planner under #715 6875278006 (owner, via lead-planner-u24; audit asked under #715 6875225978). See Disposition Rationale.
