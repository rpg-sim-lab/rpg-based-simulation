---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261118-CAMPAIGN-RUNNER-AND-RESTORED-BODIES-SKIP-THE-BUILD-TIME-SENSES-CHECK
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-CAMPAIGN-RUNNER-AND-RESTORED-BODIES-SKIP-THE-BUILD-TIME-SENSES-CHECK

## Title
Campaign episode bodies, scenario-runner bodies and checkpoint-restored bodies skip PERC-02a's build-time senses check, so a body of an unprofiled species goes blind with gate ERRORs instead of being refused

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
PERC-02a (#955, main 346c2dc78) makes every body-construction path refuse a species with no usable sense profile, raising a typed SenseProfileError at build time (divergence 2.210, Bible ch. 04, STRAT-352).

On main, require_species_sense_profile (src/content/species_senses.py:24) is reached from three paths:
- worldbuilding/compiler.py:762 (via require_declared_population_species);
- worldassembly/entity_spawner.py;
- entities/archetype_factory.py build_entity (build_risen goes through it).

Three other paths put bodies into a running world with no check:
1. src/domains/campaigns/orchestrator.py:822: campaign episode bodies, built with V2EntityBuilder, kind = cf.kind from campaign content.
2. src/domains/campaigns/runner.py:70: scenario runner bodies, built with V2EntityBuilder, kind = hero_species_id().
3. src/engine/scenario_checkpoint.py ScenarioCheckpoint.restore (lines 56-120): it never compiles and never checks senses. Content can change between save and restore, so a restored body can belong to a species that has since lost its profile.
4. Mid-run spawners (EntityGenerator spawn_*) are split into the sibling P1 ticket TCK-20261118-MID-RUN-SPAWNED-BODIES-SKIP-THE-SENSES-CHECK (rpg-designer: HARD before the Phase-3 measurement).

The effect, inspected on main: no build-time error. At runtime appraisal.perceives() catches the gate's error, logs ERROR and returns not-perceived, so the body is silently blind. This is latent today, because the hero is human and profiled, but campaign content can name any kind.

Found by rpg-planner-ubuntu. Inspected by lead-planner-u24 on 346c2dc78. Sites 1 and 2 were ruled INSIDE the 02a law by rpg-designer: "At build, on every path, the body's sense profile is its species' sense_profile". The words "compile, spawn and archetype" listed the paths known at the time; they were not a limit on the law. rpg-designer added site 3.

## Scope
1. Every production body-construction path in sites 1 and 2 refuses a body of an unprofiled species at build, with the typed SenseProfileError.
   - Prefer ONE shared production helper that the sites call, e.g. a checked-build function in src/entities/ or src/content/, over a separate check at each site.
   - Do NOT put a hook inside V2EntityBuilder itself (rpg-designer). It is a generic builder, and test fixtures that deliberately build bodies of unprofiled kinds would fail for reasons unrelated to the law.
2. Add a restore-time check in ScenarioCheckpoint.restore, after fill_missing_fields(state) and before Kernel(...): every body in the restored state must resolve a usable sense profile for its species under the CURRENT catalog. Otherwise restore refuses with a typed error before any tick. Reuse SenseProfileError, or a typed restore error that wraps it.
3. Add a source-scan test: every non-test V2EntityBuilder(...) construction site under src/ either calls the senses check on its path, or is in a named allowlist with a one-line reason per entry.
4. Docs, in the same change:
   - Bible ch. 04 and divergence 2.210 name all the construction paths, including campaign, scenario runner and restore;
   - the STRAT-352 v2_evidence cites the new tests.

## Out of Scope
- Changing the sense law itself (profiles, signals, night, touch).
- PERC-02b (the perceived_neighbours migration).
- Births: births takes rpg-designer's option (D) with no new src; its disclosure cites this ticket for the restore path.
- The other restore gaps already filed: TCK-20261110-A-RESTORED-SCENARIO-DROPS-ITS-GOVERNOR-AND-EVENT-RECORDER and TCK-20261110-A-RUN-RESTORED-FROM-A-CHECKPOINT-EQUALS-THE-UNINTERRUPTED-RUN-TICK-BY-TICK.

## Acceptance Criteria
- A campaign episode whose content names an unprofiled kind fails at build with SenseProfileError, naming the site. A profiled kind builds exactly as before.
- runner.py:70 fails the same way if hero_species_id() resolves to an unprofiled species, and builds exactly as before for human.
- Restore test: a checkpoint saved under content A and restored under content B, with one body's species profile removed, is REFUSED with the typed error before any tick. A restore under unchanged content succeeds, and its state hash equals the saved state's.
- The source-scan test fails if a new non-test V2EntityBuilder site under src/ neither calls the check nor is allowlisted with a reason.
- No existing test expectation changes. If one must change, that is an owner ask.
- Statics (code-health, lint-imports, mypy filter) and the targeted tests run after every src commit.
- Until this closes, PERC-02a's limits text in docs/engine/known_limitations.md states: "campaign, scenario-runner and checkpoint-restore bodies are not yet checked for a usable sense profile (TCK-20261118-CAMPAIGN-RUNNER-AND-RESTORED-BODIES-SKIP-THE-BUILD-TIME-SENSES-CHECK)". This line is added in the same PR that files this ticket, or in the first PR to touch these sites.

## Related Tickets
- TCK-20261117-EACH-BODY-PERCEIVES-BY-ITS-SPECIES-SENSES-AND-SIGNALS-FOLLOW-THE-BODY (PERC-02a, done in #955)
- TCK-20261109-M1-HONEST-PERCEPTION-DEFAULTS (the parent; PERC-02b follows)
- TCK-20261118-MID-RUN-SPAWNED-BODIES-SKIP-THE-SENSES-CHECK (the sibling: spawners, P1)
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND (births; it cites this ticket for restore)
- TCK-20261110-A-RESTORED-SCENARIO-DROPS-ITS-GOVERNOR-AND-EVENT-RECORDER, TCK-20261110-A-RUN-RESTORED-FROM-A-CHECKPOINT-EQUALS-THE-UNINTERRUPTED-RUN-TICK-BY-TICK (the other restore gaps)

## Related Docs
- docs/mechanics/04_strategic_cognition.md (perception, senses)
- docs/guidelines/intentional_divergences.md 2.210
- docs/parity_ledger/strategic_cognition.yaml STRAT-352
- docs/engine/scenario_runtime_contract.md (checkpoint and restore)
- docs/engine/known_limitations.md

## Related Stored Artifacts
- None.

## Related Code Areas
- src/content/species_senses.py (require_species_sense_profile)
- src/domains/campaigns/orchestrator.py:822, src/domains/campaigns/runner.py:70
- src/engine/scenario_checkpoint.py (ScenarioCheckpoint.restore, fill_missing_fields, Kernel(...))
- src/core/builder.py (V2EntityBuilder, which is NOT edited)

## Durable state, lifecycle and clocks
No new durable state. The check reads the catalog's species sense_profile when a body is built or restored. No record, field or clock is added.

## Assumptions / Open Questions
- Priority P2 for sites 1-3 (rpg-designer): no M1 gate-world body goes through these sites, and no M1 measurement restores. It becomes HARD before any M1 measurement that uses a campaign, the scenario runner or a restore.
- RULED (rpg-designer): restore raises its own typed RestoredBodySenseProfileError(ValueError), with the SenseProfileError as __cause__. The message names the checkpoint path, the entity id and the species, and the test asserts both the type and the cause. Reason: restore callers already handle the CheckpointSchemaError family of ValueErrors, and "the save doesn't match this content" is a checkpoint fact.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
