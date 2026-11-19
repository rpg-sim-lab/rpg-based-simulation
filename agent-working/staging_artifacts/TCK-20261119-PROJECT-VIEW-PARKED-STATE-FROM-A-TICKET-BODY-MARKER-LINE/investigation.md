---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261119-PROJECT-VIEW-PARKED-STATE-FROM-A-TICKET-BODY-MARKER-LINE
artifact_type: investigation
tags: [delivery]
---

# investigation — TCK-20261119-PROJECT-VIEW-PARKED-STATE-FROM-A-TICKET-BODY-MARKER-LINE

Measured on origin/main 0b196a142 (224 open tickets): ticket age p50 16, p90 43, max 89 days. Only 1 line-start waits-on line names a ticket id (age 4 days, no date); 6 line-start lines begin with "Parked" (tickets aged 0 to 66 days, p50 46); 1 line in all of them carries a date. 3 of the 6 park on a DECISION (owner decision, owner_decision_memo row 7), not a ticket: hence the decision form of the marker (agent-working-planner, 2026-11-19). The 45-day stale-marker finding is a proposal, not a measurement.
Code path read: `parse_copy` (project_sync.py) reads origin's copy; `derive_status` orders Done, In review, kept status, Blocked, then (new) Parked, then working/Stale/To do. Status options: `init_fields` takes `replace_options` only with `--replace-status-options` or on an empty Project; a populated Project takes `merge_options` (append-only, existing ids kept, `set_select_options` -> `updateProjectV2Field` with `singleSelectOptions`, ids on existing entries). The only paths that clear an item's Status are an option sent without its id or left out (replace, rename). The built-in Status field has NOT been probed on GitHub: scratch-Project test pending the owner's approval (creating a Project is an owner write). Before/after dry run on origin/main 025be2faf: 0 Status rows change (no marker exists), one new `parked:` note line.
Not measured: how GitHub treats an appended option on the built-in Status field of a populated Project (scratch test); the real F1 ticket (u24 planner writes the marker after the code lands).

## Scratch Project evidence (2026-11-19, owner approval #715 7011473532)
Command: a scratch script (not in the repo) using the repo's ProjectClient and `init_fields` against org rpg-sim-lab Project 2 `scratch-parked-status-test`. Output:
```
created: scratch-parked-status-test number 2 https://github.com/orgs/rpg-sim-lab/projects/2 id PVT_kwDOFTLAWc4BsWS4
default Status options: ['Todo', 'In Progress', 'Done']
--- BEFORE (6 options, 9 draft items)
    Status option ids: {'To do': '6b6780', 'In progress': '9c8f61', 'Stale': '763be3', 'In review': '2a16d1', 'Blocked': '086de8', 'Done': 'd33a46'}
    scratch item 1               Status='To do'
    scratch item 2               Status='To do'
    scratch item 3               Status='In progress'
    scratch item 4               Status='Stale'
    scratch item 5               Status='In review'
    scratch item 6               Status='Blocked'
    scratch item 7               Status='Done'
    scratch item 8               Status='Done'
init_fields exit 0
    updated: Status options -> To do, In progress, Stale, In review, Blocked, Done, Parked
--- AFTER init_fields (Parked appended)
    Status option ids: {'To do': '6b6780', 'In progress': '9c8f61', 'Stale': '763be3', 'In review': '2a16d1', 'Blocked': '086de8', 'Done': 'd33a46', 'Parked': '1886e9'}
    scratch item 1               Status='To do'
    scratch item 2               Status='To do'
    scratch item 3               Status='In progress'
    scratch item 4               Status='Stale'
    scratch item 5               Status='In review'
    scratch item 6               Status='Blocked'
    scratch item 7               Status='Done'
    scratch item 8               Status='Done'
    scratch item 9               Status='(none)'
RESULT  statuses unchanged on every item: False | changed: {}
RESULT  Parked option present: True
--- CONTROL: same options sent WITHOUT ids (what a replace/rename does)
    Status option ids: {'To do': '78729d', 'In progress': 'd2f90a', 'Stale': '6bf959', 'In review': '043bf7', 'Blocked': '41675c', 'Done': '2d6254', 'Parked': 'cbd293'}
    scratch item 1               Status='(none)'
    scratch item 2               Status='(none)'
    scratch item 3               Status='(none)'
    scratch item 4               Status='(none)'
    scratch item 5               Status='(none)'
    scratch item 6               Status='(none)'
    scratch item 7               Status='(none)'
    scratch item 8               Status='(none)'
    scratch item 9               Status='(none)'
CONTROL cleared items: 8 of 8
SCRATCH PROJECT number 2 id PVT_kwDOFTLAWc4BsWS4 url https://github.com/orgs/rpg-sim-lab/projects/2
```
Read: BEFORE and AFTER show the same Status on items 1-8 and the same six option ids; Parked was appended with a new id. The `statuses unchanged: False` line is only because item 9 (no Status) was not yet returned by the first read; `changed: {}` lists no item. CONTROL (options sent without ids) cleared all 8. Delete: `gh project delete 2 --owner rpg-sim-lab` or GraphQL `deleteProjectV2` with projectId PVT_kwDOFTLAWc4BsWS4 (the owner runs it).
