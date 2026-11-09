# Implementation Sequence: next-generation-engine

Epic `TCK-20261109-EPIC-NEXT-GENERATION-ENGINE`, filed by architecture-planner-u24, 2026-11-09. Owner decisions and delivery
model: #715 6735575831. Scoping only; no implementation authorised.

## Order

1. **World farm** (to be cut by platform-planner) and **stage 0 re-measure** (to be cut by perf-planner). Both are independent, and
   the farm comes first in priority (owner Q3).
2. `TCK-20261109-NEXT-GENERATION-ENGINE-ADR`: lead-planner (ubuntu), when the ubuntu lead is reachable and its docs batch has landed.
   It may be combined with `TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT`.
3. `TCK-20261109-NEXT-GENERATION-ENGINE-ACCESS-AUDIT` (stage 1): design now. Code after 2, after the three RPG heads (LOW-HP,
   hardening, hit-wake) are pushed, in a gap rpg-planner names, under rpg-planner's conditions in the ticket.
4. `TCK-20261109-NEXT-GENERATION-ENGINE-CONTRACT-SPEC`: architecture, after 2, with 1's and 3's results.
5. **Stages 3 to 5:** not cut. They come after M1 completes and 4 is accepted. The parallel executor also needs Gate B.

## Rules

- Trunk, additive stages: small PRs on `main`, behind the existing selection. The current path stays untouched and selected as today
  until equivalence is proven. No long-lived integration branch. Spike branches are never merged.
- Every stage PR carries a Level A equivalence test: content compare first, then hash and `TICK_END` trail.
- `src/engine` stages are sequenced by rpg-planner around M1. E's refactor never rides an M1 PR.
- Perf work comes in only on a measured hard issue (depth rule, #715 6731764470).
- The filing rides a later implementation PR on this track (#715 6697748243).
