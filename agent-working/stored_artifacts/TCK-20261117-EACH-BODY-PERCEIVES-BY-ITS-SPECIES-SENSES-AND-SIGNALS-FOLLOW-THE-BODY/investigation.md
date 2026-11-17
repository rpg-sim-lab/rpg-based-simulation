---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261117-EACH-BODY-PERCEIVES-BY-ITS-SPECIES-SENSES-AND-SIGNALS-FOLLOW-THE-BODY
artifact_type: investigation
---

# Investigation — TCK-20261117-EACH-BODY-PERCEIVES-BY-ITS-SPECIES-SENSES-AND-SIGNALS-FOLLOW-THE-BODY

## Findings (origin/main bb26e4e5f + item 1)
- Compiled and corpus bodies never got `identity.properties["sense_profile_id"]` (only ArchetypeEntityFactory wrote it), so the gate fell back silently to the baseline humanoid profile on every compiled world.
- Species already declare a sense_profile in data/content/living/species.yaml; the archetype resolver (content/resolver.py:478) always takes the archetype's profile from its species, and no archetype yaml declares another: NO content finding.
- get_entity_signals returned fixed defaults from properties keys nobody set; no signal followed the body.
- There is no PerceptionComponent; the designer ruled DERIVE AT READ (no stored field, no FIELD_RULES row, no #942 change).
- Gate failure was treated as perception (appraisal.perceives, tactical._target_still_perceived returned True).
- Known: legality.attack_allowed, is_feeding_kill, scorers_support.perceived_hostiles and the other get_neighbor_view sites stay day-by-default until 02b.
