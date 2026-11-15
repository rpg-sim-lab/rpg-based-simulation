# Implementation Sequence: next-generation-engine

Epic `TCK-20261109-EPIC-NEXT-GENERATION-ENGINE`, filed by architecture-planner-u24, 2026-11-09. Owner decisions and delivery
model: #715 6735575831. Scoping only; no implementation authorised.

## Owner decision 2026-11-15 (#715 6889952914, owner's words 6889947724)

This supersedes any older gate text below where they differ.
- **Child 3, world farm: unblocked.** Owner item B: platform-planner (ubuntu) files and builds it. No `src/engine` change. Its
  filing is recorded in item 1.
- **Child 1, stage 0 re-measure: unblocked.** Owner item C exempts it from the perf pause (#715 6556861718). The exemption is
  measurement only and is recorded in `TCK-20261101-PERF-BENCH-KNOWN-REDS-PARKED-DURING-THE-PAUSE`. perf-planner filed it as
  `TCK-20261115-PER-PHASE-TICK-COST-AFTER-THE-HOSTILITY-AND-COOPERATION-FIXES`. It takes the heavy slot in turn through the leads.
  The pause stays for everything else.
- **Still paused:**
  - the languages/architecture re-design (owner, 2026-11-14, #715 6875162764): no stage 3 cut, no contract spec draft 3;
  - all `src/engine` work under this epic until after Milestone 1.

## Order

1. **World farm** (to be cut by platform-planner, the ubuntu seat, as filed; lead-planner-u24 may reassign it to platform-planner-u24)
   and **stage 0 re-measure** (to be cut by perf-planner). Both are independent, and the farm comes first in priority (owner Q3).
   - Stage 0 needs an owner exemption from the perf pause (#715 6556861718) or the end of that pause (ubuntu review N1).
   - No platform seat is running on either host, so the farm waits for one to launch (N2).
2. `TCK-20261109-NEXT-GENERATION-ENGINE-ADR`: **DONE 2026-11-09**, accepted by the owner (#715 6742854335) and adopted as `docs/architecture/next_generation_engine_adr.md`. Was: lead-planner (ubuntu) reviews it; it then goes to the owner for acceptance. It depends
   only on that review and the owner's yes (ubuntu review R5). It stays separate from `TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT`
   (R1: split).
3. `TCK-20261109-NEXT-GENERATION-ENGINE-ACCESS-AUDIT` (stage 1): **DONE**, merged as #863 (`5c6990e51`). The report is
   `docs/plans/architecture/next_generation_engine_access_audit_report.md`. Code by rpg-implementer-2, sequenced by rpg-planner
   (#715 6743082252).
4. `TCK-20261109-NEXT-GENERATION-ENGINE-CONTRACT-SPEC`: architecture. Draft 2 is written with 3's results and approved by ubuntu
   (`ea0446ffe`, #715 6785056608). Draft 3 waits on child 1's costs, and on the re-design pause lifting.
5. **Stages 3 to 5:** not cut. They come after M1 completes and 4 is accepted. The parallel executor also needs Gate B.
   - **Stage 3 entry condition: CLEARED 2026-11-12.** rpg-planner took `src/systems/strategic_systems/intelligence.py` off its
     hands-off list (spec §8). The §8 slice is `fused_strategic_pass` (ubuntu review A-n2).
   - rpg-planner signed off on the spec's §8 (A-n1) on 2026-11-11.
   - Stage 3 is still not cut. That waits on M1, the re-design pause, and child 1's costs for the slice order.

## Rules

- Trunk, additive stages: small PRs on `main`, behind the existing selection. The current path stays untouched and selected as today
  until equivalence is proven. No long-lived integration branch. Spike branches are never merged.
- Every stage PR carries a Level A equivalence test: content compare first, then hash and `TICK_END` trail.
- `src/engine` stages are sequenced by rpg-planner around M1. E's refactor never rides an M1 PR.
- Perf work comes in only on a measured hard issue (depth rule, #715 6731764470).
- The filing rides a later implementation PR on this track (#715 6697748243).
