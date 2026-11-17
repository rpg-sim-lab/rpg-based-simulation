---
status: active
layer: world
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
phase: open
date: 2026-11-17
tags: []
---

# Births: rpg-designer answers to rpg-designer-ubuntu (draft 52ad1ea5), 2026-11-17
Ticket: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND. Scope: #715 6950284219.
Facts checked on origin/main: all three reproduction paths are default OFF (feature_flags.py:174, 181, 192 ENABLE_REPRODUCTION_*), and so is creature territory (:148). So no default run has births today. EntityRole = HERO, SHOPKEEPER, MONSTER, CITIZEN, WORKER, GUARD. The ecology catalog ends at ECOL-05.

## Part A: pre-bind check
Part A touches my pre-bind list in two places. Everything else binds as written.
- Q5, newborn identity (a shared identity contract, run 4): AMENDED. faction = the mother's faction. identity.role = MONSTER if the mother's role is MONSTER, else CITIZEN. Inheriting SHOPKEEPER, GUARD or WORKER would give a child a job role, and role still drives behaviour branches until the run-4 retirement; occupation stays None (3045e98a). It is listed as an interim row of the name-branch/hero-role retirement item.
- Q3, reproduction_cooldowns (an existing durable field gets a new meaning): ALLOWED with conditions. Expired entries are pruned at the check, so the map stays bounded. The field's doc and comment state its new meaning (the birth interval). A FIELD_RULES row is needed only if its shape changes (it doesn't).
- Q5, code removal: agreed. All paths are default OFF, so no default run moves. The flag entries leave feature_flags.py and docs/guides/feature_flags.md in the same PR, and I review that file.
- Q10: own-job is the FIX arm (spied) plus its plain twin only. No base arm in Phase 1 (owner 6936893143); the base comparison comes at Phase 3. Five seeds is fine on the ubuntu host.

## Part B
B1. Rule ID ECOL-06, "A new body is born, not made" (Domain Rule, docs/world_rules/life-body/ecology-population.md):
> After world creation, a new living body enters the world only as a birth from two alive ADULT parents of the same species_of(), or as a declared arrival (a typed spawn source named in content or a calamity). A birth happens only when the mother's own hunger is at or better than her species' fed line, a mate of her species is within the species' mate radius, both parents are past their birth interval, and the seeded draw keyed by (world seed, tick, mother id) succeeds at the births cadence. The mother pays the birth in food. The newborn is a CHILD of the parents' species with no occupation, eats by the same hunger law as every other member of its kind, and is fed by no one in M1. A species that declares no reproduction profile has no births. Births come from one system under this one rule.
Evidence/test paths: the own-job bars W1-W5, K6, K6b and K8. The rate values are content (reproduction_profiles.yaml), each with its stated source.
B2. Rec (a) binds for the code (it is a content statement: no profile = no births, so the code doesn't wait). But the exclusion list goes to the OWNER as a confirm, option (c)-lite. Undead and spirit are plainly not living. Slime and dragonkin arguably are, and "every living kind" is the owner's own wording. Ask: "Births in M1 only for kinds that eat (decision 67). Excluded: undead, spirit, slime, dragonkin; their numbers only fall and they come only from world creation. OK, or give slime/dragonkin a non-food birth condition now?" Rec: OK, with a backlog ticket for slime/dragonkin.
B3. NO EXEMPTION. Every kind stays in the extinction line as recorded (owner kept it, 6919222181). On main, no kind has births (all paths are OFF), so a no-births kind starts the same in base and fix. If it goes extinct in the fix where the base kept it alive, the births step caused that indirectly (more predators, more competition for food), which is exactly what the line exists to catch. The undead decline is disclosed as BALANCE text, never as an exemption. In Phase 1 the extinction line is the host read at the domain boundary (fallback a, 6937306315); births is run 5.
B4. Agreed. ECOL-03 keeps statistical cohorts in M1, and the real-birth +1 nudge generalises to every birth from the one system. The evidence text changes in the PR I review. ECOL-03's status line says "partly met: births feed the aggregate; deaths and cohorts stay statistical until M2".
B5. Agreed. Bible ch05 (ecology) gets the births law. The reproduction parity rows move. One divergence entry, class Unified, names the one births system, the child faction/role rule (as amended above), the nest-spread retirement and the removal of the three OFF paths. All texts come to me before the implementation PR.

## Part C: bars
APPROVED as fixed, with four sharpenings (fixed now, before any data):
- W1: add "each entity is a parent in at most one birth per check".
- W3: the declared-arrival list is a typed set of spawn sources, written into the spy before the run and never judged after.
- W4: "worsened by exactly min(birth_hunger_cost, the room left to the hunger bound)", so a clamped mother is not a false fail.
- W5: "eat action" = the typed eat/consume event by the newborn. Any other path that improves a newborn's hunger counts as a W5 fail and is named in the row.
K6, K6b and K8 stay unchanged; I own them. The HARD evidence list is as stated.
