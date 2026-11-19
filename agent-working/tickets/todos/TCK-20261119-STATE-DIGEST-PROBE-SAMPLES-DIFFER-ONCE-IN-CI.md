---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261119-STATE-DIGEST-PROBE-SAMPLES-DIFFER-ONCE-IN-CI
phase: open
date: 2026-11-19
tags: [determinism]
---

# TCK-20261119-STATE-DIGEST-PROBE-SAMPLES-DIFFER-ONCE-IN-CI

## Title
The state-digest field-coverage test failed once in CI and passed on the same sources elsewhere: build_samples' chest contents may vary in CI

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Filed by rpg-planner-ubuntu on 2026-11-19, routed by lead-planner as a determinism question. Cc: rpg-planner (u24), via lead-planner, because the probe's sample determinism may touch their lanes.

On PR #967 (TCK-20261119-OCCUPATION-READS-COMPARED-WITH-A-NON-LIVING-SPECIES-ID-MISS-THE-WORLD-BOSS), one CI run of `tests/architecture/test_state_digest_covers_every_field.py::test_every_unhashed_field_is_a_reasoned_row_and_every_row_is_still_unhashed` failed at line 156 (`assert check(load_allowlist(), merged) == []`) with exactly one item:

> state.chests[].items[].properties: stale row (no longer a field path); delete it

- **Failing run:** job 135337639021, head a2f23b237, "Architecture / docs / static", CI Python 3.13.12 (uv venv). Result: 1 failed, 553 passed, 3 skipped, 1 deselected, 2 xfailed.
- **Passing runs of the same job:** at 173436661 and at d9c223344, the merge of a2f23b237 with main 5d00cf025. The only change between 173436661 and a2f23b237 is one allowlist line in tests/unit/core/test_occupation_field.py. Neither touches state, chests, items or the probe.
- **Local evidence** (rpg-implementer-ubuntu, clean `git archive` trees of main a30847030, a2f23b237 and main 5d00cf025, local Python 3.13.7):
  - the test file alone: 11 passed on each tree;
  - the whole tests/architecture directory with the CI marker: 245 passed on each tree;
  - CI's one-process command: 553 passed. The 1 failure in that run was a different test (`tests/docs/test_subsystem_ownership_lifecycle_doc.py`), which needs `.git` and so is an artifact of the archive tree;
  - the test file on a2f23b237 under PYTHONHASHSEED 1-8: all passed.
- **What the walk depends on:** the `merged` fixture is `probe.merge([probe.probe_state(s) for _n, s in probe.build_samples()])` (tests/architecture/state_digest_probe.py:331). The path `chests[].items[].properties` exists only when some sampled state holds a chest with an item carrying `properties`. So in the failing run, no sample held one.

No cause is claimed. The open question: are build_samples' states (compiled worlds plus kernel ticks) the same in every environment? If not, the digest test's coverage depends on where it runs.

## Scope
- Find out whether build_samples is deterministic across environments. Compare per-sample chest and item contents (the field-path set of each sample) between a local run and CI, with the same Python patch version if possible.
- If the samples vary: find the source (environment, dependency version, ordering, unseeded randomness) and report it. A determinism defect in the engine path gets its own ticket.
- Make the test's coverage not depend on a run happening to place a chest item with properties. For example, a sample that carries every field path it relies on by construction. This needs a ruling before any change.

## Out of Scope
- Editing the allowlist row to make the test pass. The check's "delete it" advice is not a ruling.
- TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ (digest coverage of decision-read fields). That's related, but a separate question.

## Acceptance Criteria
- A stated answer to whether build_samples' field-path set is identical across local and CI runs, with evidence.
- If it isn't, the source is named, and the test's coverage no longer depends on it, under a recorded ruling.

## Related Tickets
- TCK-20261119-OCCUPATION-READS-COMPARED-WITH-A-NON-LIVING-SPECIES-ID-MISS-THE-WORLD-BOSS (PR #967, where it surfaced)
- TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ

## Related Docs
- docs/engine/kernel.md (determinism)

## Related Stored Artifacts
None yet.

## Related Code Areas
tests/architecture/state_digest_probe.py, tests/architecture/test_state_digest_covers_every_field.py

## Assumptions / Open Questions
- One failure in three runs on equivalent sources. The rate is unknown.
- The Python patch versions differ (3.13.12 in CI vs 3.13.7 locally); this is not shown to matter.
- The local repro trees were /data/vboxuser/h2-repro-trees/{main-a30847030,h2-a2f23b237,main-5d00cf025}; they're on the owner's delete list.

## Durable state, lifecycle and clocks
None: a test-coverage and determinism question. No durable state is added or changed.

## Implementation Notes
Taken by testing-planner on 2026-11-19 (tests/architecture/** is testing's; rpg-planner-ubuntu filed it, lead-planner agreed the re-route). A determinism defect found in the engine path is a separate ticket, routed to rpg-planner.

None yet.

## Test Summary

## Files Changed

## Completion Summary
