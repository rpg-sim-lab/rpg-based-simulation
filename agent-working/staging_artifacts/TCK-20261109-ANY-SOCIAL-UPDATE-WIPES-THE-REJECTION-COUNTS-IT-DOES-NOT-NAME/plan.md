---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME
artifact_type: plan
phase: inprogress
date: 2026-11-11
tags: []
---

# Plan

1. `relationships.py`: build `new_rejection = dict(social.rejection_count)`, add each `update.rejection_increment` entry to it, and pass that to `replace`. Keying unchanged. One local variable, no new state.
2. `updates.py` `SocialUpdate.merge`: sum `rejection_increment` per key (a small local dict built like the neighbouring `new_combat_loss`). This field only.
3. Tests (new file `tests/unit/social/test_rejection_counts_kept.py`): a trust-only update leaves counts intact; an increment for A leaves B; a merge of two same-tick rejections from one offerer gives 2; two offerers stay separate; a `to_canonical_dict` round trip; one appraisal row where the fatigue penalty reads the kept count (a count of 3 kept across a trust-only update still cancels a fair-pay offer).
4. Parity: add SOC-280 in `docs/parity_ledger/social_narrative.yaml` citing the new test, with the lifetime-count disclosure. A divergence entry (u24 block 2.200-2.249, 2.203 next unless taken) only if the measurement moves anything.
5. Light checks first: `tests/unit/social` and `tests/unit/core` at -n 1, `mypy_gate`, `codebase.health check`. If the ratchet fails, stop and report; no reshaping.
6. Measurement: not yet. rpg-planner relays the cell set and HOST FREE. Base cells are fresh on main 5c6990e51; both arms run with a read-only counting spy that the designer approves at its sha before any run.
7. Close: hot-loop timing NOT MEASURED (perf pause); hand-close record; the `record_review.py` call for the A ticket (`--review-ref 862#6784371939`) rides this PR.
