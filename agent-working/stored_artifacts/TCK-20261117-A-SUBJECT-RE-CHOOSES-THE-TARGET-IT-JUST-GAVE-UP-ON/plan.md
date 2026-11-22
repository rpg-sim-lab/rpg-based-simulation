---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON
artifact_type: plan
tags: []
---

# Plan

Written at close (2026-11-22) from the executed evidence of this branch; the ticket was built from the rpg-designer drafts (.claude/handover/drafts/rpg-designer-f2-giveup-memory.md, v2.2 / v2.2a) and rulings relayed by rpg-planner, so no pre-implementation staging artifacts existed.

Divergence 2.220 (Bug Fix). Four deliveries, all on branch rpg-stalemate-nav, final head 551f5d09a (merged with main 67c653219):
1. D1, the same-pass staged read: `destination_suppressed(entity, pos, tick, staged)` also reads the staged give-up record and the staged blockers of the fused strategic pass.
2. D2, one proposal point: `propose_target` for EVERY place-target writer (combat and flight included, owner scope #715 7062303482), with per-class fallbacks (flight candidates then own-tile hold; combat branch does not fire; stalemate-break holds; objective typed idle; bridge next alternative plus a typed clear; executor typed end). A source test (tests/unit/engine/test_propose_target_single_path.py) forbids an unguarded writer.
3. D3 and D4: the give-up files its ACCESS blocker with no current project; `BlockerState.giveup_count` is its own counter (omitted at 0, fingerprint ':g<n>' above 0, restore fill 0); the way-round settings moved to data (`data/content/movement/wayround_settings.yaml`).
4. A'' and C after the smoke and full runs: a clear that carries an anchor (the give-up record's, or `NavigationUpdate.target_clear_anchors` written by the strategic pass when it refuses a stored target or files a suppression) beats a same-update target set within `GIVEUP_NEAR_RADIUS` (one core constant) of that anchor; a subject with a pending record takes the slow pass and a work-queue tier (6b).
Out of scope: the G3 repeat give-ups on a few anchor tiles (carried to TCK-20261121-TWO-ANCHOR-TILES-ARE-GIVEN-UP-ON-BY-MANY-SUBJECTS-FOR-THOUSANDS-OF-TICKS, owner #715 7078467940); the own-tile-hold classifier change (owner: from the next run on).
