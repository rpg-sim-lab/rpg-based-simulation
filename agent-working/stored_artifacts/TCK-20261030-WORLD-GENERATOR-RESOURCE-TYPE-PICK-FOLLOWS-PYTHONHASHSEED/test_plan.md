---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261030-WORLD-GENERATOR-RESOURCE-TYPE-PICK-FOLLOWS-PYTHONHASHSEED
artifact_type: test_plan
date: 2026-11-16
tags: [determinism]
---

# Test plan
- New: subprocess cross-seed test (hash seeds 0-3) over three (seed, density) intents; asserts identical resource types per node and identical digest across the four processes. Positive control: the same harness over the pre-fix expression yields at least two distinct digests (4 on main today).
- Existing, must stay green and unchanged: tests/unit/worldgeneration/ (test_generator.py, test_composition_generator.py, test_seed_params.py), tests/integration/worldassembly/test_real_content_world_compositions.py and test_e2e_smoke.py (read ProceduralCompositionGenerator), tests/unit/platform/test_rng_hygiene.py.
- ProceduralCompositionGenerator guard: before/after digest of its generated YAML for seeds 42, 7, 12345 at PYTHONHASHSEED 0 and 1 (outside the repo, scratch script) must be equal.
- Parity and registry: parity_ledger_writer --check on substrate.yaml, make docs-registry, tests/tools/test_generate_registry.py, paths guard.
- All capped (3 GB scope, swap 0, CPUs 4-5, PYTHONHASHSEED set per test); no simulation runs.
