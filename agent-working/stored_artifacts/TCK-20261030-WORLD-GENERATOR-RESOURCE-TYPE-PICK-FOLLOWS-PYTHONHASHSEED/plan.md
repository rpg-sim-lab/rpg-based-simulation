---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261030-WORLD-GENERATOR-RESOURCE-TYPE-PICK-FOLLOWS-PYTHONHASHSEED
artifact_type: plan
date: 2026-11-16
tags: [determinism]
---

# Plan
The governing text is `rpg_planner_ruling_2026-10-30.md` (word for word), whose Scope/AC replace the ticket's hotfix Scope/AC.
1. generator.py:220 `sorted(set(...))` (string ids; stable key = the id itself).
2. Test `tests/unit/worldgeneration/test_generator_hash_seed_independence.py`: subprocess per PYTHONHASHSEED 0-3, same seed and intent, assert identical per-node resource types and an identical digest; a positive control that runs the same comparison against a copy of the pre-fix expression and shows it differs (so the test can fail on main).
3. Before/after disclosure: main at hash seed 0 versus fix, 16/16, 19/20, 26/30 nodes differ (main is not the reference).
4. Divergence 2.145 (Stabilized, ubuntu block): states plainly that no shipped world or CLI path uses this generator (cli.py uses ProceduralCompositionGenerator), so no world content changes; Verification = the new test.
5. Parity: update SUBSTRATE-NEW-002 (same-process claim becomes cross-process) through a precise line edit, evidence adds the new test.
6. docs/world/generator_contract.md Step 5: one sentence that the candidate list is sorted by resource type id.
7. STOP and report if any test outside the generator's own changes, or if ProceduralCompositionGenerator's output moves (checked by a before/after digest of its output for 3 seeds at hash seeds 0 and 1).
8. Capped runs (3G scope, swap 0, CPUs 4-5), no simulation runs. Standard closure, commit, no push.
