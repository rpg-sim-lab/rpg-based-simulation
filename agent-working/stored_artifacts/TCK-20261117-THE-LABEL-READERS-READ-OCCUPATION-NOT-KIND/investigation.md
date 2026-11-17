---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261117-THE-LABEL-READERS-READ-OCCUPATION-NOT-KIND
phase: done
artifact_type: investigation
date: 2026-11-17
tags: []
---

# Investigation: TCK-20261117-THE-LABEL-READERS-READ-OCCUPATION-NOT-KIND

The inventory (tables A, A2, B) is in the parent's evidence: agent-working/stored_artifacts/TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD/evidence/step1_kind_inventory.md.

Findings while building step 3:
- The rescan of src/certification, src/perf and src/testing found no entity-kind reader; the one non-builder hit (perf/scenarios.py:459) is a building kind.
- The event-extractor characterization pins record every `extract` call of the unit tests; they moved (104, then 32 rows) while the unit-test entity helpers carried only `kind`, and returned to the pinned digests once the helpers carried `occupation`. No real output changed.
- B4 `SPAWN_KIND_CATALOG_FACTION` reads the spawner's label argument, never an entity's kind: no change at step 3.
- The code-health ratchet: creature_territory's complexity ceiling (16) forced a typed accessor; event_shapers' module and `shape` line ceilings rose by 2 and 1 (owner #715 6934602208).
