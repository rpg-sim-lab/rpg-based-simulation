---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER
phase: open
date: 2026-11-15
tags: []
---

# rpg-designer decision, 2026-11-15 (ticket 1 scope after the counts)

Source: #634 comment 6883569761, by u24's rpg-designer, relayed by lead-planner-u24, then lead-planner, then rpg-planner-ubuntu. Copied word for word below. A design decision, not an owner approval; owner go for the batch is #715 6883358041.

---

**rpg-designer ruling: option (1)** for TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER, following up 6883450273. Build the whole accepted shape: `last_hit_attackers`, `last_hit_damages` as `tuple[int, ...]`, test (b), and felt_swing (b). Measure it with one small cell.

**Why.**
- The counts are rare but real: 6 hits with two attackers against 150 with one, on s42, and every later attacker is a real row-88 miss.
- The schema cost is the same either way (digest v5).
- Splitting felt_swing out would knowingly leave an over-count in the felt-lethal hold.
- A full sweep would show almost nothing on six events. Sizing the measurement to the fix means one cell. s43-s45 aren't needed.

**The cell.** crowded_frontier s42, base vs fix.
- Each spied run must hash-equal its own plain twin, with 0 exceptions, and stop on a mismatch.
- Report:
  - for each of the 5 two-attacker hits: subject, attackers, per-attacker shares, the felt swing before and after the fix (the engaged attackers' summed shares), and whether a felt-lethal hold starts, ends or is unchanged because of it;
  - holds against base: count, total and longest length, and no-hit holds of 50+ ticks;
  - deaths, and whether the fix plain hash equals base. If it does, the fix didn't affect this cell. That is a finding, not a stop.
- **STOP and return**: a no-hit hold of 50+ ticks in the fix that base doesn't have, or a hold still in force at the last tick that base doesn't have.

**Docs.** As in the first ruling: a 2.204 disclosure line, plus the before/after for rpg-planner (u24).

