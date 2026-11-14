---
status: active
layer: ticket
authority: P2
audience: agent
phase: open
ticket_id: TCK-20261114-PROJECT-SYNC-INIT-AND-APPLY
artifact_type: plan
tags: [planning, delivery]
---

# Plan

Order: (1) `tools/sessions/project_client.py` (new), (2) wire `--init`/`--apply`/live read into `project_sync.py main()`, (3) tests, (4) doc, (5) write-proof runs AC 2(a)-(e) only after the owner's Project number arrives through the planner.

## Decision for the designer
The ticket says "one `ProjectClient`". I put it in a **new module** `tools/sessions/project_client.py` rather than inside `project_sync.py`, so that `project_sync.py` still contains no `graphql` call at all and `_guard` stays untouched. `project_sync.py` imports it lazily in the `--init/--apply/live-read` branches only. The ticket lists `project_sync.py` as the code area; the new file is one extra path. Say if you want it inlined instead.

## 1. `project_client.py`
- `TOKEN_PATH = ~/.config/rpg-project-sync/token`; `read_token(path)` raises `ClientRefused` (plain message, no token) if the file is missing or `stat.S_IMODE(mode) != 0o600`.
- `class ProjectClient(owner, number, token_path=TOKEN_PATH, runner=_run_gh)`: `graphql(query, variables)` builds `{"query":..., "variables":...}` JSON and passes it on stdin to `["gh","api","graphql","--input","-"]`; env = copy of `os.environ` without `GH_TOKEN`/`GITHUB_TOKEN`, plus `GH_TOKEN=<token>` for that call only. Non-zero exit or a body with `errors` raises `ProjectError` whose message is the response text with the token replaced by `***` (a defence even though gh doesn't echo it). The token is read per call and never stored on the instance.
- `runner` is the injection point for tests: `runner(args, env, stdin) -> CompletedProcess`.
- Methods: `load_project()` (id, fields by name with type and options), `list_items()` (paginated), `create_field(...)`, `set_status_options(field_id, names)`, `add_draft(title, body)`, `update_draft(draft_id, title, body)`, `set_value(item_id, field, value)`, `clear_value(item_id, field)`, `archive(item_id)`. No delete mutation anywhere.

## 2. `--init` (`init_fields(client) -> InitReport`)
Wanted: text `Ticket ID, Domain, Seat, Host, Branch, PR, Source, Sync hash`; single-select `Tier` (hotfix, standard, epic); built-in `Status` with options exactly `STATUSES`; built-in `Title` as is. Pass 1 classifies all fields; any same-name wrong-type field -> print it, write nothing, return non-zero. Pass 2 creates the missing ones and sets Status options if they differ. Prints created / updated / left alone. A second run prints nothing created or updated.

## 3. `--apply` (`apply_plan(client, project, plan, items) -> ApplyReport`)
Field ids and option ids come from `load_project()` on that run. Create: `add_draft(Title, BODY)`, then set `Ticket ID, Status, Domain, Seat, Host, Branch, PR, Tier, Source` (skipping empty), `Sync hash` last. Update: `update_draft` when Title changed; set each changed field (clear if the new value is empty), `Source`, then `Sync hash` last. Archive: `archive(item_id)`; a no-ID item is matched by its title. A mutation failure stops the run, prints done vs not done and returns 1.

## 4. `project_sync.py main()`
- `--init` / `--apply` need `project.number > 0`, else exit 2 with a plain message; `--init` with `--apply`, or `--apply` with `--items`, exit 2.
- Items: `--items` file if given; else a live read when the Project is configured and the token is readable; else none, with a note. The dry run is still the default and writes nothing.
- `--apply` prints the same plan text as the dry run (header says APPLY), then applies.
- `_guard` and `run_command` unchanged.

## 5. Docs and config
`docs/guidelines/session_roles/project_sync_dry_run.md`: usage, token rule, never-delete rule. `registries/session_project.yaml`: `number` is set to N only when the owner gives it, in the same change as the proof runs.

## Out
P2/P3/P4, views, tokens, creating the Project, `status.py`/launcher/roster, writes back to tickets.
