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

1. New pure function `add_rejection_counts(base, increment)` in `src/core/social_counts.py` (core must not import systems): keeps every key in `base`, adds each `increment` entry, does not mutate. It is the one sum rule. (First cut inlined the loop in both places; it tripped three code-health rows, so rpg-planner ruled the shared helper: one definition, not a line-move.)
2. `relationships.py` `process_update` passes `rejection_count=add_rejection_counts(social.rejection_count, update.rejection_increment)`; `SocialUpdate.merge` in `updates.py` passes `rejection_increment=add_rejection_counts(self.rejection_increment, other.rejection_increment)`. Keying unchanged; the other keyed deltas stay last-writer-wins. The explanation lives in the helper's docstring, not as call-site comments.
3. Tests (new file `tests/unit/social/test_rejection_counts_kept.py`): a trust-only update leaves counts intact; an increment for A leaves B; a merge of two same-tick rejections from one offerer gives 2; two offerers stay separate; a `to_canonical_dict` round trip; direct helper tests in `tests/unit/core/test_social_counts.py` (empty, disjoint, overlapping, base not mutated); one appraisal row where the fatigue penalty reads the kept count (a count of 3 kept across a trust-only update still cancels a fair-pay offer).
4. Parity: add SOC-280 in `docs/parity_ledger/social_narrative.yaml` citing the new test, with the lifetime-count disclosure. A divergence entry (u24 block 2.200-2.249, 2.203 next unless taken) only if the measurement moves anything.
5. Light checks first: `tests/unit/social` and `tests/unit/core` at -n 1, `mypy_gate`, `codebase.health check`. If the ratchet fails, stop and report; no reshaping.
6. Measurement: not yet. rpg-planner relays the cell set and HOST FREE. Base cells are fresh on main 5c6990e51; both arms run with a read-only counting spy that the designer approves at its sha before any run.
7. The mechanism-completeness pin moves scope 361 -> 362 and unbound 255 -> 256 (helper left unbound, dated lines in the test).
8. Close: hot-loop timing NOT MEASURED (perf pause); hand-close record; the `record_review.py` call for the A ticket (`--review-ref 862#6784371939`) rides this PR.
