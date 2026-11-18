---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261118-BIRTHS-BALANCING-PASS
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-BIRTHS-BALANCING-PASS

## Title
Births need a balancing pass: birth rates, newborn survival, combat deaths, cohort drift and population curves were reported in M1, not tuned

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
This is owner backlog, not M1. Owner direction on the births scope, logged on #715 and relayed by lead-planner on 2026-11-18: "birth is a big field that need well balancing and different from the rest logic ... a yet simple but strong foundation is enough, we will comeback to improve later".

M1 (TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND) ships the foundation only. These must hold for it:
- the HARD set: ECOL-06, W1-W5, K6, K6b, K8, and check 6a if rpg-designer accepts it;
- determinism (twin hash, control match);
- the S9 no-new-never-exit-loop gate;
- no crash.

Everything about balance is reported and disclosed in M1, without re-tuning against own-job data. This ticket collects those questions for one later balancing pass.

## Scope
Rule work comes first, for every item. rpg-designer and rpg-designer-ubuntu decide the bands, then the owner judges outcomes by variety within bands across seeds. The pass then tunes against those bands. Items:
- **Birth rates.** Per-kind birth_chance_per_check and the cooldowns in data/content/living/reproduction_profiles.yaml, read against the M1 own-job birth counts.
- **Newborn survival.** How many newborns live to the end of a run, per kind and world, from the M1 own-job rows.
- **Combat-death rise (M1 own-job check 3).** Births roughly doubled combat deaths in both trace worlds. M1 reports per-capita rates, the killer kind -> victim kind table, a per-seed consistency verdict and mechanism probes. This pass decides whether the rise is a defect or a balance target.
- **Cohort drift (M1 own-job check 6b).** The regional cohort count and live bodies drift apart by design (Bible 05, "Individual-Birth Population-Pressure Nudge"). This pass decides whether any drift needs a bound.
- **Per-kind population curves.** Growth, plateau or decline per kind over a run.
- **Provisional newborn bodies.** A newborn has an adult body until a child body scale exists (TCK-20261117-A-NEWBORN-HAS-AN-ADULT-BODY-UNTIL-A-CHILD-BODY-SCALE-EXISTS). This pass decides how that interacts with balance.
- **Border-crossing births.** births writes the cohort nudge to the mother's region, but a newborn can be placed on a tile in a neighbouring region. rpg-designer (u24) ruled on 2026-11-18 that M1's check 6a counts by the mother's region, and reports the crossings as a BALANCE count with tiles, deferred to this pass. This pass decides whether the nudge should follow the newborn's tile.
- **Regionless births.** births.py writes no cohort nudge when the birth region is None. M1 counts these and discloses "N births in no region added no cohort". This pass decides whether a regionless birth should exist at all (rpg-designer-ubuntu's checks 3-6 ruling, 6a).
- **Decayed bodies lose non-meat items (pre-existing, found 2026-11-18).** `WorldDynamicsSystem._decay_corpses` (src/engine/world_dynamics.py) turns only a corpse's gold into a ground purse, and `_meat_decayed_events` sinks only raw meat. Every other item stack in a decayed corpse leaves the world with no record. It is a pre-existing ch03 conservation defect, with its own P1 ticket: TCK-20261118-A-DECAYING-CORPSE-DESTROYS-EVERY-ITEM-EXCEPT-GOLD-AND-MEAT-WITH-NO-SINK, filed by rpg-planner (u24). It is outside this pass. M1's risen origin does not add the breach. rpg-designer's FINAL Q-R6 ruling is (b): a rising drops every non-meat item stack as a ground item at the corpse tile, through one shared helper that the decay ticket reuses.
- **Deferred undead origins:** TCK-20261118-UNDEAD-RISE-AT-A-GRAVEYARD-PLACE and TCK-20261118-UNDEAD-RAISED-BY-A-DARK-MAGIC-CASTER (owner, "Corpse only now").
- **Births-touching follow-ups, tracked here so they are judged together, each owned by its own ticket:**
  - the per-tick SOLO re-decision (TCK-20261118-A-SUBJECT-WITH-A-STANDING-HELP-NEED-RE-DECIDES-SOLO-EVERY-TICK, rpg-planner);
  - the scorer side (TCK-20261118-QUALITY-SCORES-REWARD-SILENCE-OVER-LATE-ACTIVITY).

## Out of Scope
- Any M1 item, including the M1 HARD set.
- The maturation clock itself (TCK-20261117-A-NEWBORN-NEVER-GROWS-UP-INSIDE-A-RUN-NEEDS-A-MATURATION-CLOCK). It is a related input to this pass, not part of it.
- A non-food birth condition for slime and dragonkin (TCK-20261117-SLIME-AND-DRAGONKIN-NEED-A-NON-FOOD-BIRTH-CONDITION).
- The fixes owned by the follow-up tickets named in Scope.

## Acceptance Criteria
- Each Scope item has a ruled band, or a ruling that it needs none.
- Tuned values land with evidence across seeds, showing variety within the band.
- Mechanics Bible, parity ledger and content docs match the tuned values.

## Related Tickets
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
- TCK-20261117-A-NEWBORN-NEVER-GROWS-UP-INSIDE-A-RUN-NEEDS-A-MATURATION-CLOCK
- TCK-20261117-A-NEWBORN-HAS-AN-ADULT-BODY-UNTIL-A-CHILD-BODY-SCALE-EXISTS
- TCK-20261117-SLIME-AND-DRAGONKIN-NEED-A-NON-FOOD-BIRTH-CONDITION
- TCK-20261118-A-SUBJECT-WITH-A-STANDING-HELP-NEED-RE-DECIDES-SOLO-EVERY-TICK
- TCK-20261118-QUALITY-SCORES-REWARD-SILENCE-OVER-LATE-ACTIVITY

## Related Docs
- docs/mechanics/05_world_evolution.md (Individual-Birth Population-Pressure Nudge)
- docs/mechanics/01_entity_anatomy.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND/rpg_designer_ubuntu_births_checks_3_6_ruling_2026-11-18.md

## Related Code Areas
src/world/births.py, data/content/living/reproduction_profiles.yaml, src/engine/apply_plan.py

## Assumptions / Open Questions
- The M1 own-job rows are the starting evidence. They are not tuned against in M1.

## Implementation Notes
None yet.

## Test Summary

## Files Changed

## Completion Summary
