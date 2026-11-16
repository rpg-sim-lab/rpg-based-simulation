---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261030-WORLD-GENERATOR-RESOURCE-TYPE-PICK-FOLLOWS-PYTHONHASHSEED
phase: done
date: 2026-10-30
tags: [determinism]
---

# TCK-20261030-WORLD-GENERATOR-RESOURCE-TYPE-PICK-FOLLOWS-PYTHONHASHSEED

## Title
The intent-driven world generator picks each node's resource type with the RNG from a list built by list(set(...)), so the generated world depends on PYTHONHASHSEED. Sort the list.

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
**2026-10-30: re-tiered STANDARD after the STOP.** Seed-0 content changes with the fix (16/16, 19/20, 26/30 nodes). There are no pinned outputs, and the generator has no production caller. rpg-planner's ruling, relayed via lead-planner-u24 and lead-planner, is word for word in `agent-working/staging_artifacts/TCK-20261030-WORLD-GENERATOR-RESOURCE-TYPE-PICK-FOLLOWS-PYTHONHASHSEED/rpg_planner_ruling_2026-10-30.md`. Its Scope/AC replace the hotfix Scope/AC below wherever they differ. Dispatch needs the owner's standard-dispatch go; write no fix code until then.

Found by the (B) audit of TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED (item 5e, investigation at 16f7eb1f1). `src/worldgeneration/generator.py:220` builds `resource_types = list(set(r.resource_type ...))` and then calls `rng.choice(..., resource_types, ...)` per node. The RNG is seeded, but the list it indexes is in hash-seed order. So the same seed and catalog give different generated worlds across processes. This affects the intent-driven `WorldGenerator` path only, not the declarative worlds in `data/worlds`.

rpg-planner ruled on 2026-10-30 (ruling 3, Q2, in `TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED/rpg_planner_ruling_2026-10-29.md`): this goes in a SEPARATE ticket, P2, in the ubuntu queue, not in B.

## Scope
1. First step: list every pinned generator output, meaning snapshots, golden worlds and content assertions that read `WorldGenerator` output, with file:line. Grep tests/ and tools/ for `WorldGenerator`, `generator.generate` and fixtures built from it.
2. Change the site to `sorted(set(...))` with a stable key (the resource type id string, or `.value` if it is an Enum).
3. STOP before any re-pin (rpg-planner's plan-OK condition, 2026-10-30) and report to rpg-planner-ubuntu if either:
   - step 1 finds ANY pinned generator output; or
   - seed-0 generated content changes (a different resource pick under PYTHONHASHSEED=0). Compare the per-node resource types for a fixed seed and intent on main and on the fix, both at PYTHONHASHSEED=0.
   A content change in a generated world is a world-content change. The ticket then becomes STANDARD with a divergence entry. If nothing is pinned and seed 0 is unchanged, it stays a hotfix.
4. Add a test: generate the same seed and intent in subprocesses at PYTHONHASHSEED 0 and 1, and assert identical resource types per node. Positive control: the comparison fails on main.

## Out of Scope
- data/worlds declarative assembly.
- Any other set-order site (those are TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED).

## Acceptance Criteria
1. The pinned-output inventory is in Implementation Notes, before any code change.
2. The generator site iterates a sorted, stable-key list.
3. The cross-seed test passes, and its positive control is shown.
4. The seed-0 comparison (main against the fix, PYTHONHASHSEED=0) is recorded: unchanged, or a STOP.
5. Scoped tests pass (`tests/` for worldgeneration, `-m "not slow"`), and generate_registry --check and paths-guard pass.

## Related Tickets
- TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED (B; the audit that found it)
- TCK-20261029-EVENT-EMIT-ORDER-FOLLOWS-PYTHONHASHSEED (A, #790)

## Related Docs
- docs/engine/kernel.md (determinism)
- docs/mechanics/06_worldbuilding_foundation.md

## Related Stored Artifacts
- agent-working/staging_artifacts/TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED/rpg_planner_ruling_2026-10-29.md (ruling 3, Q2)

## Related Code Areas
- src/worldgeneration/generator.py

## Assumptions / Open Questions
- Originally a hotfix dispatched under S4. It STOPPED on Scope 3 (seed-0 content changes) and was re-tiered STANDARD per rpg-planner's ruling. Owner standard-DISPATCH GO: #715 comment 6525127552, sequenced after TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED and the SimQ re-anchor work.
- It queues behind the corpus hotfix and B on rpg-implementer-ubuntu.

## Implementation Notes
2026-11-16 (rpg-implementer-ubuntu), re-verified at origin/main db6b4579d, before any code change; full detail in staging_artifacts/<ticket>/investigation.md.
- Pinned-output inventory: no test, fixture, tool or data file pins a generated resource type or a hash-seed-dependent value. The only reader is tests/unit/worldgeneration/test_generator.py (lines 32-291); its determinism test (95-98) compares two runs inside one process. No caller in src other than the class itself; cli.py uses ProceduralCompositionGenerator.
- Seed-0 comparison (main at PYTHONHASHSEED=0 versus the sorted(set) fix): resource_type differs at 16/16 nodes (seed 12345, density 0.8), 19/20 (seed 42, density 1.0), 26/30 (seed 7, density 1.5); ids, counts and regions do not change. Main gives four different worlds at hash seeds 0-3; the fix gives one. Main is not the reference (its pick was a hash accident).
- The 10-30 stash (471ef6fe6, rpg-impl-ubuntu-generator-hold-20261031) holds only an older copy of this ticket with an empty Implementation Notes section; its seed-0 counts above are reproduced here from /data/vboxuser/Work/b_runs/gen_probe/ and a fresh run.
- ProceduralCompositionGenerator shares no code path with the pick (separate class; its sets are membership-only).

## Test Summary
Capped (3 GB scope, swap 0, CPUs 4-5), no simulation runs. New test: tests/unit/worldgeneration/test_generator_hash_seed_independence.py (a subprocess per PYTHONHASHSEED 0-3 over three intents; identical per-node resource types and identical resource lists; a control that the old list(set(...)) order of this catalog really varies across the four seeds).
- Positive control, the unchanged new test file against a `git archive` of main db6b4579d (outside the repo): 2 failed, 1 passed. Both cross-seed tests fail: PYTHONHASHSEED 1 picks different resource types than 0 (intent 12345/0.8: res_node_0 crystal_shard vs silver_ore, res_node_2 venom_sac vs frost_shard, and more); the four seeds give four different digests. The in-test control passes there (the catalog's candidate-set order varies). On the fix: 3 passed.
- Every catalog resource_type is a str (checked: 16 resources, 14 distinct types, all str), so the sort key is the value itself.
- Scoped run on the fix: tests/unit/worldgeneration, tests/unit/platform/test_rng_hygiene.py, the three parity ledger tests, tests/tools/test_generate_registry.py, tests/tools/test_agent_working_paths_guard.py, tests/integration/worldassembly/test_real_content_world_compositions.py and test_e2e_smoke.py (both read ProceduralCompositionGenerator), `-m "not slow"`: 197 passed, 1 failed before registry regeneration (test_generate_registry drift, expected until `make docs-registry`); re-run after regeneration below. No test outside tests/unit/worldgeneration/ changed or newly fails.
- Before/after disclosed (main at PYTHONHASHSEED=0 vs the fix): resource_type differs at 16/16, 19/20, 26/30 nodes (seeds 12345/d0.8, 42/d1.0, 7/d1.5); ids, counts and regions unchanged; main is not the reference.
- ProceduralCompositionGenerator unmoved: sha256 of its full output (world.yaml, provenance manifest, assembly and validation reports; timestamps normalised) for seeds 42, 7, 12345 at PYTHONHASHSEED 0 and 1 is identical on main and on the fix (e.g. hs0: 7 029602a0f4200646, 42 91241e2a1ec5d24c, 12345 2e742a4850c954e7; hs1: 7 0b49c928bc64cacf, 42 d2684c646858ead8, 12345 0a5e2767ff0b117f). Script /data/vboxuser/Work/groups_base/comp_digest.py.
- parity_ledger_writer.py --check docs/parity_ledger/substrate.yaml: exit 0; `git diff --stat` of that file: 2 insertions, 2 deletions (SUBSTRATE-NEW-002 text and v2_evidence lines).
Known gap: ProceduralCompositionGenerator's resolved/assembly_report.json and validation_report.json list their warnings in a different order at different hash seeds (its world.yaml and provenance manifest do not vary). Not this change and not fixed here; worth its own ticket.
Known gap: no shipped world or CLI path uses WorldProceduralGenerator, so no sim run is affected; hot-loop timing is not applicable.

## Files Changed
src/worldgeneration/generator.py (line 220); tests/unit/worldgeneration/test_generator_hash_seed_independence.py (new); docs/guidelines/intentional_divergences.md (2.145 and its table row); docs/parity_ledger/substrate.yaml (SUBSTRATE-NEW-002); docs/world/generator_contract.md (Step 5 sentence); ticket and staging artifacts.

## Completion Summary
WorldProceduralGenerator's resource-type candidates are now `sorted(set(...))`, so the same seed and intent give the same generated resources in every process (divergence 2.145, Stabilized). It is a legacy generator with no shipped world or CLI user, so no world content changes; the seed-0 content did change (16/16, 19/20, 26/30 nodes), as the ruling anticipated. The draw count is unchanged (same list length, same rng.choice call). Per rpg-planner-ubuntu's plan-OK of 2026-11-16 (ruling 2026-10-30). Not pushed; push needs an owner ask.
