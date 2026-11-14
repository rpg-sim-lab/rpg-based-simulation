---
status: active
layer: ticket
authority: P2
audience: agent
phase: open
ticket_id: TCK-20261114-PROJECT-SYNC-LAYER-EPIC-PRIORITY-TAGS
artifact_type: plan
tags: [planning, delivery]
---

# Plan

Order: (0) probe, by hand, after this plan is OK'd; read-back to the planner BEFORE deleting the probe field; (1) `set_select_options` keeps ids; (2) fields + `--init`; (3) derivation (Layer/Priority/Tags/Epic); (4) hash migration; (5) docs; (6) tests; (7) live runs in P1b order, `--apply` after the planner's OK.

## 0. Probe (scratch script, not committed)
`ProjectClient("rpg-sim-lab", 1).graphql`: create single-select `zz-option-probe` (options a, b); set item X to `a`; `updateProjectV2Field` with options a, b, c passing the existing ids for a and b; read X back. Value `a` kept -> Layer SINGLE_SELECT. Value cleared -> Layer TEXT, and the planner is told before anything else. Send the read-back, then delete the field by hand (`deleteProjectV2Field`; the only delete, probe field only, never in repo code); read the field list back to show it is gone. Checkpoint: hold after the read-back until the planner says go.

## 1. `ProjectClient.set_select_options(field_id, options)`
`options` becomes `list[tuple[name, color, id | None]]`; the GraphQL option input carries `id` when known. New helper `merge_options(existing: ProjectField, wanted: list[(name, color)]) -> list[tuple]`: existing options first, with their ids and original order, then each wanted name not present appended with `None`. It never drops an existing option. P1b's Status path uses it too, so a Status change keeps the ids of unchanged options; `--replace-status-options` stays as is (explicit replace with no ids).

## 2. New fields in `--init`
`Layer` (SINGLE_SELECT, options = `layer_registry.jsonl` layer values; TEXT if the probe fails), `Priority` (SINGLE_SELECT P0-P3), `Epic` (TEXT), `Tags` (TEXT). Existing same-name wrong-type field -> the existing refusal. Existing Layer/Priority with missing options -> `set_select_options(merge_options(...))`, reported as `updated: Layer options + <names>`. A rerun reports nothing created or updated.

## 3. Derivation (pure, in `project_sync.py`)
- `TicketCopy` gains `layer`, `priority`, `tags`; `parse_copy` reads frontmatter `layer:` and `tags: [..]` and `## Priority`. Tags joined by single spaces in the file's order.
- Layer not in the registry, or Priority not in P0-P3, or empty: field empty + note `<id>: layer 'x' not in registry`.
- Epic, first match wins: (a) the best copy's path (branch copy first, else main) is `.../todos/<folder>/` -> epic id = the `TCK-*-EPIC-*.md` in that folder (from the main index) else the folder name; (b) the id is named in exactly one folder's `SEQUENCE.md` `## Order` (todos/ or done/) -> same epic-or-folder rule for that folder; more than one folder -> `standalone` plus a note naming the folders; (c) `standalone`. `## Related Tickets` is not read.
- SEQUENCE.md texts are read once per run with `git ls-tree` + `git show origin/main:<path>` through `run_command` (read verbs only), cached in a dict passed into `build_plan`.
- `derive_item` fields gain Layer, Priority, Epic, Tags; `HASH_FIELDS` gains them (Layer, Priority, Epic, Tags appended at the end).

## 4. Sync hash migration
`HASH_FIELDS_V1` (the P1b nine) is kept. `hand_edits`: not a hand edit if `sync_hash(item) == stored` OR `sync_hash(item, HASH_FIELDS_V1) == stored`. The update still happens because the new fields differ from the empty live values; the new hash replaces the old one. One test.

## 5. apply / client
`VALUE_ORDER` gains Layer, Priority, Epic, Tags (after Tier); `SELECT_FIELDS` gains Layer, Priority (not Epic/Tags). `Sync hash` stays last. Option ids are looked up by name per run (existing code).

## 6. Docs and tests
`project_sync_dry_run.md`: the 4 fields, the Epic rule, the probe result. About 9 tests: derivation (empty/unknown), Epic (a)/(b)/(c)/ambiguous, merge_options keeps ids and appends, hash migration, `--init` adds a newly registered layer option and rerun is a no-op.

## 7. Live runs (Project 1, P1b order)
dry run -> `--init` -> second `--init` (no-op) -> `--apply` plan to the planner (about 30 updates, no hand edits) -> `--apply` -> final dry run (nothing to do). Stop on any refusal; no retry.

## Branch and SEQUENCE.md
Branch `agent-working-project-sync-layer-epic` cut from origin/main 6b8b56eda (#909 merged). SEQUENCE.md: P1c entry; TCK-20261114-PROJECT-CLIENT-WRITE-PACING listed as a P3 prerequisite, not cut. The pacing ticket file is not taken.

## Out
P3 (Domain single-select, other boards), pacing/retry, new views, other lanes, ubuntu, writes back to tickets.
