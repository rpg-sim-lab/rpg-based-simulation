---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261109-DISTRIBUTED-WORKERS-DESIGN
artifact_type: test_plan
---

# Test plan — TCK-20261109-DISTRIBUTED-WORKERS-DESIGN

**Reconstructed at close from design §8-§8a; no tests run (doc deliverable).** This file was written on 2026-11-16, when the
ticket closed. It was not written as pre-work.

## This ticket
The deliverable is a design doc, so this ticket ran no tests and added none. Verification was review only:
- ubuntu review 2/2 and its re-check;
- the owner's acceptance (#715 6777076537);
- `tools/validate_frontmatter.py` on the doc.

## The strategy it hands to later children (design §8, §8a)
- Equivalence follows the existing pattern: `tests/unit/kernel/test_executor_context_parity.py` (#837) covers the new manager as
  a third packet consumer, and the long equivalence test pattern is `tests/integration/kernel/test_executor_equivalence_long.py`.
  The claim is an identical final hash under `PROOF_DIGEST_SCHEME` plus the `TICK_END` trail, against `LocalSequentialExecutor`.
- Behaviour evidence stays on the pinned sequential runner. Child 6 refuses anything else.
- Lanes: the PR lane under the medium budget; a sibling extra_slow file, each slow test signed off by testing-planner under 540 s;
  child 4's smoke run is opt-in.
- These belong to children 3 and 4, which are shelved (#715 6917359910). Child 3's re-cut as R3 revises them.
