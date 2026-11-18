---
status: active
layer: combat
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS
date: 2026-11-18
---

# Plan: each monster kind declares why it fights (decision 62)

Tier standard, P1. Phase 1 (this branch) is docs only. Code is dispatched separately after the rule text is accepted.

## Phases

1. **Rule text (now, docs only).** Catalog entry and Bible text, in `rule_text_draft.md` beside this file as exact before/after. Owner questions below. No `src/`, no `data/`.
2. **Code step (after acceptance and dispatch).** Sketch, contingent on answers:
   - A content property on the species (home chosen by Q1), validated at content load (shared check with TCK-20261118-MID-RUN-SPAWNED-BODIES-SKIP-THE-SENSES-CHECK).
   - One extracted hostility module (outside `legality.py`, which is at its ceiling) that all 13 direct `are_entities_hostile` sites route through; the monster branch reads the declared reason, the people branch keeps the faction verdict.
   - `is_wild_creature` replaced by a property read. Species via `species_of()` / `occupation_of()` only. No defaulted `night` or `tick`.
   - Tests per reason; parity ledger and Bible in the same change; divergence 2.107 INTERIM paragraph closed.
3. **Measurement.** Decision-76 floor: 3 worlds x 5 seeds x 5000 ticks per arm plus every world holding an affected known entry. Each heavy run needs lead's GO on #715.

## Owner questions (options and recommendation; the forward design's recommendations are not rulings)

**Q1. Where does a kind declare why it fights?**
- A. A new species field `fight_reasons` (a list from a closed set: hates_living, guards_place, hunts_by_diet). *Recommended:* one place, per kind, validated at load, read generically.
- B. Inside the drive profile (`aggression` target keys). Reuses an existing file but the drive weights are bands for goal pressure, not a closed vocabulary.
- C. Derived from traits (e.g. `undead` trait implies hates the living). Hides the declaration in a name check, which decision 46 forbids.

**Q2. What does "the living" mean for the undead?**
- A. A body-model property `living` (true for flesh bodies; false for `spirit_body`, amorphous). *Recommended:* explicit, content-declared; undead then ignores spirits and slimes.
- B. Any body with a non-empty diet. Simple, but excludes the slime and treats dragonkin and troll as living; same result today, fragile for new kinds.
- C. Every non-undead body. Includes spirits, so undead and spirits fight.

**Q3. What is the place a spirit guards, given territory is out of scope (§12.4)?**
- A. The spirit's home tile: it engages a perceived body within a fixed radius of it, nothing persistent. *Recommended:* no territory record; revisit when places land.
- B. The region it controls (`controlling_faction`). This reads a faction label again.
- C. Defer: spirits fight only back, until M1 item 4 (places from perception and memory) lands.

**Q4. The slime (not named by decision 62): which reason?**
- A. hunts_by_diet with a declared diet (a slime would need a diet; today none). *Recommended*, a content line, no code.
- B. No reason: it fights only when attacked.
- C. Out of scope: no slime archetype exists, so declare nothing now and let the content-load check require a reason of any monster kind that gets one.

**Q5. Does a settlement guard or hero attack a monster on sight once the invader verdict is gone?**
- A. Only defence and appraisal (PREDATION when hungry, fight back). Guards would no longer clear undead. Lowest risk, largest behaviour change.
- B. People regard a body as hostile when its declared reason names them (an undead hates the living, so people treat it as an aggressor). *Recommended:* symmetric with CONFLICT-03, no faction label, keeps the guard behaviour.
- C. Keep faction verdict on the people side (people to monster). Breaks "no monster hostility reads a faction label".

**Q6. Permission to attack (CONFLICT-03 symmetry).**
- A. Permitted both ways whenever either side's declared reason names the other. *Recommended*, extends the symmetry already ruled.
- B. One-way (the monster may attack, the target only defends). Reintroduces the one-way legality CONFLICT-03 removed.

**Q7. Same-faction rule for monsters.** Today a faction never hunts its own members.
- A. Keep, but expressed as same species (no cannibalism in M0, `relation` already does this). *Recommended*.
- B. Drop it for monsters.

## Constraints that bind (from rpg-planner)
Branch from main 51a6516cf+; no defaulted night or tick; species only through `species_of()` / `occupation_of()`; mirror `properties["species_id"]` untouched (step 5 deletes it); lane B overlap files noted in investigation.md; legality.py ceilings; merge only in domain-3 segment after run-1 boundary and step 5.

**Q8. Do declared reasons replace the species_relations hostility step for non-people kinds?** (added after the read in `trace_species_relations.md`)
- A. Replace for non-people kinds; people-vs-people entries stay. *Recommended.* One source; the 13 direct sites and legality stop disagreeing. Needs Q5's aggressor reading first, because human_to_undead is high today.
- B. Coexist (reasons decide the monster side, the species step stays as an upgrade on the people side). Two sources for one fact.
- C. Use species_relations as the declaration mechanism for monsters. A pairwise matrix with 18% coverage, no reason vocabulary, and no rows for spirit and slime.
