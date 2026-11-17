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

# rpg-planner (u24): final mechanisms.yaml text for the births PR (copy verbatim)
Source: rpg-planner via lead-planner-u24, 2026-11-18. u24's copy: .claude/handover/drafts/rpg-planner-births-mechanisms-yaml-text.md, sha256 7e2179615235152d (u24's file; this ubuntu transcription is lead-planner's, from the relayed message text).
Replace only <BIRTHS-TICKET> (the births ticket id) and <DATE> ("YYYY-MM-DD", the commit date). YAML indentation matches the surrounding entries.

=== 1. humanoid_reproduction (replace the whole entry) ===
  - id: humanoid_reproduction
    layer: entity
    summary: "Adults pair up and have children, who are born into the world with tracked parents."
    systems: [world]
    depends_on: []
    state: partial
    implemented_by:
      - src/world/births.py::BirthService
      - src/core/spawn_source.py::SpawnSource
    verified:
      instrument: code_trace
      verdict: observed
      date: "<DATE>"
      note: >-
        Re-bound by <BIRTHS-TICKET> (v2.2 Q5): src/world/births.py::BirthService replaces the retired src/world/reproduction_humanoid.py::HumanoidReproductionService, and the ENABLE_REPRODUCTION_HUMANOID_PATH flag is removed, so births run unflagged. Code trace: WorldDynamicsSystem.resolve_dynamics (src/engine/world_dynamics.py) calls BirthService.process_births every cadence.births ticks (30); the world_dynamics phase passes no feature flag and is must_run_every_tick (phase_graph.py). Runtime evidence is the births own-job; this entry stays `partial` until that is recorded. Earlier record (2026-09-30, corpus_run): 0 calls under the retired flag.
        Pairs existing adults into a tracked-parent birth (atlas idea 32). `aging_death`/`succession` are lifecycle exits; `demographic_cohort_cycle` is aggregate.

=== 2. genetics_aptitude (replace summary, state and the verified block; the rest unchanged) ===
  - id: genetics_aptitude
    layer: entity
    summary: "Offspring inherit a blend of their parents' natural aptitudes."
    systems: [progression]
    depends_on: []
    state: partial
    implemented_by: [src/systems/lifecycle_systems/genetics.py::GeneticsSystem]
    verified:
      instrument: code_trace
      verdict: observed
      date: "<DATE>"
      note: >-
        <BIRTHS-TICKET>: no longer gated. Births (src/world/births.py::BirthService, unflagged) give a parent with no genetic profile a fallback from GeneticsSystem.generate_profile_from_seed keyed by (world seed, parent id), and combine the two profiles through V2EntityBuilder.birth_record (src/core/builder.py, GeneticsSystem.combine_profiles). Code trace only; the births own-job is the runtime evidence, so the state is `partial`, not `done`. Effect size on aptitudes is not measured.
        Superseded (2026-09-16, TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION): `gated`, because the only caller then was src/world/reproduction_humanoid.py behind ENABLE_REPRODUCTION_HUMANOID_PATH (default OFF); before that it was mis-registered `orphan`.

=== 3. camp (two edits; the rest unchanged) ===
 (a) Delete this implemented_by line entirely, with its comment:
      - src/systems/world_systems/generator.py::EntityGenerator  # re-bound 2026-10-14: ...
     implemented_by keeps CampState, CampService and CreatureTerritoryService.
 (b) Append this as the LAST line of the camp verified note (same indentation as the note's other lines):
        EntityGenerator binding removed by <BIRTHS-TICKET>: the flag-OFF nest-spread offspring path it served was deleted with the M1 births, and CampService.process_camps calls nothing on its generator argument (D70, 2.125: a camp spawns nothing).

=== Checks for the ubuntu implementer, after the paste ===
- registry validator, mechanism_state_caller_check, mechanism_registry_completeness_check, all -n 1.
- Expected state_caller result: the new ('humanoid_reproduction','gated_without_flag_context') is gone, and ('genetics_aptitude','gated_without_flag_context') leaves the pinned set. That one row removal plus its docstring paragraph is the owner ask in the births batch. No other finding may appear; if one does, STOP and send it to rpg-planner.
- Completeness: deleting reproduction_humanoid.py and adding births.py may move total_targets or bound only by those two files. That's under S8 with attribution; unbound must stay 0. Anything else moving comes to rpg-planner.
- The leftover comments at coming_of_age.py:131 and lifecycle.py:207 (naming the deleted spawn_*_offspring paths) should be fixed in the same PR; code-comment truth, the ubuntu planner's call.
- u24's note: the genetics_aptitude text holds under Q19 (a) or (b), so it doesn't wait on Q19.
