---
status: historical
layer: ticket
authority: P2
audience: agent
phase: done
ticket_id: TCK-20261115-PROJECT-SYNC-ALL-LANES
artifact_type: investigation
tags: [planning, delivery]
---

# Investigation

- `attribute()` (project_sync.py): `branch.split("-",1)[0]` is the domain, so `agent-working-...` gives `agent`. The roster has 9 domains (`registries/session_roles.yaml`, loaded by `roster.load_roster`).
- Candidates today: branch copies in `pilot_lanes` plus existing items. Main-only todos have no host segment, so their Domain is empty today; "unassigned" is a new explicit value.
- `build_plan` archives any item with no Ticket ID: a heartbeat draft item would be archived unless split out first.
- Heartbeat rc is only known after the apply, so the heartbeat write is the last step, outside `apply_plan`'s plan steps (one `set_text` or `add_draft` + `set_text`).
- SEQUENCE.md as a filing-seat carrier: 6 SEQUENCE.md files under `todos/`, 4-5 with free-text "filed by <seat>", 140 flat todos with no folder. Not reliable: rule dropped (the ticket allowed this).
- `_guard` refuses `git fetch`; `--fetch` uses a separate fixed-argv runner so the read-only guard stays as is.
- `session_start_hook.py` already prints `_disk_line` and `_graphify_line`: a `_sync_line` reading one small JSON is the cheapest place for the 2-failure warning.
- GitHub `updateProjectV2Field` accepts `name` (rename without changing the field id or its values). To be confirmed live by the `--init` (the old values stay under `Domain (old)`).
- The first load is about 155 creates (To do) plus ~40 Domain updates on existing items, at 1 mutation per second.
- Routed code areas (planner's rule), measured on origin/main todos/ + inprogress/ (161 ticket files; scratch script, `route()` per path token of `## Related Code Areas`): 120 resolve to rpg, 2 agent-working, 1 asset, 1 platform = 124 resolved (77%); 37 stay unassigned: 21 whose routed paths disagree (e.g. agent-working+rpg, rpg+testing, perf+rpg), 10 with no path token, 6 with none routed.
