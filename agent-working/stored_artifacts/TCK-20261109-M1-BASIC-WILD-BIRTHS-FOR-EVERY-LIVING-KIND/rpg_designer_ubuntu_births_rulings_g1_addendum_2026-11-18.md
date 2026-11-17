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

# Births rulings G1 addendum (rpg-designer-ubuntu, 2026-11-18)
This amends drafts/rpg-designer-ubuntu-births-rulings-g1.md (sha256 0c8ea97d). Where they differ, this file wins. It answers lead-planner-u24's finding, which lead-planner relayed.

## A1. G1a missed a runtime reader of population_id. The ruling stands, with a disclosure and a test
**Correction.** G1 said no runtime system reads `population_id` and that compiler.py:396,426 runs at t0 only. That is wrong. On main 3aafdb383, `src/domains/campaigns/orchestrator.py` (about lines 1080-1093) rebuilds each episode's survivor roster from `EntityCarryForward.properties`, then calls `WorldCompiler.resolve_pending_information(entities, ...)` on it. That call gives each pending information response and self-model event to the first entity, in roster order, whose `properties["population_id"]` equals the target population. I missed it because I treated the compiler's matcher as compile-time only and didn't trace who else calls it.

**Ruling: delivering to a newborn is correct. Leave the reader unchanged.**
- G1a makes the newborn a member of its mother's population, so it is "of" that population. Content that targets a population means "a surviving member of it". The resolver's own comment says the same: with no surviving member it skips the entry rather than misdeliver it. So a surviving newborn who is the only member left is a correct target.
- Don't add a "t0 bodies only" filter to the shared resolver. That would change the shared match for every population and every campaign. It is also not needed: the content doesn't say the information was written for t0 bodies.
- Claim no more than the code does. The match is "first in roster order", not "t0 first". If newborn ids sort after t0 ids in the rebuilt roster, a surviving t0 member wins. Pin whatever order the code actually has.
- Under Q11 condition (b), LifeStage gates keep gating. A CHILD who receives information is not treated as an ADULT by anything. Information delivery is not a LifeStage gate.

**Disclosure** (step report and the field's doc line): in campaign mode, a surviving newborn can receive its population's pending information responses and self-model events in a later episode, through `resolve_pending_information`, when no member earlier in roster order survives.

**Condition 3, expanded.** One test file covers three cases:
1. Provenance: as in G1, a newborn id past the t0 count comes back unresolved, not as a t0 population.
2. Campaign resolver, newborn only: the roster holds only a newborn of population P, and a pending response targets P. The response resolves to the newborn.
3. Campaign resolver, both present: the roster holds a t0 member and a newborn of P. The response resolves to the entity the code picks, with the order asserted as the code has it (ascending id expected). If the code shows a different order, report it to me before the PR. Don't change the resolver.

## A2. G1b's ch05 wording is a new Bible item, not part of Q11/D3
Correction: Q11/D3 is closed. rpg-designer answered (a) YES with exact wording on 2026-11-17. So the camp-refill ch05 text ("newborns stay CHILD for the run, so 'refill' means one generation of presence near the camp, not membership") is a new Bible item. It goes to rpg-designer with the other B5 texts before the implementation PR. It needs no separate question now.

The rest of G1b is unchanged.

## Pre-bind check
- A1 adds no field and changes no shared contract. The resolver is unchanged, and the change is a disclosure plus tests. So A1 is a cc.
- A2 only moves the ch05 text into the B5 Bible batch for rpg-designer, which was already planned.
