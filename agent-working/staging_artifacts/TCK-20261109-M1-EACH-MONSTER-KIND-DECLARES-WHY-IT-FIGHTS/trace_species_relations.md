---
status: active
layer: combat
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS
date: 2026-11-18
---

# Trace 1: species_relations and the species-hostility step (read at origin/main 51a6516cf)

## When it applies (`src/content_semantics/relation.py`, `project_relation`, step 3.5, lines 225-250)
All four must hold:
- the two faction ids differ (:239);
- the `RelationContext` carries BOTH `source_species` and `target_species` (:240);
- the label so far is on the escalation ladder: None, neutral, threat, intruder or enemy (:222 table, :241). Off-ladder labels (ally, protected, opportunity, ignored, prey) are skipped, fail-closed;
- a `species_relations` entry exists for (source species, target species) (:242-243).

## "Upgrade-only" relative to what
Relative to the label already produced by step 3 (the perspective's projected groups, :166-199, and the faction relationship's hostility axis, :202-223). The step only raises it: hostility "high" lifts any label below enemy to enemy; "medium", "medium_contextual", "high_contextual" and "low_base_contextual" lift a label below threat to threat (:246-249). It never lowers or replaces a label. If it lifts a None label, the legacy fallback (step 4, :252) is skipped.

## Callers that reach it
`project_relation` has four callers: `content_semantics/faction.py:219` (inside `is_hostile_compat`), `world/region_threat_classifier.py:116,127`, `engine/quests.py:134`.
- `is_hostile_compat` reaches `project_relation` only when the source faction has a perspective or a relationship row toward the target (faction.py:208-212). Otherwise it goes to the legacy `is_hostile` (alignment law) and never touches species.
- Only two code sites build a `RelationContext` with species: `engine/hostility.py:67` (`faction_hostile`) and `engine/legality.py:59` (the attack-legality context, with the reverse swap at :265). Of the 17 `RelationContext(` constructions in `src/`, the other 15 carry no species, so the species step is skipped for them.
- **So none of the 13 direct `are_entities_hostile` / `is_hostile_compat` sites reaches the species step** (their contexts have `source_species=None`). The step is live only through `faction_hostile` (the tactical relation) and attack legality. The 13 sites and legality can therefore disagree about the same pair today, which is the divergence TCK-20261107-A-COMBAT-ENGAGE-PROJECT-TARGETS... describes.
- For wild creatures `faction_hostile` returns False before the context is built (hostility.py:63), so wolf, spider and (in a wild faction) troll entries are moot on that path.

## Entries (`data/content/social/species_relations.yaml`, 24 directed)
Every entry has a people-kind (human, elf, dwarf) on one side; none is monster-vs-monster, and none names spirit or slime.
- Monster to human: wolf medium_contextual; goblin high; orc high; troll high; undead high; spider medium_contextual; dragonkin medium_contextual; lizardfolk medium_contextual.
- Human to monster: wolf medium_contextual; goblin high; orc medium_contextual; troll medium_contextual; undead **high**; spider medium_contextual; dragonkin low_base_contextual; lizardfolk low_base_contextual.
- goblin and orc to elf/dwarf high; elf/dwarf to goblin/orc medium_contextual.
- The header calls the matrix 18% coverage: "monster-vs-monster pairs rarely fight each other".

## What it means for M1
- It already contains a species-level "hates the living" for the undead (undead_to_human high, human_to_undead high) and a troll hostile to humans (troll_to_human high). It is a pairwise table, not a reason: a new monster needs an entry per pair, and spirit and slime have none.
- human_to_undead high is the second route (besides the invader verdict) by which people attack undead today. Dropping the invader verdict alone would not stop a human attacking an undead through `faction_hostile` and legality.
- Interaction with the rule: pairs of two people-kinds (goblin, orc, human, elf, dwarf) are people-vs-people and stay under faction semantics; only entries whose source or target is a non-people kind (wolf, spider, troll, undead, dragonkin) collide with declared reasons.

## Q8 (new owner question)
Do declared fight reasons replace the species_relations hostility step for non-people kinds?
- A. Replace for non-people kinds. *Recommended.* The entries naming wolf, spider, troll, undead or dragonkin on either side are removed or ignored by the rule; people-vs-people entries (goblin/orc against human/elf/dwarf) stay. One source for a monster's hostility, and the 13 direct sites and legality stop disagreeing. Cost: hostility toward the undead on the people side then comes from Q5 (the aggressor reading), which must be in place first.
- B. Coexist: declared reasons decide the monster's side, and the species step stays as an upgrade on the people side. Two sources for one fact; the undead "hates the living" would be declared twice. Smallest change to people-side behaviour.
- C. Make species_relations the declaration mechanism for monsters instead of a new field. Reuses a file but the pairwise matrix needs N entries per new kind, has no reason vocabulary, and covers 18% of pairs; spirit and slime would need new rows.
