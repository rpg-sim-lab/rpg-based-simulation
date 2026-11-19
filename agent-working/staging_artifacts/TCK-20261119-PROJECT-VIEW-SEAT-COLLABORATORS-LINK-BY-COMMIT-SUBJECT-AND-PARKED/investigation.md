---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED
artifact_type: investigation
tags: [delivery]
---

# investigation — TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED

Refs: origin/main 77e4aeb72; the planner's branch base 84b44272c = 77e4aeb72 plus two ticket files (hotspot counts re-checked on both: identical). Project 1 read live at about 15:50 on 2026-11-19 (328 items).

| cause | status | numbers |
|---|---|---|
| 1 seat not recorded | measured | 47 items "seat not recorded" (19 not Done: Stale 7 of 8, Blocked 7 of 9, In progress 3 of 6, In review 2 of 2); only 3 items carry a real seat |
| 2 link by commit subject | measured, corrected | on 84b44272c over 403 branches' own commits (no merges, nothing reachable from the SHA): 128 tickets named in a subject; 16 named on a branch that does not change the ticket file (To do 10, Done 6). Earlier "31/20" was a mixed definition and is superseded. Rule (leading id + a file outside agent-working/ and docs/) moves 5 of the 10 To do; stays 5 (2 docs-only epics, 3 mid-subject or filing) |
| 3 collaborators | measured | 9 of 11 ubuntu worktree branches have a recorded seat; of 32 tickets named by such a branch 3 have 2+ seats; commit author is identical on every commit so only the worktree seat can name a seat |
| comment prefix | measured | last 100 #715 comments (2026-10-22..10-26): 38 name a ticket id, 0 start `<seat>, <date>:` (0%): comment parsing not shipped |
| 4 Parked | measured | 8 Stale; 1 of 223 open tickets has a line-start waits-on line; phrase grep would match 46 of 224: not used. Parked deferred to a separate ticket |
| 5 Hotspot | measured | 123 open tickets cite a src `.py` file, 152 distinct files, 57 cited by 2+; top intelligence.py 19, tactical.py 13, kernel.py 12, core/state.py 12; 10 seeded sample tickets agree with an independent count 10 of 10 |
| record shape | measured | `launch.py --worktree` writes `state.write_bound_worktree(root, instance, realpath, explicit)`; `status.py seat_infos` reads `read_bound_worktree` -> `writing_in` when explicit; same shape. One path per seat |
| Not visible from ubuntu | unmeasured | the coin fix branch (`rpg-coin-sink`), STALEMATE F1's `rpg-stalemate-nav` and #965: the u24 side checks them at the before/after dry run |
