# Implementation Sequence: next-generation-engine

Epic `TCK-20261109-EPIC-NEXT-GENERATION-ENGINE`, filed by architecture-planner-u24, 2026-11-09. Owner decisions and delivery
model: #715 6735575831. Scoping only; no implementation authorised.

## Order

1. **World farm** (to be cut by platform-planner, the ubuntu seat, as filed; lead-planner-u24 may reassign it to platform-planner-u24)
   and **stage 0 re-measure** (to be cut by perf-planner). Both are independent, and the farm comes first in priority (owner Q3).
   - Stage 0 needs an owner exemption from the perf pause (#715 6556861718) or the end of that pause (ubuntu review N1).
   - **World farm: filed 2026-11-15 as `TCK-20261115-WORLD-FARM-RUNS-WORLDS-SIDE-BY-SIDE-WITHOUT-CLASHING`** (platform-planner,
     ubuntu; claim #634 6889978228). The owner approved filing and building it (#715 6889952914, item B), covering the review's §7
     blockers 1 to 3 only, with no `src/engine` change. platform-implementer writes it; rpg-planner-ubuntu reviews (its answer of
     2026-11-15 is in the ticket). Blocker 4 (N worlds per host) is perf-planner's, under the exemption in item C. Was: no platform
     seat running (N2).
2. `TCK-20261109-NEXT-GENERATION-ENGINE-ADR`: **DONE 2026-11-09**, accepted by the owner (#715 6742854335) and adopted as `docs/architecture/next_generation_engine_adr.md`. Was: lead-planner (ubuntu) reviews it; it then goes to the owner for acceptance. It depends
   only on that review and the owner's yes (ubuntu review R5). It stays separate from `TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT`
   (R1: split).
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

- 2026-11-19: `TCK-20261119-AN-ENGINE-STEP-REGISTRY-RETIRES-THE-PIPELINE-IMPORT-OF-THE-RISEN-SYSTEM` filed by rpg-planner. It is the retiring ticket for births' owner-approved import-baseline row `src.engine.pipeline_phases.resources -> src.world.risen`, and must be on main before births merges. It is not ordered within the stages yet; architecture-planner-u24 places it when it runs again.
