---
status: active
layer: engine
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261118-CAMPAIGN-RUNNER-AND-RESTORED-BODIES-SKIP-THE-BUILD-TIME-SENSES-CHECK
date: 2026-11-19
---

# Plan

1. Build checks at orchestrator and runner via `require_species_sense_profile`.
2. `src/engine/checkpoint_senses.py` plus the call in `ScenarioCheckpointer.restore`.
3. Typed error at catalog load for `sense_profile: null`.
4. Tests (see test_plan.md) and the builder-site source scan.
5. Docs: Bible ch04 line 27, divergence 2.210 items (3) and Verification, STRAT-352 evidence. The known_limitations line is not needed because this change closes the gap.
No existing test expectation changes.
