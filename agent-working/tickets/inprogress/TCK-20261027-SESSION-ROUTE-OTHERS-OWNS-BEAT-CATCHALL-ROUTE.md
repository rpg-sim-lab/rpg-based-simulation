---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261027-SESSION-ROUTE-OTHERS-OWNS-BEAT-CATCHALL-ROUTE
phase: open
date: 2026-10-27
tags: [ai, governance]
---

# TCK-20261027-SESSION-ROUTE-OTHERS-OWNS-BEAT-CATCHALL-ROUTE

## Title
`route --from <domain>`: another domain's `owns` claim should beat the asking domain's catch-all `tools/**` route

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
agent-working-implementer-u24 found this on 2026-10-27 while closing
`TCK-20261022-SESSION-ROLES-RPG-OWNS-RPG-MEASURE`. agent-working-planner-u24 checked it against
`tools/sessions/route.py` on origin/main (3cf79fa05).

In `route()`, the asking domain's `routes` win whenever that domain doesn't itself claim the path,
**even when another domain's `owns` does claim it**. codebase, testing, lead, platform and
architecture all have `"tools/**": agent-working-designer` in their `routes`. As a result:

- `route tools/rpg_measure/paired.py --from codebase|testing|lead|platform|architecture` returns
  agent-working-designer.
- `route ... --from rpg|agent-working|asset|perf` returns rpg, which is the real owner.

This doesn't only affect the new rpg_measure entry. From codebase, `tools/perf/**`, `tools/loadtest/**`
and `tools/visual_assets_*.py` also go to agent-working-designer. The only `tools/` paths that escape are
`tools/test_architecture/**` and `tools/release/**`, and only because those domains route them to
testing-planner explicitly. A seat that follows `route --from` sends work about a path another domain
owns to the wrong session.

The plan text (`session_layer_working_process.md` §9.1: "`--from` applies the asking domain's `routes`
to a path it does not own") is ambiguous. "it" can be read as the asking domain, which is what the code
does, or as no domain.

## Scope
- `tools/sessions/route.py::route()`: when `from_domain` is set, an `owns` claim by any other domain beats
  a route from the asking domain whose glob is **less specific**. See the open question for the exact rule.
- `tests/tools/test_session_route.py`: cover each case.
  - Another domain owns the path and the asker has a catch-all route: the owner wins.
  - The asker has an explicit, more specific route (e.g. `tools/release/**` -> testing-planner): the route
    still wins.
  - Nobody owns the path: the asker's route still applies.
  - A split path: unchanged.
- `docs/plans/agent_infrastructure/session_layer_working_process.md` §9.1: state the precedence exactly.
- Run a route diff over all tracked paths for every `--from` domain, before and after. Report every path
  whose answer changes.

## Out of Scope
- Any change to `owns`/`routes` entries in `registries/session_roles.yaml`. That includes adding per-path
  routes to the 5 domains, which was rejected as option (b) on the RPG-MEASURE ticket.
- Card text and card budget: route.py logic doesn't change the cards. If the generated cards change,
  stop and report.
- `.claude/settings.json`, CLAUDE.md.

## Acceptance Criteria
1. `route tools/rpg_measure/paired.py --from X` names rpg for every domain X.
2. `route tools/release/<f> --from testing` (and every other existing explicit specific route) answers
   the same as before.
3. The route diff (all tracked paths × all `--from` domains) changes only paths that some domain's `owns`
   claims. Each changed answer moves from a route target to that path's owner, and the PR body lists them.
4. `pytest tests/tools -k "session or route or roster or card" -p no:randomly` passes, run serially.
5. §9.1 states the rule, and the PR body quotes the new wording.

## Related Tickets
- TCK-20261022-SESSION-ROLES-RPG-OWNS-RPG-MEASURE (where it was found; recorded there as an unmet
  scope check)
- TCK-20261004-SESSION-LAYER-M3A-ROUTE-OWNER-LOOKUP (built route.py and `--from`)

## Related Docs
- docs/plans/agent_infrastructure/session_layer_working_process.md §9.1

## Related Stored Artifacts
None.

## Related Code Areas
- tools/sessions/route.py
- tests/tools/test_session_route.py
- registries/session_roles.yaml (read only)

## Assumptions / Open Questions
- **Precedence rule (owner decides before dispatch).** Proposed: compare glob lengths and let the longer
  glob win. A route beats another domain's `owns` only when its glob is longer than that owns glob; on a
  tie, `owns` wins. Under this rule `tools/release/**` routes still win where nothing more specific owns
  the path, and catch-alls like `tools/**` lose to any real owner. Alternative: `owns` always beats a
  route, and routes apply only to paths nobody owns. That is simpler, but it would silently override every
  explicit route that a domain's owns glob also matches. The diff in AC3 shows which paths the choice
  affects.
- Not dispatched. Dispatch waits for the user (agent-working-planner-u24's dispatch is from the user or
  agent-working-designer-u24).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
