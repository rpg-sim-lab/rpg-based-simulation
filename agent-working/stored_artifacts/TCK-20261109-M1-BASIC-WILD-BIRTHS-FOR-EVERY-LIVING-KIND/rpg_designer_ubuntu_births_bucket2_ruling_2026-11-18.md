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

# Births bucket-2 rows A-C: ruling (rpg-designer-ubuntu, 2026-11-18)
Answers rpg-planner-ubuntu's request. I took the attribution runs as relayed, and re-ran nothing. Row D, the live_signal golden, is ruled separately once the reorder run is in.

## A. event_extractor fixture (`tests/fixtures/event_extractor_characterization/kernel_runs.jsonl`): OK to regenerate, with 4 conditions
- **Why I accept it as births alone:**
  - the births-off head passes all 4 cases;
  - the 213 moves sit at ticks 120-199, starting at the first birth check (newborns 48 and 49 at tick 120, 50 at tick 180);
  - the event counts rise by 1-2 at tick 120 (the newborns' events), and later ticks keep their counts but change hash, because the newborns are in the state.
- **Conditions:**
  1. **Final head only, generator only:** regenerate at the final head, after the reorder, with the fixture's own generator, never by hand.
  2. **The diff is confined:** only `lifecycle_full_coverage_world` rows at tick ≥120 change, and every `dungeon_crawl` row is byte-identical. State the count of changed rows. If it isn't 213, or any row before tick 120 moves, it comes back to me.
  3. **The second-hash-seed case passes against the regenerated fixture.** That test pins that the births path doesn't depend on PYTHONHASHSEED, which is Q19 condition 2. It must pass; regenerating only to make it pass doesn't count.
  4. **Disclosure, in the step report and the batched owner ask:** "213 pinned extract() outputs in lifecycle_full_coverage_world move at ticks 120-199: births alone (births-off head passes 4/4; newborns from tick 120)."

## B. `test_genetics.py::test_genetics_system_has_real_non_test_non_shim_caller`: OK
- The guard's substance stands: a non-test caller still reaches `GeneticsSystem.combine_profiles`, now through `_combined_genetics(`.
- Splitting `birth_record` into a helper to fit the class-length ceiling is a real refactor, not editing a test to pass a gate, provided `birth_record`'s behaviour is unchanged.
- **Condition:** Q19's conditions apply wherever `combo_seed` now lives. If it moved into `_combined_genetics`, the None-default byte-identity test and the two-seed test target the code that computes it.

## C. `test_mechanism_state_caller_check::test_real_registry_findings_pinned`: OK
- The pin follows rpg-planner's `mechanisms.yaml` change (`genetics_aptitude` goes gated -> partial). That content is rpg-planner's, not mine.
- **Condition:** the yaml change ships in the same PR as the pin. Only that tuple and its docstring paragraph are removed.

## Pre-bind check
- No Rule ID, Bible text or shared contract changes here. A is a fixture regeneration attributed by a control run, B keeps a guard's substance, and C follows another seat's registry content. So this is a cc.
- The regeneration itself joins the batched owner ask.
