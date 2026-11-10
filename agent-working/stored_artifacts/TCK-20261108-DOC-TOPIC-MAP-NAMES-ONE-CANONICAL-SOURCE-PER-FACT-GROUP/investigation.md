---
status: active
layer: architecture
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261108-DOC-TOPIC-MAP-NAMES-ONE-CANONICAL-SOURCE-PER-FACT-GROUP
tags: []
---

# investigation - TCK-20261108-DOC-TOPIC-MAP-NAMES-ONE-CANONICAL-SOURCE-PER-FACT-GROUP

Context scan: `search_docs` ("canonical doc per topic map satellites") returned D25 §1 as the existing map. `graphify query` couldn't run: this worktree has no `graphify-out` link, and the ticket touches docs only. One read-only Explore agent then built candidate rows from headers, frontmatter and grep hits for 30 fact groups, starting from D25's five rows. It did not read full doc bodies.

lead-planner checked the agent's output at 297494469:
- All 37 proposed canonical, satellite and world-rules paths exist.
- Conflict C1 is confirmed: `capability_registry.yaml:30` says "17-phase", and `:35-37` says "6-Phase".
- Conflict C2 is confirmed: `architecture.md:81` says the RNG uses xxhash, and `src/platform/rng.py` has no xxhash.
- Conflict C3 is confirmed in part: `SKILL.md:24` says "The 7 Hard Laws". The counts of 8 and 9 come from the 2026-11-07 audit.
- C4-C6 are reported by the agent and were not re-read.

Findings:
- The `authority:` field (P0/P1/P2) can't tell canonical docs apart, since nearly every doc is P1. Canonical docs were chosen by stated scope.
- Alerts and the watchdog have no contract-level doc.
- Checkpoint and REST/read-model each split into two rows.
