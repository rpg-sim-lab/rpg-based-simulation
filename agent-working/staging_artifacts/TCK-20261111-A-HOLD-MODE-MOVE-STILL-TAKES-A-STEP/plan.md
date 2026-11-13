---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP
artifact_type: plan
tags: []
---

# Plan

Read-first (dispatch of 2026-11-13, owner #715 6843780354). No fix before rpg-designer rules. 1. Read what HOLD means in code and docs, who writes it, whether the def2 shape is still possible on main, and finding (a): done in investigation.md, sent to rpg-planner. 2. rpg-designer rules the meaning. 3. Only then: a fix (HOLD takes no step) with a unit test pinning it and a paired measurement if the rule moves any outcome, or a docs-only close if HOLD is a priced step. Any parity-ledger edit goes through tools/parity_ledger_writer.py, never by hand. No cells without rpg-planner's HOST FREE. No push without a verified owner yes at an exact sha. The record_review row for 903#6843438923 rides this PR.
