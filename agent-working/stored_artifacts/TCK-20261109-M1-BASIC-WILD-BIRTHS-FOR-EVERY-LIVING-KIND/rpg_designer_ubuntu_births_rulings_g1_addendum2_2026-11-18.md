---
status: active
layer: world
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
phase: open
date: 2026-11-18
tags: []
---

# Births rulings G1 addendum 2: Q13 and Q14 (rpg-designer-ubuntu, 2026-11-18)
This amends G1 (0c8ea97d) and addendum 1 (4560ab2a). Where they differ, this file wins. It answers rpg-planner-ubuntu's STOP under A1 case (3), and its Q14.

## Q13. The resolver picks the first match in roster insertion order, not by ascending id: (a), with a wording fix
**Fact** (implementer's test, confirmed by the planner): `resolve_pending_information` (compiler.py:394-397) runs `next()` over `entities.items()`, so it takes the first match in dict insertion order. The campaign roster comes from `persistent_entities`, which `_extract_entity_carry_forwards` fills in `state.entities` iteration order. `persistent_entities.update(...)` (orchestrator.py:261) keeps the positions of keys already present and appends new keys at the end. Nothing sorts the roster. The order is deterministic, because each build is.

**Correction to the record.** Addendum 1 said "ascending id expected", and rpg-designer's ack gave "the order is ascending id" as its reason. Both are inexact. The outcome rpg-designer accepted still holds: a member already in the roster comes before a newborn appended after it. It holds because of the order bodies were added, not because of any id rule.

**Ruling: (a). Leave the resolver unchanged (A1 still applies).**
- Case 3 asserts "first match in roster insertion order", and tests both insertion orders as the implementer wrote them (150 then 99 resolves to 150; 99 then 150 resolves to 99). Add one test for the real flow: a campaign roster built through the carry-forward path, where a t0 member and a newborn of P both survive, resolves to the t0 member.
- Disclosure wording (step report and the field's doc line). This replaces the planner's suggested sentence, because "t0 members are inserted before newborns" is not true across episodes:
  > "In campaign mode, a surviving newborn can receive its population's pending information responses and self-model events in a later episode (`resolve_pending_information`), but only when no member of that population that entered the carried-forward roster before it survives. The resolver takes the first match in roster insertion order, with no id rule. Every t0 body enters the roster before any newborn."
- The planner files a P3 backlog ticket: "resolve_pending_information picks by dict insertion order, not a declared rule". It is for a later decision on an explicit order in the shared resolver. Any change to that order changes the resolver shared with u24, so it is on the pre-bind list for rpg-designer.
- Option (b), sorting the resolver now, is rejected: it is a shared-resolver change, and A1 holds.

## Q14. The "species.yaml schema doc" (v2.2 condition 2): (a), using its fallback
Checked on origin/main. `docs/content/content_pack_format.md` describes pack manifests (`pack.yaml` fields, dependencies, enable/disable). It has no living or species section, so this is the wrong place for species fields. `docs/content/pipeline_contract.md` covers resolver and catalog contracts, not per-field schema. There is no dedicated species schema doc.

**Ruling: the schema doc is these three, all in the same PR:**
1. A `Field(description=...)` on `SpeciesDefinition` for `newborn_archetype` and for `reproduction_profile`. Each says what the field means, whether it is optional, what happens when it is absent, and that it is set only for species with a profile (the v2.2 key condition).
2. The `content_usage_matrix.md` `living/species` row, regenerated (not hand-edited) so it names both fields.
3. One line in the PR body: "species schema doc = SpeciesDefinition Field descriptions + content_usage_matrix row; no dedicated species schema doc exists (content_pack_format.md covers pack manifests only)".

Don't start a new species schema doc in this PR. Ch01's identity-fields text is Bible. It changes only through the B5 Bible batch to rpg-designer, if at all.

This reads rpg-designer's own v2.2 condition, so it goes to rpg-designer as a cc. rpg-designer can override it at the B5 pre-impl review by naming another doc.

## Pre-bind check
- Q13 doesn't change the resolver. It fixes a test assertion and the disclosure wording, and files a backlog ticket, so it is a cc. It also corrects the record of rpg-designer's stated reason.
- Q14 adds no doc under the pre-bind list and no Bible text. It applies rpg-designer's condition, so it is a cc that names the B5 override window.
