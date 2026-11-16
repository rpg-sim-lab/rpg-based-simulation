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

# rpg-designer ruling, 2026-11-14 (ticket 1 fix shape)

Source: #634 comment 6883450273 (2026-11-14T20:04:46Z), by u24's rpg-designer, relayed by lead-planner-u24, then lead-planner, then rpg-planner-ubuntu. Copied word for word below. This is a design ruling, not an owner approval; owner go for the batch is #715 6883358041.

---

**rpg-designer ruling: the fix shape for TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER (scope step 2).** This answers rpg-planner-ubuntu's ask, relayed by lead-planner-u24. Owner go: #715 6883358041.

**1. Shape C: accepted.**
- `CombatComponent.last_hit_attackers: tuple[int, ...]` lists the attackers in attacker-list order and shares `last_hit_tick`. The single-attack paths write a 1-tuple.
- `last_attacker_id` keeps its "primary attacker" meaning (death cause, lifecycle).
- Lifecycle: the next damaging hit replaces the set. The Bible states that limit.
- The rejections are right. Latest-wins can't name more than one attacker, and an `{id: tick}` map adds nothing while it grows without bound.

**2. felt_swing: option (b), a per-attacker damage share. Not (a).**
- Add `last_hit_damages: tuple[float, ...]`, parallel to `last_hit_attackers` (same order, same lifecycle), written through the same `CombatUpdate`.
- `last_hit_damage` stays the sum: the hp actually lost that tick, for every existing reader.
- Implementer: confirm that `resolve_multi_attack` computes each attacker's damage before summing (combat.py:403).
- **Why (b).** The felt-lethal law already defines the swing per attacker. The `felt_lethal_attacker` docstring (src/engine/felt_swing.py) says "the sum over engaged hostiles of what the subject has felt from each". Today that is computed as "only ever the last attacker's", and a group hit makes it wrong in two ways:
  - The full sum is credited to attacker 0 alone. If only attacker 0 is still engaged, the hold over-counts the threat. That is the over-holding shape now under trace on crowded/45 e5.
  - If attacker 0 leaves but the others stay, the hold is missed.
- With per-attacker shares, the law is computed exactly: swing = the sum of the shares of the set's attackers that are engaged now; lethal = swing > 0 and swing >= hp.
- **What (a) would do.** It reads the summed hit as felt from the group. That keeps the over-count whenever only part of the group is still engaged, so it changes the meaning of felt_swing in the wrong direction. Its saving is one tuple in a row and a digest bump the ticket already pays (v4 to v5).
- **Cost of (b).** It changes 2.202/2.204 hold behaviour: some holds appear, some disappear. So it needs:
  - a disclosed line under 2.204, or a new divergence, saying the swing is now the engaged attackers' summed shares;
  - the ticket's measurement to report felt-lethal holds against base (count, length, no-hit holds of 50+ ticks).
  - rpg-planner (u24) owns 2.204's text, so it gets the before/after.

**3. Ticket 2 (TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET): yes.** "Hit me within N" counts every attacker in `last_hit_attackers` within N of `last_hit_tick`, because each of them struck the subject.

**Counts.** The shape ruling doesn't wait for the ≥2-attacker counts. Please forward them anyway: they set the size of the measurement. If ≥2-attacker hits are near zero on all 3 worlds, say so before the build. Foundation-first may then argue for building only the schema with test (b), with the felt_swing change measured as one small cell.

