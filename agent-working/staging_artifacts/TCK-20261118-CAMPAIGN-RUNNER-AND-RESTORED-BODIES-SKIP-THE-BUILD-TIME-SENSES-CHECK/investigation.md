---
status: active
layer: engine
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261118-CAMPAIGN-RUNNER-AND-RESTORED-BODIES-SKIP-THE-BUILD-TIME-SENSES-CHECK
date: 2026-11-19
---

# Investigation: senses check on campaign, runner and restore paths

- `require_species_sense_profile` (src/content/species_senses.py:24) is already the one shared helper. The compile (via `require_declared_population_species`), spawn and archetype paths call it. A second wrapper would only add indirection, so the new sites call it directly. `V2EntityBuilder` is not hooked (rpg-designer).
- Campaign orchestrator survivor rebuild (`_build_initial_state`, orchestrator.py ~:809): one check per carry-forward, before `V2EntityBuilder(eid).kind(cf.kind)`.
- Scenario runner (runner.py:70): one check per hero before the builder.
- Restore: `ScenarioCheckpointer.restore` after `fill_missing_fields` and `check_group_counter`, before `Kernel(...)`. New module src/engine/checkpoint_senses.py with `RestoredBodySenseProfileError(ValueError)`; the message names the checkpoint path, entity id and species; `__cause__` is the `SenseProfileError`. A species not in content is refused too (the helper's rule).
- Null profile: a species record with `sense_profile: null` failed schema validation inside `CatalogRepository.load_all` (non-strict), was dropped silently, and a later lookup died with a bare `KeyError: 'wolf'`. Now raised as `SenseProfileError` naming the species when the key is present and null (a missing key keeps the old schema path, so partial test fixtures are unchanged).
- Note for the planner: a body whose species is not in content (test fixtures) is refused at the three new sites, as at the existing ones. No existing test hit this.
- Source scan: 5 files are checked, 5 are allowlisted with a reason (certification/scenarios, testing/scenario_runner, readiness/harness, perf/scenarios, systems/world_systems/generator, the last owned by the mid-run sibling ticket). `src/world/systems/generator.py` is untouched.
