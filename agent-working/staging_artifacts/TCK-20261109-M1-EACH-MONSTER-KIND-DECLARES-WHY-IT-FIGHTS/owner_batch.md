---
status: active
layer: combat
authority: P2
audience: agent
artifact_type: owner_batch
ticket_id: TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS
date: 2026-11-18
---

# Owner batch: why each monster kind fights (decision 62)

Eight questions for the owner. Options are quoted exactly as `plan.md` words them, with the recommended option moved first (letters are plan.md's, so they do not run in order). Under each is rpg-designer (u24)'s view, word for word from its phase 1 review (matched by description, not by letter). The owner decides; neither recommendation is a ruling. Draft rule text: `rule_text_draft.md`. Investigation and traces: `investigation.md`, `trace_species_relations.md`, `trace_camp_troll.md`.

**Two things the owner should know before answering**
- **Coupling (T2):** people-kind follows an economy trait (keeps_coin_and_trades), so the combat law is coupled to that trait.
- **Current inconsistency:** today the 13 direct faction sites and attack legality can disagree about the same pair, because only hostility.py:67 and legality.py:59/:265 pass species into project_relation.

**Q1. Where does a kind declare why it fights?**
- A. A new species field `fight_reasons` (a list from a closed set: hates_living, guards_place, hunts_by_diet). *Recommended:* one place, per kind, validated at load, read generically.
- B. Inside the drive profile (`aggression` target keys). Reuses an existing file but the drive weights are bands for goal pressure, not a closed vocabulary.
- C. Derived from traits (e.g. `undead` trait implies hates the living). Hides the declaration in a name check, which decision 46 forbids.

rpg-designer (u24) view: A species `fight_reasons` field, closed set, validated at load. [match to plan.md, implementer's note: option A]

---

**Q2. What does "the living" mean for the undead?**
- A. A body-model property `living` (true for flesh bodies; false for `spirit_body`, amorphous). *Recommended:* explicit, content-declared; undead then ignores spirits and slimes.
- B. Any body with a non-empty diet. Simple, but excludes the slime and treats dragonkin and troll as living; same result today, fragile for new kinds.
- C. Every non-undead body. Includes spirits, so undead and spirits fight.

rpg-designer (u24) view: A body-model `living` property, REQUIRED, no default. "Non-undead = living" is false for spirits, slimes etc. [match to plan.md, implementer's note: option A, and rejects option C]

---

**Q3. What is the place a spirit guards, given territory is out of scope (§12.4)?**
- A. The spirit's home tile: it engages a perceived body, not of its own species, within a reach declared per species in content, of its home tile. The home tile is set at spawn and never changes; nothing else persists. *Recommended:* no territory record; revisit when places land.
- B. The region it controls (`controlling_faction`). This reads a faction label again.
- C. Defer: spirits fight only back, until M1 item 4 (places from perception and memory) lands.

rpg-designer (u24) view: Home tile + declared reach, revisited when places land. [match to plan.md, implementer's note: option A]

---

**Q4. The slime (not named by decision 62): which reason?**
- A. hunts_by_diet with a declared diet (a slime would need a diet; today none). *Recommended*, a content line, no code.
- B. No reason: it fights only when attacked.
- C. Out of scope: no slime archetype exists, so declare nothing now and let the content-load check require a reason of any monster kind that gets one.

rpg-designer (u24) view: Declare NOTHING now. No slime archetype exists, and under CONFLICT-05's default a slime with no declared reason fights only back. [match to plan.md, implementer's note: option C, not the recommended A]

---

**Q5. Does a settlement guard or hero attack a monster on sight once the invader verdict is gone?**
- B. People regard a body as hostile when its declared reason names them (an undead hates the living, so people treat it as an aggressor). *Recommended:* symmetric with CONFLICT-03, no faction label, keeps the guard behaviour.
- A. Only defence and appraisal (PREDATION when hungry, fight back). Guards would no longer clear undead. Lowest risk, largest behaviour change.
- C. Keep faction verdict on the people side (people to monster). Breaks "no monster hostility reads a faction label".

rpg-designer (u24) view: A people-kind regards a body as an aggressor when THAT BODY's declared reason names it (the aggressor reading), so guards keep clearing undead with no label. Not "defence+appraisal only" (the largest unmeasured change), and not the faction-verdict option. [match to plan.md, implementer's note: option B]

---

**Q6. Permission to attack (CONFLICT-03 symmetry).**
- A. Permitted both ways whenever either side's declared reason names the other. *Recommended*, extends the symmetry already ruled.
- B. One-way (the monster may attack, the target only defends). Reintroduces the one-way legality CONFLICT-03 removed.

rpg-designer (u24) view: Symmetric, extending CONFLICT-03. [match to plan.md, implementer's note: option A]

---

**Q7. Same-faction rule for monsters.** Today a faction never hunts its own members.
- A. Keep, but expressed as same species (no cannibalism in M0, `relation` already does this). *Recommended*.
- B. Drop it for monsters.

rpg-designer (u24) view: Same species is never a target. [match to plan.md, implementer's note: option A]

Where M0 states it: it does not state it as a rule. The only statement is the code comment at `src/engine/hostility.py:88` ("a kind regards its own as neither prey nor danger (no cannibalism in M0)"), and the behaviour is `relation` (`hostility.py:87-88`) returning NONE for the same species. So the wording is "as relation does today".

---

**Q8. Do declared reasons replace the species_relations hostility step for non-people kinds?** (added after the read in `trace_species_relations.md`)
- A. Replace for non-people kinds; people-vs-people entries stay. *Recommended.* One source; the 13 direct sites and legality stop disagreeing. Needs Q5's aggressor reading first, because human_to_undead is high today.
- B. Coexist (reasons decide the monster side, the species step stays as an upgrade on the people side). Two sources for one fact.
- C. Use species_relations as the declaration mechanism for monsters. A pairwise matrix with 18% coverage, no reason vocabulary, and no rows for spirit and slime.

rpg-designer (u24) view: REPLACE, stated as a rule. For any pair where EITHER side is a non-people kind, the declared reason is the ONLY hostility source. species_relations keeps people-people pairs only; a load-time check refuses an entry naming a non-people kind; and the existing monster entries are removed in the same change, each listed in the ticket with its current effect. [match to plan.md, implementer's note: option A]

---

