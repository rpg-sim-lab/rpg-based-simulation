---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261030-WORLD-GENERATOR-RESOURCE-TYPE-PICK-FOLLOWS-PYTHONHASHSEED
artifact_type: investigation
date: 2026-11-16
tags: [determinism]
---

# Investigation: resource-type pick follows PYTHONHASHSEED

Re-verified at origin/main db6b4579d (872 commits after the 10-30 STOP). Probe: `/data/vboxuser/Work/b_runs/gen_probe/gen_probe.py` (seeds 12345/0.8, 42/1.0, 7/1.5), run against two clean `git archive` trees of db6b4579d outside the repo (`/data/vboxuser/Work/groups_base/gen_main_tree` and `gen_fix_tree`); the fix tree differs by exactly one token (`list(set(...))` to `sorted(set(...))` at generator.py:220). Raw outputs: `/data/vboxuser/Work/groups_base/gen_out/{main,fix}_hs{0..3}.txt`. No code in this worktree is changed.

## 1. The site
`src/worldgeneration/generator.py:220` still reads `resource_types = list(set(r.resource_type for r in catalog_resources))`; `:226` then does `rng.choice(Domain.WORLD, 0, idx, resource_types, sub_id=0)`. The RNG is seeded; the list it indexes is in hash-seed order. Catalog resource types are plain strings (the probe prints the set order: it differs for hash seeds 0, 1, 2, 3).

## 2. Cross-seed behaviour (measured)
- main, PYTHONHASHSEED 0,1,2,3: four DIFFERENT generated worlds (four distinct digests of the per-node (id, type, count, region) lists).
- fix tree, PYTHONHASHSEED 0,1,2,3: ONE world (identical digest).
- Seed-0 content changes with the fix (main is not the reference, its pick was a hash accident). Nodes whose resource_type differs, main at hash seed 0 versus fix: 16/16 (seed 12345, density 0.8), 19/20 (seed 42, density 1.0), 26/30 (seed 7, density 1.5): the same counts as the 10-30 probe. Node ids, count and region do not change (only the type pick).
- Against main at other hash seeds the fix matches only 0-4 nodes (the hash seeds are just different permutations).

## 3. Pinned-output inventory (tests, tools, fixtures, data that read WorldProceduralGenerator output)
`git grep` over src, tools, tests, data, scripts, registries:
- src: `src/worldgeneration/generator.py` itself only. `src/worldbuilding/cli.py:23,342-370` uses `ProceduralCompositionGenerator` (a different class, no resource pick). No other caller of `WorldProceduralGenerator`: no shipped world, no CLI path, no tool, no API route uses it.
- tests (`tests/unit/worldgeneration/test_generator.py`, the only reader): lines 32, 77, 116, 144, 197, 212, 231, 263, 279 construct the generator. Assertions: world_id/schema/topology (37-40), region `town_center` (43), position bounds (46-47), `len(spec.buildings) == 3` (50), `len(spec.resources) > 0` (51), entity count (52), determinism = two runs IN ONE PROCESS equal (95-98, including content_fingerprint), different seed differs (103), compile readiness and a 5-tick smoke sim (123-126, 172), population formulas (200-242), faction fallback (268), density ceiling (291). NONE asserts a resource TYPE, a fingerprint literal, a state hash literal, or a golden file. Nothing is pinned to hash-seed-dependent content.
- fixtures / data / tools: no file reads the generator's output (no golden worlds, no snapshots).
- Other mentions are not readers: `tests/unit/platform/test_rng_hygiene.py:30` (lists the file for the RNG lint), `tests/unit/tools/test_scenario_lane_paths.py:208` (path list), `tests/unit/tools/test_mechanism_registry_completeness_check.py:308` (comment), `registries/mechanisms.yaml:2790-2811` (states the legacy path "has no production caller and is kept on purpose").
- Docs: `docs/world/generator_contract.md` Step 5 (lines 141-157) describes "resource_type and region are chosen via rng.choice()" without naming the candidate list, and line 212 lists "Resource type and region assignment (step 5)" among the seeded decisions; parity entry `SUBSTRATE-NEW-002` (substrate.yaml:3883+) claims bit-identical output for the same inputs, true within a process, false across processes today.
- `docs/performance/wall_clock_inventory.*` and `codebase/baselines/*` mention generator.py but a `sorted(...)` change moves no line.

## 4. Does ProceduralCompositionGenerator share this code path?
No. It is a separate class in the same file (`generator.py:382+`), selects modules with `random.Random(intent.seed)` in declaration order, and calls neither `WorldProceduralGenerator` nor the resource pick. Its only sets (`claimed` :421, `visited` :518) are used for membership tests, never iterated, so its output does not depend on hash order. The planned change cannot move its output; the test plan proves that with a before/after digest.

## 5. Conclusion
The ruling's plan is sound: one-line `sorted(set(...))`, a subprocess cross-seed test, disclosed before/after counts, divergence 2.145 (free: the divergences file runs 2.144 then 2.146), parity SUBSTRATE-NEW-002 update, generator_contract.md Step 5 sentence. No pinned output exists, so the STOP condition ("any test other than the generator's own tests changes") is not expected to trigger.
