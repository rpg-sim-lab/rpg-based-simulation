---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261107-A-RESTORED-SCENARIO-CHECKPOINT-DRAWS-FROM-SEED-0
phase: open
date: 2026-11-07
tags: [determinism, bug]
---

# TCK-20261107-A-RESTORED-SCENARIO-CHECKPOINT-DRAWS-FROM-SEED-0

## Title
A restored scenario checkpoint builds its RNG with base seed 0, so for any nonzero seed the resumed run's stateless draws differ from the uninterrupted run

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
The owner asked, via personal-career on 2026-11-07, that this defect be ticketed. It was found in the 2026-11-07 backend review follow-up (row R-eng-03, lead-planner draft `agent-working/lead/review_followups_2026-11-07.md`, Batch 2) and earlier in `docs/plans/architecture/port_leak_audit.md` §3 row 2a, which was never ticketed. Verified at origin/main a7f1bb3df:
- `ScenarioCheckpointer.restore` builds `DeterministicRNG(base_seed=0)` (`src/engine/scenario_checkpoint.py:91`), then calls `rng.set_state(state.rng_checkpoint)`.
- `set_state` restores only the per-domain stream generators, never `_base_seed` (`src/platform/rng.py:57-62`).
- The stateless draws (`get_float`, `get_int` and the rest) seed from `_base_seed` through `_composite_seed`.
- A normal run uses `base_seed=self._initial_state.seed` (`src/engine/scenario_runtime.py:420`).
- So after a restore, every stateless draw uses seed 0 instead of `state.seed`.
- The code comment at `scenario_checkpoint.py:88-90` ("base_seed is irrelevant post-restore") is wrong.
- This contradicts `docs/engine/deterministic_execution.md` ("Checkpoint files": loading and continuing must give the same downstream hash sequence).

## Scope
- Build the restore RNG with `base_seed=state.seed`, and correct the comment.
- Regression test: parametrize the existing `test_checkpoint_restore_determinism` (`tests/integration/scenarios/test_scenario_runtime_service.py:338`) on a nonzero seed. Today its `_make_service()` (`:33`) gives no initial state, so the runtime takes the seed-0 branch (`scenario_runtime.py:421-423`) and the test cannot see the defect. That is how the bug survived.
- Check whether any recorded evidence run resumed from a scenario checkpoint. If one did, name it for a re-check.
- Remove the README's open-defect line (README.md, "Verification and reproducibility") when this lands.

## Out of Scope
- Atomic checkpoint writes (temp file, fsync, `os.replace`) and checking the header `spec_id` before unpickling: the review's F6, also in Batch 2 of the draft. The owning planner decides whether to fold it in.
- A checkpoint format version (`TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION`).
- Pickle safety for untrusted input.

## Acceptance Criteria
- On a nonzero seed, restore at tick N and run to N+k gives the same proof digest at every tick as the unbroken run to N+k.
- The same test fails on origin/main a7f1bb3df (shown before the fix).
- The seed-0 case still passes.

## Related Tickets
- TCK-20261022-ARCHITECTURE-PORT-LEAK-AUDIT (done; recorded it as row 2a, no ticket filed)
- TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION
- TCK-20261107-README-OVERVIEW-AND-VERIFICATION-SCOPE (the README names this defect)

## Related Docs
- docs/engine/deterministic_execution.md
- docs/engine/scenario_runtime_contract.md
- docs/plans/architecture/port_leak_audit.md

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/scenario_checkpoint.py, src/platform/rng.py, src/engine/scenario_runtime.py, tests/integration/scenarios/test_scenario_runtime_service.py

## Assumptions / Open Questions
- The tier is a hotfix suggestion; the owning planner (rpg) may raise it. A determinism fix is unavoidable and is done properly, not disclosed.
- Unverified: whether any shipped flow restores a checkpoint and then compares a hash.

## Implementation Notes
Planner scope (rpg-planner-ubuntu, 2026-11-08; owner dispatch "yes", logged at #715 comment 6720661924):
- Tier stays hotfix. Re-verified at origin/main 297494469: `scenario_checkpoint.py:91` still builds `DeterministicRNG(base_seed=0)`; `set_state` (`rng.py:57-62`) restores only the stream map; `_build_kernel` uses `base_seed=self._initial_state.seed` when there is an initial state (`scenario_runtime.py:419-420`).
- The comment at `scenario_checkpoint.py:88-90` is corrected in the same change (docs-as-review-source batch A item 6). It is wrong twice: base_seed does not match `_build_kernel()` for a nonzero seed, and it is not irrelevant post-restore.
- The regression test must build the service with a nonzero-seed initial state, so the runtime takes the `base_seed=state.seed` branch, and it must show a red on 297494469 first.
- README.md is lead-owned: do not edit it. When this lands, rpg-planner-ubuntu tells lead-planner, who drops the README line.
- Evidence-run check: search recorded evidence for a resume from a scenario checkpoint and name any hit in the Completion Summary. "None found" with the search used is an acceptable result.
- F6 (atomic checkpoint write, spec_id before unpickle) is NOT folded in: no ticket, and a durability change is a separate concern from this determinism fix.

## Test Summary

## Files Changed

## Completion Summary
