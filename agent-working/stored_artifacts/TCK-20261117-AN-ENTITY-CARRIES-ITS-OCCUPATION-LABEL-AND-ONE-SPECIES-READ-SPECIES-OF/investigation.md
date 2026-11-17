---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261117-AN-ENTITY-CARRIES-ITS-OCCUPATION-LABEL-AND-ONE-SPECIES-READ-SPECIES-OF
phase: done
artifact_type: investigation
date: 2026-11-17
tags: []
---

# Investigation: TCK-20261117-AN-ENTITY-CARRIES-ITS-OCCUPATION-LABEL-AND-ONE-SPECIES-READ-SPECIES-OF

The per-reader inventory of every entity-kind reader and the table of kind-keyed constants are in the parent ticket's evidence: agent-working/stored_artifacts/TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD/evidence/step1_kind_inventory.md.

Findings made while building step 2:
- `ApplyPath._fast_replace_identity` (src/engine/apply.py) builds the next identity record slot by slot with `object.__new__`; without the new slot the first tick that hashed an entity raised AttributeError. Found by tests/architecture (state-digest probe).
- The step-1 scan excluded src/certification, src/perf and src/testing; the writer-list test found 25 more `V2EntityBuilder(...).kind(...)` chains there (18, 6 and 1). The designer's ruling (a) added `occupation` to each. Re-running the scan over those directories (readers and writers) is recorded for step 4.
- `to_readonly` builds the identity by hand too and had to carry the field.
- The campaign survivor rebuild and the archetype copies are the carry sites of step-1 finding 1; the archetype copies already pass `identity` whole.
- The CI-equivalent run found a mypy no-any-return in `species_of` and a stale docs registry; both fixed.
