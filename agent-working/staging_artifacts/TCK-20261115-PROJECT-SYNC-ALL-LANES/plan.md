---
status: active
layer: ticket
authority: P2
audience: agent
phase: inprogress
ticket_id: TCK-20261115-PROJECT-SYNC-ALL-LANES
artifact_type: plan
tags: [planning, delivery]
---

# Plan

Order: (1) investigation answers (below, done); (2) `attribute()` prefix + roster domains; (3) all-lanes candidates and the Domain value; (4) Epic (a) fix; (5) client: Domain rename + single-select in `--init`, heartbeat steps; (6) `--fetch`; (7) last-run file + start-hook line; (8) heartbeat + stale-host flag; (9) docs; (10) tests; (11) first load by hand (AC3).

## Design

**1. All lanes.** `project_sync` reads the registered domains from `load_roster(root).domains` (9 today). `pilot_lanes` is ignored (key stays in the yaml, unused, noted). `in_pilot_lane` is deleted. Candidates = every id on any branch fact ∪ every id with a `todos/` or `inprogress/` copy on origin/main ∪ existing items. Done tickets on origin/main that no branch holds and no item exists for are NOT candidates (no mass Done creates; `pilot_start` and `done_window_days` stay as they are).

**2. Domain of a main-only ticket** (amended after the planner's review). Order: (a) the domain in any host's segment (`Host facts domain=`); (b) **routed code areas**: take the repo-relative path tokens of the ticket's `## Related Code Areas`, route each through `tools/sessions/route.py::route()` (manifest only, no guess); if every routed path gives the same single domain, that is the Domain (an unowned path is skipped; a SPLIT path counts all its domains); if the routed paths disagree or none routes, (c) `unassigned`. Never from `layer`. Measured on origin/main (investigation): 124 of 161 todos/inprogress tickets resolve (120 rpg, 2 agent-working, 1 asset, 1 platform), 37 stay `unassigned` (21 disagree, 10 no path token, 6 none routed). If the designer rejects (b), this is recorded here and the planner takes it to the owner. The SEQUENCE.md filing-seat rule is dropped (investigation).
Several distinct domains for one ticket (two hosts disagree): the Domain select takes the sorted-first one and adds a finding (same on every host, so no flip-flop).
**Amendment F (designer):** tokens are taken from `## Related Code Areas` of the chosen copy; strip backticks, a trailing `::name` or `:line`, and trailing punctuation; skip any token holding `*`, `{` or `}`; route in-process with `route(path, roster)` using the roster the sync already loaded (no subprocess); ignore unowned paths. All remaining owners the same -> that domain; they disagree or none remain -> `unassigned`, counted in ONE summary note (`domain: N tickets unassigned (no or mixed code-area owners)`), never a finding per ticket. The doc calls it "the owner of the code the ticket names", not a guess. Known limit (in the limits line): both hosts agree only when run on the same roster; with different checkouts it is last writer wins until both are on the same origin (same as the existing content rule). Tests: paths agree; mixed -> unassigned and counted; unowned paths and glob tokens skipped; a segment's domain beats the code areas. The 37 unassigned (21 mixed, 10 no path token, 6 not routed) go in the ticket's Test Summary and a limits line.
The code-area read needs the ticket body: `TicketCopy` gets `code_areas: tuple[str, ...]`, filled by `parse_copy` from `## Related Code Areas` (path tokens: containing `/`, backticks and punctuation stripped).

**3. `attribute()` prefix fix.** `attribute(branch, seats, domains)`: the longest registered domain `d` such that `branch.startswith(d + "-")` gives `(f"{d} (seat not recorded)", d)`; no match gives `("unknown", "unknown")`. A recorded seat still wins, with the roster's domain.

**4. Domain single-select.** `TEXT_FIELDS` loses `Domain`. `init_fields`: if `Domain` is TEXT and `Domain (old)` is absent, rename it (`updateProjectV2Field` with `name`; new client method `rename_field`), then create the single-select `Domain` with options = registered domains + `unassigned` + `unknown`; if `Domain` is already a single-select, append missing options (`merge_options`); if both `Domain` TEXT and `Domain (old)` exist, refuse (nothing written). A second `--init` prints "left alone". Never deletes. `SELECT_FIELDS` gets `Domain`; `apply_plan` already writes in VALUE_ORDER. A derived Domain with no option is a finding, field left empty (like Layer). The hash fields are unchanged (Domain stays in the hash as its string value).

**5. Epic rule (a).** In `make_epic_resolver.resolve`, the folder key comes from the chosen copy's path, else from ANY origin path for the same id (`main_index[tid]`), so a branch copy under `inprogress/` of a ticket that lives in an epic folder on origin still resolves to the epic.

**6. `--fetch`.** `fetch_origin(root)` runs `git fetch origin main` through its own narrow runner (exact argv, `_guard` untouched and still refusing `fetch`). On failure the run carries on, adds a finding and the header already shows origin/main's age. Not set by default.

**7. Last-run file.** After each `--apply` (and only then) write `~/.local/state/rpg-project-sync/last-run.json` (mode 600; dir created): `{time (UTC), host, rc, done, left, error (redacted, first), failed_streak, stale_hosts}`; `failed_streak` = previous streak + 1 when rc != 0, else 0. Write failure never fails the run. Warning: `session_start_hook._sync_line(root)` (same pattern as `_disk_line`: one small file read, fails open) prints one line when `failed_streak >= 2` or the file is older than `stale_host_hours`. Lowest cost: no new tool, ~15 lines. Only the hook's Python under tools/ changes; `.claude/settings.json` is the owner's and is not touched.

**8. Heartbeat.** One draft item titled `_sync heartbeat` (no Ticket ID) with text field `Last run` (new text field, created by `--init`): one segment per host, `u24desktop: 2026-11-15T10:00Z rc=0`, segments joined by `; ` and parsed with the `merge_host_facts` pattern. It is written as the LAST step of `--apply`, after the plan steps, because rc is only known then: create it (draft + Last run) if absent, else set `Last run` with only this host's segment replaced (1 mutation). If `--apply` stops, the heartbeat is still written with rc=1, best effort and a SINGLE paced attempt with no retry loop (amendment D, so it cannot break a run stopped by a rate limit): a failed heartbeat write prints `heartbeat: not written (<redacted error>)`, is recorded in the last-run file, and never changes the run's rc or hides the first error. Two heartbeat items (a create race between hosts) are handled by (amendment C): read the segments from all of them, write this host's segment to the oldest (first in list order), print a finding naming the extra; **nothing is archived** (removing the extra is a delete: the owner does it by hand through the lead).
A dry run reads it and prints `stale-host: <host> last run <ts> (> stale_host_hours)` as a note, and the same list goes in the last-run file. It only reports: no Status change, no archive. A dry run adds nothing to the plan, so "nothing to do" stays true.
Heartbeat in views: it is an item with no Status. **Open for the designer:** keep it visible (the point of a heartbeat) and have the owner filter it out of views 1-4 by hand (`-title:"_sync heartbeat"`), or give it a seventh Status? I propose the first (no new Status, no change to `STATUSES`).

**Amendments from the designer's review (A-E).**
- **A. Rename and hand edits.** After `--init` renames, an item's old text value sits under `Domain (old)` and the new `Domain` reads "". `hand_edits()` would report a false edit on every item. Fix: in `build_plan`, when an item's `Domain` is empty and it has `Domain (old)`, the hash check (and `hand_edits`) uses the `Domain (old)` value; the derived Domain is written as a normal update. Test: after a rename fixture, no hand edits and only Domain updates are planned.
- **B. No pre-P3b `--apply` once the heartbeat exists.** P1c/P2 code archives "an item with no Ticket ID", which is the heartbeat. AC3 gets: no `--apply` on pre-P3b code, on either host, after the first P3b `--apply`. A pre-P3b dry run showing "archive _sync heartbeat" is expected, not a finding. The ubuntu dry run (AC3.5) must run on this branch's code. Said in the doc.
- **B (doc).** The limits line also says: P2-code `--apply` archives an item with no Ticket ID, so the heartbeat is lost if anyone runs pre-P3b code after the first load.
- **C.** two heartbeats: see item 8. **D.** single heartbeat attempt: see item 8.
- **E. `--fetch` timeout.** `fetch_origin` uses a 60 s timeout; a timeout takes the failure path (carry on, finding, origin/main's age printed).
- **Heartbeat in views.** No seventh Status, STATUSES unchanged. The heartbeat stays visible; the owner filters it out of views 1-4 by hand in the UI, trying `has:status` first (the sync sets Status on every ticket item and never on the heartbeat), else `-title:"_sync heartbeat"`. Owner UI step; the sync does not depend on it. Put in the doc. The heartbeat is written on every `--apply` even when nothing else changed (one mutation per timer run for an honest liveness signal); stated in the limits line.

**9. Docs.** `project_sync_dry_run.md`: all lanes, Domain rules, `--fetch`, last-run file, heartbeat, plus a limits line for each (rule 2 dropped, `unassigned` until a branch copy exists, heartbeat written even when nothing else changed).

## Scope guards
No timer/unit files (P3c); no delete; no pacing change (P3a); no claim rule (P4); `_guard` unchanged; `Domain (old)` is renamed, not deleted. Token handling unchanged.

## AC map
AC1 this plan + designer review. AC2 items 1-9 + tests. AC3 first load by hand: (a) live dry run with counts per domain to the planner; (b) `--init` only if the classifier allows it for this seat, else in the owner's command list; (c) exact command lines for the owner/lead terminal: `--init` if needed, a second `--init` ("left alone"), a dry run diffed against my sent plan, the `--apply`, a final dry run ("nothing to do"); rate-limit answers and the real point cost taken from that output. AC3.5 ubuntu dry run via the leads. AC4 the PR body carries the plan and the final outputs, secrets grep-checked. AC5 no delete.
