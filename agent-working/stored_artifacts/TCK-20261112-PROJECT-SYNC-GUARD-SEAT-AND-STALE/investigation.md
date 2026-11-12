---
status: historical
layer: ticket
authority: P2
audience: agent
phase: done
ticket_id: TCK-20261112-PROJECT-SYNC-GUARD-SEAT-AND-STALE
artifact_type: investigation
tags: [planning, delivery]
---

# Investigation

## Seat mapping: why every seat reads `rpg (unmapped)` (u24, 2026-11-12, real state dir)

Method: for every roster role, `status._worktree_for` result, the bound-worktree record, the instance record and the lease of each git worktree (`.git/session-roles/`).

Findings:
1. The rpg *seat* worktrees do map: rpg-designer, rpg-planner and `rpg` (rpg-implementer) each resolve to their own worktree and carry a lease.
2. The batch worktrees where rpg tickets actually live (d73, d80b, d80c, eng, f3, glossary, nonflight, recruit, sleep, selfdef, ... about 25 on this host, branch `rpg-*`) have **no lease, no bound record, and are no role's default path**. They were created by hand (`git worktree add`), not by the launcher, so no record names their writer.
3. rpg-implementer-2 and -3 are *instance* names, not roster roles; their bindings log `worktree: .../worktrees/rpg` only. The roster has one rpg-implementer role.
4. So the individual seat is **unknowable** from launcher state for a batch worktree. Only the domain is known (branch prefix), which is what `rpg (unmapped)` already says. The label is accurate but reads like a bug.
5. A true per-seat answer needs the launcher (or the seat) to record the batch worktree it works in. That is a launcher change; **out of this ticket's scope** (ticket Out of Scope; lead 2026-11-12). Report to the lead.

Smallest honest in-scope fix: a `batch_worktree_seat` map in `registries/session_project.yaml` (domain -> seat family), so an unleased worktree on an `rpg-*` branch reads `rpg-implementer (batch)` instead of `rpg (unmapped)`. It names the family, not an instance. Domains not in the map keep `<domain> (unmapped)`.

## Stale
`inspect_worktree` already computes `last_activity` (newest of last commit and working-tree change). BranchFact gains `last_activity`; Stale when older than `stale_branch_days`.

## Guard
Current `_guard` checks exact tokens only. Replace with a prefix match for `-X`, `--method` (value not GET), `-f`, `-F`, `--field`, `--raw-field`, `--input`.

## Lead note (2026-11-12): the launcher's batch-worktree record
`launch.py --worktree` records a batch worktree (TCK-20261010-SESSION-MAIN-CHECKOUT-LAUNCH-AND-BATCH-WORKTREE-RECORD); status.py reads it as `writing_in` (`_worktree_for`, bound record with writing=True). `read_branch_facts` already goes through `_worktree_for`, so a launcher-made batch worktree already gets the real seat. The family label is only the fallback for a worktree with no record. Finding for the planner (not fixed here): seats that create batch worktrees by hand with `git worktree add` are why most rows read `(batch)`.
