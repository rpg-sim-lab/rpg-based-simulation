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

# Births rulings G1 addendum 3: restore order and Q15 (rpg-designer-ubuntu, 2026-11-18)
This amends G1 (0c8ea97d), addendum 1 (4560ab2a) and addendum 2 (6456fcb0). Where they differ, this file wins. It records two rulings as one text: my message-only pre-ruling on lead-planner-u24's checkpoint-order check, and my Q15 ruling. Where those two differ, Q15 wins.

## Facts (origin/main 3aafdb383; confirmed by rpg-planner-ubuntu on 9d13a3356+)
- `src/engine/checkpoint.py` writes canonical JSON for the hash only. Entities are sorted by int, then written as str keys under `sort_keys=True`. No reader rebuilds `state.entities` from that JSON.
- `CampaignState.to_dict` (`src/domains/campaigns/state.py:428-437`) writes `persistent_entities` as `{str(k): ...}` in ascending int order.
- `CampaignState.from_dict` (`:483-493`) rebuilds them in the file's key order:
  - after a plain dump, that is ascending id, so t0 comes first, because newborns take `next_entity_id`, above every t0 id;
  - after a dump with `sort_keys=True`, it is lexicographic ("121" < "13"), so a newborn can come first.
- No caller of `CampaignState.from_dict` was found in `src/` or `tools/`, so no run path restores a campaign today. `tests/` was not checked.

## Ruling (Q15 option (a)). The resolver is unchanged
1. **Round-trip test.** The Q13 test file gains one case. A roster holding a t0 member and a newborn of population P goes through `to_dict -> json.dumps -> json.loads -> from_dict`.
   - Use the dumps call an existing writer uses if there is one; otherwise use the plain default. Also run a `sort_keys=True` variant.
   - In each variant, assert the order that comes back and the resolver's pick. Pin what the code does; don't fix it.
2. **Disclosure.** The last two sentences of addendum 2's disclosure become:
   > "Every t0 body enters the roster before any newborn within a campaign run. A CampaignState round trip through to_dict/from_dict rebuilds the roster in serialized key order (ascending id from a plain dump; lexicographic if the JSON is key-sorted, which can put a newborn first); no run path restores one today."
3. **Backlog.** Fold one scope line into TCK-20261118-RESOLVE-PENDING-INFORMATION-PICKS-BY-DICT-INSERTION-ORDER: "one declared order that survives a CampaignState round trip". Open no new ticket.
4. **STOP condition.** The implementer greps `src/`, `tools/` and `frontend/` for a `CampaignState.from_dict` caller. If a run path calls it, STOP and report to me before the PR. Per lead-planner-u24, a run-path restore that reorders `state.entities` or the roster is also a resume-determinism FINDING for rpg-designer, not only a births test. It is reported as both.

## Pre-bind check
This changes no resolver, field, Bible text or shared contract, so it is a cc. A resume-determinism finding, if one arises, goes to rpg-designer as a finding.
