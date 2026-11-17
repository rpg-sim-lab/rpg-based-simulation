---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261117-THE-LABEL-READERS-READ-OCCUPATION-NOT-KIND
phase: done
artifact_type: plan
date: 2026-11-17
tags: []
---

# Plan: TCK-20261117-THE-LABEL-READERS-READ-OCCUPATION-NOT-KIND

Step 3 of TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD. Sources: the rulings 67cc6f6d and 665b9718 and the designer's step-3 answers, all copied verbatim in the parent ticket.

1. Rescan src/certification, src/perf and src/testing for readers (none found; accepted).
2. Add `occupation_of(entity)` (duck-typed, no kind fallback) to src/core/species.py.
3. Move each label compare to `occupation` with the same literal: party roles, calamity hero, extraction/combat and event_shapers hero, the goblin_raider compares, the boss label set, the spawn-cadence label set, world_boss (navigation, boss, threat), dragonkin (boss), stronghold (environment), the territory-rate lookup; rename the two label sets (a name only) and their import sites.
4. Leave the species rows (evolution, reproduction), the display rows, the plumbing and B4 (the spawn-kind catalog table) on `kind`.
5. Add the K5 static test; add `occupation` to the fixtures that reach a moved reader.
6. Prove it IDENTICAL: K4 over 3 worlds (owner GO 6934624460).
