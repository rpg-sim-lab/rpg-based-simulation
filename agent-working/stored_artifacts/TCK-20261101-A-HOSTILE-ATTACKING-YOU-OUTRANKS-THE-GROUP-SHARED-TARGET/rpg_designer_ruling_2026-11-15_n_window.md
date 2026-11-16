---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET
phase: open
date: 2026-11-15
tags: []
---

# rpg-designer ruling, 2026-11-15 (ticket 2: the home of N)

Source: #634 comment 6883797779, by u24's rpg-designer, relayed by lead-planner-u24, then lead-planner, then rpg-planner-ubuntu. Copied word for word below. A design ruling, not an owner approval; owner go for the batch is #715 6883358041.

---

**rpg-designer ruling: where N comes from** in TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET.

**Q1 = option (2).** N is a named module constant, `ATTACKED_RECENTLY_WINDOW_TICKS`.
- It gets a new deferred-tuning register entry, D-13, in `docs/plans/deferred_tuning_decisions_register.md`, with its value, rationale and evidence. The Bible ch.02 line cites it.
- The AC test "changing N changes the window" patches the constant.

**This amends my scope line.** Ticket 2's scope says N is "a content or tuning value, NOT a number in code". That is replaced by: "a named constant registered in the deferred-tuning register (D-13), following D-11/D-12; not an unnamed literal."
- What that line was meant to prevent is a magic number buried in `target_score`. The register gives N a name, a record and a place to retune it, which is how this repo already handles the 0.2 trust floor, the VANGUARD ×0.5 multiplier, D-11 and D-12.
- The simpler path is also the cheaper one. Option (1) builds new plumbing and a schema for one number, with no runtime tuning reader in place to justify it.
- (3) is rejected for the planner's reason: it ties a scheduler cadence to a combat meaning.

**Q2 = 10 ticks.** "Attacked me" and "acting on me" then cover the same width as the row-88 act-test window, so they agree.
- It stays a separate constant on purpose. No test pins the two as equal, because they are different meanings and can be retuned apart.
- D-13 notes the current equality as the rationale for the value.

**fyi accepted:** restoring a pre-v5 checkpoint into a 1-tuple that carries the whole blow reproduces today's attribution exactly. State it in the ticket's Disclosed line.

