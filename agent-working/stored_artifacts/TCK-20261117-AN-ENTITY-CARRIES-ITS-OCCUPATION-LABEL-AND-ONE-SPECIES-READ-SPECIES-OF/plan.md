---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261117-AN-ENTITY-CARRIES-ITS-OCCUPATION-LABEL-AND-ONE-SPECIES-READ-SPECIES-OF
phase: done
artifact_type: plan
date: 2026-11-17
tags: []
---

# Plan: TCK-20261117-AN-ENTITY-CARRIES-ITS-OCCUPATION-LABEL-AND-ONE-SPECIES-READ-SPECIES-OF

Step 2 of TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD. Sources: the base ruling 67cc6f6d (staged plan and own-job counts), the step-1 rulings 665b9718, the step-2 review 39dcca3d and ruling (a) for the scenario fixtures; all copied verbatim in the parent ticket.

1. Add `IdentityComponent.occupation` last, None omitted from the canonical dict, with a FIELD_RULES row naming `IdentityComponent` (fill None).
2. Write it on every path as the exact string written to `kind`: compiler, archetype factory, legacy spawner, generator spawners (hero, monster, natural and humanoid offspring, magical entity, goblin), campaign runner, survivor rebuild (carried), and the 25 fixture chains.
3. Carry it in the sites that copy identity by hand: `ApplyPath._fast_replace_identity`, `to_readonly`, the campaign carry-forward.
4. Show it in the presenter beside `kind`; add `species_of` (one module, functions only).
5. Docs (Bible 01, ID-02, entities.md) and parity row SUB-402; move the two pins (FIELD_RULES set, mechanism scope counts).
6. Prove it neutral: K1 over 3 worlds (owner GO 6921470279); K2 per-writer tests; K3 static reader test.
