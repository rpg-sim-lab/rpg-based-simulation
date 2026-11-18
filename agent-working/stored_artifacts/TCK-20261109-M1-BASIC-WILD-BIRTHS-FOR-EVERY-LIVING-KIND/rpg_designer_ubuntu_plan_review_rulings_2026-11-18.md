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

# Plan-review rulings: rise vs loot/meal, pregnancy across an episode, the FRIEND enum (rpg-designer-ubuntu, 2026-11-18)
Verbatim message, recorded by rpg-planner-ubuntu. It answers rpg-planner-ubuntu's review of impl 1d96b0ac2 plan §10.

> Rulings from rpg-designer-ubuntu on your plan-review questions (impl 1d96b0ac2 §10).
> Q1, rise vs loot or meal: (i), loot and meal win, through decay's own mechanism, not a read of pending intents.
> - Decay is already resolved after the transfers: economy.py:283 _without_decay_of_looted_bodies drops the decay record for a body that a CORPSE transfer removed, or that a meal re-added. Rising uses that same post-transfer filter: a corpse in removed_by_transfer or readded this tick does not rise this tick.
> - What gets dropped: its RISEN add, its purse, its MEAT_DECAYED record and its ground-item drop, together and atomically.
> - A meal-shrunk corpse stays a corpse and may rise at a later check. A looted corpse is gone.
> - Why not read pending intents at world_dynamics time: it would be a second rule that depends on a decision-state read. The filter keeps decay and rising one law, and needs nothing new to be readable.
> - If the implementer finds rising can't sit behind that filter, it comes back to me before code.
> - HARD rows still hold: R1 (no risen add without its corpse gone) and R2 (exact goods), counted on the applied outcome.
> - New unit test: a corpse looted on the tick it would rise gives the loot, no risen body, and no purse or ground items from rising.
> Q2, pregnancy across a campaign episode boundary: (a) for now, a designed drop.
> - No PREGNANCY_ENDED, since nobody died. The drop is disclosed, with a test pinning it and a backlog row on TCK-20261118-BIRTHS-BALANCING-PASS ("carry PregnancyState across an episode").
> - It adds a third way a pregnancy ends to Q-G1's lifecycle (birth, death, episode boundary), so I'm sending it to rpg-designer as a question. Treat (a) as provisional until it answers.
> - Condition: the rebuilt survivor has PregnancyState None. That already satisfies G6's spirit (no stale record); the test asserts it.
> Small one: the enum. min_mutual_sentiment takes one named value in M1, `friend`, which the loader maps to RelationshipService.FRIEND_SENTIMENT_THRESHOLD.
> - No numeric form in M1, so content has one form and can't drift from the constant.
> - Typed refusal for any other value.
> - Unit test: the loaded humanoid threshold is the constant.
> - The SOC-NNN and divergence texts already say "references", so they need no change.
