---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261116-A-TEST-KERNEL-DOES-NOT-DEGRADE-BECAUSE-AN-EARLIER-TEST-USED-MEMORY
phase: open
date: 2026-11-16
tags: [testing, determinism]
---

# TCK-20261116-A-TEST-KERNEL-DOES-NOT-DEGRADE-BECAUSE-AN-EARLIER-TEST-USED-MEMORY

## Title
A test kernel does not degrade because an earlier test used memory: the lodging test kernel pins its governor

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
rpg-planner-ubuntu reported an order-dependent failure on main c9279925b, relayed by lead-planner-u24 on 2026-11-16.
`tests/unit/tactical/test_low_hp_retreat_gate.py::test_a_held_retreat_does_not_walk_a_stored_target_through_the_kernel` fails at line 177, `assert (1 >= 2)`, "the low-hp hold must have been decided". It fails when it runs after `tests/architecture/test_unwired_subject_check.py::test_the_real_tree_completes_and_the_found_case_is_unwired_with_its_tests` (from #924). It passes when run alone. Under xdist, CI hides it whenever the two tests land on different workers.

Root cause, traced by testing-planner on 2026-11-16 in a scratch worktree at c9279925b:
- `tests/unit/engine/lodging_kernel.kernel()` builds `Kernel(profile(), state, DeterministicRNG(1))` with the default `ResourceGovernor` and no audit_mode. That governor reads the process's live RSS through `src/engine/observability.py` (`psutil`) → `signal_source` → `governor.py:84/109`, and switches to DEGRADED or SURVIVAL against `profile.max_ram_mb`.
- The unwired check parses every `src/` and `tests/` file with `ast`. That raises the process RSS, and the RSS stays high after `gc.collect()` because Python keeps the memory arenas. The next kernel built in that process starts degraded, decides less often, and the test sees 1 decision instead of 2 or more.
- The check is the trigger, not the cause. The unwired scan is AST-only and imports no `src` module, so it leaks no module state.

Evidence (same process, `-p no:xdist -p no:randomly`):
- the real-tree test, then the target: 1 failed;
- a 15 s sleep, then the target: 2 passed, so it is not timing;
- an AST parse of all `src` and `tests` files, then the target: 1 failed, and still 1 failed with `del` plus `gc.collect()`, so it is RSS, not garbage;
- 2M small objects allocated and freed, then the target: 2 passed (too small to cross the threshold);
- `lodging_kernel.kernel()` given `governor=PinnedNormalGovernor()` (from `tests/helpers/kernel_pinning.py`): the parse-then-target pair and the real pair both pass.

## Scope
1. `tests/unit/engine/lodging_kernel.kernel()` passes `governor=PinnedNormalGovernor()`. That is the shared pin for tests that run a real Kernel and must not depend on the host. Nine test files use this helper (`tests/unit/engine/test_*lodg*`, `test_beds_survive_a_checkpoint_restore`, `test_checkpoint_fields`, `test_checkpoint_group_fields`, and `tests/unit/tactical/test_low_hp_retreat_gate`). All of them must still pass.
2. A regression test that needs no heavy run. In one process, raise the signal the governor reads (patch `KernelObservability`'s cached RSS, or the platform signal, above `max_ram_mb`), build `lodging_kernel.kernel()`, and assert that it stays NORMAL and that the low-hp test's decision count is unchanged. The test must fail with the pin removed.
3. Report only, no fixes: list the other test helpers or tests under `tests/` that build a real `Kernel(` with no `governor=` pin and no `audit_mode`, and attach the list to the ticket for a follow-on sweep.

## Out of Scope
- Any `src/` change. The governor reading RSS is production behaviour.
- Changing the unwired check. Lowering its memory would only hide the defect.
- The sweep itself. Scope 3 only lists the candidates.

## Acceptance Criteria
- [ ] AC1: the real-tree unwired test followed by the target passes in one process (`-p no:xdist -p no:randomly`). So does `tests/architecture` plus the target, which was 1 failed / 237 passed before.
- [ ] AC2: the Scope 2 regression test passes with the pin and fails without it, and the Test Summary records that.
- [ ] AC3: the nine files that use `lodging_kernel` pass.
- [ ] AC4: the Scope 3 list is in the ticket.

## Related Tickets
- TCK-20261115-A-NON-SEQUENTIAL-RUN-IS-REFUSED-BY-THE-GATE-CANDIDATE-PAIRED-ARMS-AND-RPG-MEASURE (#924, added the unwired check)

## Related Docs
- `tests/helpers/kernel_pinning.py` (the pin's contract)

## Related Stored Artifacts
None.

## Related Code Areas
- `tests/unit/engine/lodging_kernel.py`
- `src/engine/governor.py`, `src/engine/observability.py`, `src/engine/signal_source.py` (read only)

## Assumptions / Open Questions
- `tests/unit/engine/` and `tests/unit/tactical/` belong to rpg. I'm asking rpg-planner whether it takes this, or whether testing builds it with rpg reviewing (as on #928 and #930). It is a test-only change and behaviour does not change.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
