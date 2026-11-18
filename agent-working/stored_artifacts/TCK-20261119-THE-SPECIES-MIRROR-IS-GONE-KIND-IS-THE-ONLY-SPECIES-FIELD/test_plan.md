---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261119-THE-SPECIES-MIRROR-IS-GONE-KIND-IS-THE-ONLY-SPECIES-FIELD
artifact_type: test_plan
tags: []
---

# Test plan
- K12 static AST test `tests/unit/core/test_species_mirror_is_gone.py` plus the `unprofiled_need_counts` stub tests.
- 93-file regression (every test mentioning `species_id`, the mirror-touching files and the targeted families), one gated pytest per file.
- Statics: `make code-health`, `make lint-imports`, `make typecheck-py`.
- Measurement (S9): K11 projection and the unprofiled-needs probe, 3 gate worlds, s42, 5000 ticks; preflight on both trees first.
