---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, process-improvement, governance]
---

# Project sync (dry run, `--init`, `--apply`)

`tools/sessions/project_sync.py` derives the GitHub Project items for ticket state from ticket files on `origin/main`, this host's
worktrees and open PRs. By default it is a dry run: it prints a create / update / archive plan and writes nothing to GitHub or the repo. `--init` and `--apply` (P1b) write to the Project only.

Run it from any checkout: `python3 tools/sessions/project_sync.py` (or `python3 -m tools.sessions.project_sync`). `--host` defaults to
`host_names[hostname]` in `registries/session_project.yaml`, else the hostname. 

Read-only by construction: git goes through a verb allowlist, and `gh` is limited to `pr list` and `gh api repos/...` with only
`--paginate`, `--jq`/`-q` and `--header`/`-H`. `gh api graphql` and every other flag are refused.

Status, first match wins: Done, In review, Blocked, In progress, To do. **Stale** replaces In progress only: every branch working the
ticket is older than `stale_branch_days` (default 14). A branch's age is the newer of its last commit and its index mtime, so it is
approximate: anything that refreshes the index counts as activity. A fresh filing branch does not keep an abandoned working branch In progress.

**Known gap, `<domain> (seat not recorded)`:** the Seat is the one the launcher recorded for the worktree. Worktrees made by hand with
`git worktree add` have no record, so they show the branch-prefix domain and this label. It is a gap in the records, not a sync fault.
Filed as `TCK-20261112-HAND-ADDED-WORKTREES-ARE-NOT-RECORDED-AGAINST-A-SEAT`.

## Writing to the Project (`--init`, `--apply`)

Needs `project.number` in `registries/session_project.yaml` (the org Project `rpg-sim-lab/<number>`; `0` means exit 2) and the token file.

- **Token:** `~/.config/rpg-project-sync/token`, mode exactly 600, read only by `ProjectClient` (`tools/sessions/project_client.py`) and set as
  `GH_TOKEN` in the env of its own `gh api graphql` child process. It is never in argv (the query goes on stdin), never printed or logged, never
  exported, and is redacted from any error text. A missing, empty or looser-than-600 file is refused with a plain message. Never run
  `gh auth refresh -s project`: that widens the login every seat uses.
- **Live read:** when the Project is configured and the token is readable, the current items are read from the Project (paginated, archived
  items skipped). `--items <file>` replaces that for offline runs. A run with neither flag is still a dry run.
- **`python3 tools/sessions/project_sync.py --init`:** creates the missing fields by name (text `Ticket ID`, `Domain`, `Seat`, `Host`, `Branch`,
  `PR`, `Source`, `Sync hash`; single-select `Tier`) and sets the built-in `Status` options to the six statuses. Every check comes before any
  write: a same-named field of the wrong type, or a missing `Status` field, is reported with nothing written (exit 1). Replacing `Status`
  options clears each item's Status, so on a Project that already has items it is refused unless `--replace-status-options` is given.
  A second `--init` reports nothing created or updated.
- **`--apply`** (not with `--init` or `--items`): prints the plan, then carries it out. Create = draft item, then `Ticket ID` first and `Sync hash`
  last; update = changed fields, `Sync hash` last; archive = `archiveProjectV2Item`. A failing step stops the run and prints what was done
  and what was not; the next run reconciles. Items and fields are found by id read on each run; none is stored.
- **Write pacing and rate limits** (`write_pacing` in `registries/session_project.yaml`; defaults apply when the block is missing or a value is bad):
  mutations are spaced at least `min_interval_s` (1 s) apart; queries are never paced. A *primary* limit (GraphQL `RATE_LIMITED`, an hourly
  points budget) stops the run at once: "primary rate limit: rerun after the hourly reset". A *secondary* limit (HTTP 429, or 403 whose text says
  "rate limit") is waited out and retried up to `max_tries`: the wait is `retry-after` when it shows up in gh's error text (gh prints no response
  headers and `--include` is not used, so often it does not), else `max(secondary_min_wait_s, backoff_base_s * 2**k)`, never over `backoff_cap_s`;
  after the last try the run stops as above. A plain 403 (permission) is not retried. Progress goes to stderr every `progress_every` steps.
  **A stop inside one item** leaves its new field values with the old `Sync hash`, so the next run prints "hand edit" lines for that ticket: the
  stop prints `partial: <ticket id>`, and those lines come from the stop, not from a person; the rerun overwrites them.
  **Known limits:** `retry-after` almost never shows in gh's text, so each secondary-limit retry waits 60 s (about 4 min worst case per call); a
  primary limit stops at once instead of waiting (an hourly reset does not fit a timer run; deviation from "wait as told", by design); and a
  secondary limit tagged `RATE_LIMITED` would also stop (fails safe: the rerun reconciles).
- **`--apply` needs known PR facts:** if `gh pr list` fails, or any PR's file list cannot be read, `--apply` exits 1 and writes nothing (a dry run only notes it), because In review and PR would be written wrong.
- **Never deleted:** the module has no delete mutation. Items without a `Ticket ID`, duplicates of one `Ticket ID`, and items whose ticket
  file is gone are archived, by their own item id.

## Layer, Epic, Priority and Tags (P1c)

`--init` also creates four fields, and `--apply` fills them from the ticket's own files:

- **Layer** (single-select, options = `registries/layer_registry.jsonl`) from frontmatter `layer:`; **Priority** (single-select P0-P3) from `## Priority`
  (a leading `P2 (...)` takes `P2`); **Tags** (text) from frontmatter `tags:`, joined by spaces in `registries/tag_registry.jsonl` order, unknown tags last. A value not in
  the registry or not P0-P3 leaves the field empty and prints a finding; it is never guessed.
- **Epic** (text), first match wins: (a) the ticket sits in an epic folder (`todos/<folder>/` or `done/<folder>/`): the folder's ticket whose `## Tier` is `epic`
  (an epic's own Epic is its own id); no epic ticket -> the folder name; several -> the folder name plus a finding; (b) exactly one folder's `SEQUENCE.md` (exact
  basename) names the ticket, in `## Order` if that section exists, else anywhere in the file: that folder's epic; named in more than one folder -> `standalone` plus a
  finding; (c) otherwise `standalone`. `## Related Tickets` is not read.
- **Option ids are kept.** `--init` adds a missing option (a newly registered layer) by sending every existing option with its id, so items keep their value. Probe on
  Project 1 (2026-11-14): a single-select with options a, b, an item set to `a`, options updated to a, b, c passing the existing ids: the ids of a and b stayed and the
  item still read `a`. Status on a Project that has items is append-only too (an option not in `STATUSES` is kept and reported, not dropped).
  `--replace-status-options` sends exactly `STATUSES` in order with existing ids, so only items on an option left out lose their Status (the next `--apply` restores them),
  and a rename is a remove plus an add, so only that option's items blank.
- **Sync hash** is versioned: `v2:<sha>` over the nine P1b fields plus these four; an unprefixed value is the P1b (v1) hash. A v1 item is not a hand edit; it is updated once and carries `v2:` afterwards. P2 adds `v3:` (the v2 fields plus `Host facts`); a v1 or v2 item is not a hand edit and is rewritten once.

## Two hosts (P2, `TCK-20261114-PROJECT-SYNC-SECOND-HOST`)

Ubuntu and u24 both write Project 1. Each host rewrites only its own facts and derives every shared field from the union of all hosts' facts, so both derive the same value
and a run on one host never undoes the other's. This corrects design section 5, which said Status rules 1, 2, 3 and 5 depend only on origin: that holds for Done and In review only.

- **`Host facts`** (text, created by `--init`, in the v3 hash) holds one segment per host, joined by `; `: `u24desktop: state=progress seat=a,b domain=rpg; ubuntu: state=blocked seat=c domain=rpg`.
  `state` is `filing | progress | stale | blocked` from that host's own branch copies; `seat` is the seat names the launcher recorded (a placeholder such as `rpg (seat not recorded)` is made when the
  Seat is shown and never stored; a filing segment gives no seat); `domain` comes from every branch the host has. A host with no copy of the ticket has no segment. A malformed segment is skipped with a finding.
- **Holder:** a host with a segment on the item, in any state. A host that wrote its segment with P1c code (a `Branch` entry and no segment) counts as a holder through a **legacy segment**, derived on read, never written,
  never for the host running the sync. While one exists, Seat and Domain keep their current entries and add this host's (they do not shrink until that host writes its own segment).
- **Status** from the union: Blocked if any segment is blocked (origin's BLOCKED copy counts only when no host holds the ticket); Stale only when every non-filing segment is stale; In progress when any is progress or stale; else To do.
  `stale` is set only by the host that wrote it, from its own branches' age.
- **Seat and Domain** are the sorted union of the segments, and shrink when a host drops its segment.
- **Title, Tier, Layer, Priority, Tags, Epic, Body:** no holder: origin's copy. One holder that is this host: its own copy. One holder that is another host: keep the current value (origin's copy if there is no item yet).
  Two or more holders: origin's copy if origin has one, on every host; with no origin copy only the holder with the lowest host tag (string sort) writes its own copy and the others keep the current value. The plan prints a note naming the rule.
- **Archive guard:** "no ticket file for this ID" never archives an item that carries another host's segment (or a legacy entry); it prints a finding naming the host.
- **Known gaps:** a host that stops running leaves its segment saying `progress`; the stale-host flag that would catch it is P3. Until u24 runs P2 code, u24's Blocked and Stale cannot be seen from ubuntu. So when this host has no copy of a ticket and every other holder is a legacy segment, Status stays the item's current value
  (Done and In review from origin still win); it clears when u24 writes its own segment. **Limit: with only legacy u24 segments, Status freezes until u24 runs P2 code**; the hold on u24 `--apply` lifts only after u24's first P2 `--apply`, which should follow soon after P2 lands on main. If this host has its own segment, the normal union applies. The current Status is never copied into a legacy segment's state. P1c code reads `v3:` as an unknown version, so a P1c-code dry run reports a hand edit on every v3 item; do not run `--apply` from a checkout on P1c code.
  Hiding `Host facts` in the Project views is an owner step in the view settings (the API cannot do it); the sync does not depend on it.

## All lanes, Domain, `--fetch`, last run and heartbeat (P3b)

- **All lanes.** The sync no longer filters by `pilot_lanes` (the key stays in `registries/session_project.yaml` and is ignored). Every ticket
  on any host's branch, every ticket in `todos/` or `inprogress/` on `origin/main`, and every existing item is a candidate. A Done ticket that
  only `origin/main` holds still gets no new item (no mass Done creates); `pilot_start` and `done_window_days` apply as before.
- **Domain is a single-select** with one option per registered domain (`registries/session_roles.yaml`) plus `unassigned` and `unknown`. `--init`
  renames the old text field to `Domain (old)` and creates the select; it never deletes anything (deleting `Domain (old)` is a separate owner
  ask once P3 is proven). A second `--init` prints "left alone". After the rename the first run reads the old values from `Domain (old)` for the
  hash check, so it prints no false hand edits and plans only the Domain writes.
- **Where a ticket's Domain comes from**, first match wins: (1) the domain recorded for a branch copy on any host (`Host facts`); (2) the owner
  of the code the ticket names: the repo paths in `## Related Code Areas` (globs and braces skipped), each routed through
  `tools/sessions/route.py` on the loaded roster; when every owned path gives the same domain, that is the Domain (not a guess); (3)
  `unassigned`. Never from `layer`. A branch name's domain is the longest registered domain followed by `-` (`agent-working-x` is
  `agent-working`, not `agent`); no match is `unknown`. Two hosts naming different domains: the sorted first, with a finding.
- **`--fetch`** runs `git fetch origin main` first (60 s timeout). On failure or timeout the run carries on, adds a finding and prints the age of
  `origin/main`. The plan header says `fetched`, `fetch FAILED` or `no fetch` to match what happened. The read-only guard still refuses every other git write.
- **`last-run.json`**: every `--apply` (any outcome) writes `~/.local/state/rpg-project-sync/last-run.json` (mode 600): UTC time, host, rc,
  steps done and left, the first error (redacted), the heartbeat result, stale hosts and `failed_streak`. A dry run writes nothing. The
  SessionStart hook prints one line when the last two runs failed.
- **Heartbeat.** One draft item `_sync heartbeat` (no Ticket ID, no Status) holds a `Last run` text with one segment per host
  (`u24desktop: 2026-11-15T10:00Z rc=0`). Each `--apply` rewrites only its own segment, as the last step, in one paced attempt with no retry; a
  failed write prints `heartbeat: not written (...)` and changes neither rc nor the first error. It is written on every `--apply`, even when
  nothing else changed (one mutation per run buys an honest liveness signal). Any other host older than `stale_host_hours` is reported as
  `stale-host:` in the output and the last-run file; this only reports. The item is never archived and never counted as a ticket. Two heartbeat
  items (a create race) are all read, the first is written, a finding names the extra, and the owner removes it by hand (a delete, through the
  lead). To keep it out of the board views the owner filters views 1-4 by hand in the UI: try `has:status` first (the sync sets Status on every
  ticket item and never on the heartbeat), else `-title:"_sync heartbeat"`.
- **Limits.** (a) The SEQUENCE.md filing-seat rule was dropped: no reliable carrier (4-5 of 6 name a filer in free text; 140 flat todos sit in no
  folder). Tickets whose named code has no single owner stay `unassigned` (37 of 161 on 2026-11-15: 21 mixed, 10 with no path, 6 not routed). The run's `domain: N tickets unassigned` note counts every candidate, existing items included, so it can be larger than the `unassigned` creates.
  (b) Both hosts get the same Domain from the code areas only when they run on the same roster; with different checkouts the last writer wins
  until both are on the same `origin/main` (as for the content rule). (c) **Never run `--apply` on pre-P3b code, on either host, once the
  heartbeat exists**: P1c and P2 code archive "an item with no Ticket ID", so the heartbeat would be lost. A pre-P3b dry run showing `archive
  _sync heartbeat` is expected, not a finding. (g) The sync sees only branches checked out in a worktree on this host; a branch with no worktree (parked) falls back to main's copy, so the plan can change when a branch is checked out or removed. (d) `Domain (old)` stays on the board until the owner asks for it to be deleted. (e) **Tier** is the leading token of the ticket's `## Tier` line (`standard (provisional)` is `standard`); anything else outside hotfix/standard/epic is a finding and Tier is left empty. (f) A live dry run checks every select value the plan would write (Status, Tier, Layer, Priority, Domain) against the live field's options and prints `finding: apply would refuse: <id> <field> '<value>'` for each; `--apply` runs the same check before its first mutation and refuses (rc 2, nothing written), naming all of them.

## Filed date and the Backlog view (`TCK-20261115-PROJECT-SYNC-FILED-DATE-AND-BACKLOG-VIEW`)

- **`Filed`** is a DATE field that `--init` creates (a second `--init` leaves it alone; an existing `Filed` of another type is refused before any
  write). Its value is the `date:` of the ticket's frontmatter (`YYYY-MM-DD`) from the copy the content rule picks. A missing or invalid date
  leaves the field empty and adds a finding `Filed left empty`. When another host's lower tag holds the content, the current value is kept, as for
  the other content fields. An empty value clears the field.
- **Sync hash v4** is the v3 fields plus `Filed` (`v4:<sha>`). A v1, v2 or v3 item is not a hand edit; its first run writes `Filed` (and the hash)
  once. Pre-v4 code reads `v4:` as an unknown version, so do not `--apply` from a checkout older than this change.
- **Backlog view (owner UI step, no code).** Add a table view on https://github.com/orgs/rpg-sim-lab/projects/1: filter `status:"To do"`, group
  by Domain, sort by Priority and then Filed. For the age of the pile add a filter such as `filed:<@today-30d`; if the UI does not accept that
  syntax, sort by Filed instead. GitHub shows the item count per group, so no count is stored anywhere.
- **Limits.** (a) `Filed` is the filing date, not the last activity: a ticket filed long ago and worked on yesterday still looks old.
  (b) A merged ticket gets a Done item only while some host's worktree still has its branch checked out (seen in P3b AC3.5 on ubuntu, #917), so the
  Done lane is not a full list of recent closes. This is documented only; no code changes it.

## Running on a timer (P3c, `TCK-20261115-PROJECT-SYNC-HOST-TIMER`)

Two templates in `tools/sessions/systemd/` run `project_sync.py --apply --fetch` hourly on each host: `project-sync.service` (a oneshot, so runs
cannot overlap) and `project-sync.timer` (`OnCalendar=*-*-* *:00:00`, `Persistent=true`, `RandomizedDelaySec=60`). u24 runs at :00 and ubuntu
at :30. **No seat installs, enables or starts either unit; the owner does, on each host.**

- **Standing approval.** Installing the timer on a host is the owner's standing approval for unattended `--apply` writes to Project 1 from
  that host (owner decision #715 6881411615, item 1). Removing it withdraws the approval.
- **Caps.** `Nice=19`, `IOSchedulingClass=idle`, `CPUQuota=25%`, `MemoryMax=256M`, `TimeoutStartSec=15min` (a hung run is stopped).
  `ExecCondition` skips a run when `MemAvailable` is below 1 GB: `awk` exits 1, which systemd treats as a **skip** (exit codes 1 to 254 of an
  `ExecCondition` skip the unit without failing it; 255 or a signal is a failure). A skipped run leaves `last-run.json` as it was.
  `CPUQuota` and `MemoryMax` need the `cpu` and `memory` controllers delegated to the user manager (u24 has both; check on ubuntu with
  `cat /sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/cgroup.controllers`); without them the two caps are ignored and
  `Nice`, the idle I/O class and the timeout still hold.
- **HOST FREE exemption.** The timer does not wait for a host's HOST FREE slot. One run measured 43 s, 38 MB and about 0.5 CPU on 2026-11-15
  (P3b load, u24), far under the caps above.
- **Preconditions.** (1) Install only on code at or after the current `origin/main`, never older code once the heartbeat exists: pre-P3b code
  archives the `_sync heartbeat` item, and pre-v4 code rewrites every hash (amendment B). (2) The main checkout must sit on `main`; the sync reads
  git refs, not the working tree, but `--fetch` runs `git fetch origin main` in `WorkingDirectory`, so that must be a checkout with a working
  `origin` and credentials a user service can reach (no ssh agent in a user unit: use an unencrypted key or an https credential helper). A
  failed fetch is not fatal: the run adds a finding and uses the old `origin/main`. (3) The token file `~/.config/rpg-project-sync/token` (mode
  600) must exist for that user; the templates name no token path or value. (4) **`gh` auth.** The sync reads open PRs with `gh pr list`. If `gh` cannot answer inside the
  user service, every `--apply` refuses with rc 1 (`open PRs unknown, nothing written`) and the SessionStart line warns after 2 runs. That
  happens when the `gh` token sits in the system keyring and no login session or D-Bus unlocks it. Check with `gh auth status`: the token must
  come from `~/.config/gh/hosts.yml` (as on u24) or from `GH_TOKEN` in a drop-in. The owner checks this on ubuntu before installing.
- **Install (per host, by the owner).** `@REPO@` is the host's main checkout (u24: `/mnt/data/Working/rpg-based-simulation`; ubuntu: its own path).
  ```
  REPO=/path/to/the/main/checkout
  mkdir -p ~/.config/systemd/user
  for u in project-sync.service project-sync.timer; do sed "s|@REPO@|$REPO|g" "$REPO/tools/sessions/systemd/$u" > ~/.config/systemd/user/$u; done
  systemd-analyze --user verify ~/.config/systemd/user/project-sync.service ~/.config/systemd/user/project-sync.timer
  # ubuntu only: stagger to :30 with a drop-in
  mkdir -p ~/.config/systemd/user/project-sync.timer.d
  printf '[Timer]\nOnCalendar=\nOnCalendar=*-*-* *:30:00\n' > ~/.config/systemd/user/project-sync.timer.d/stagger.conf
  systemctl --user daemon-reload
  systemctl --user enable --now project-sync.timer
  loginctl enable-linger "$USER"      # so the timer runs with no login session
  ```
- **Read it.** `systemctl --user list-timers project-sync.timer` (next and last run), `journalctl --user -u project-sync` (progress lines, the
  `applied N step(s)` line, the exit status), and `~/.local/state/rpg-project-sync/last-run.json` (rc, steps, `failed_streak`; the SessionStart
  hook warns after two failures in a row). A skipped run shows `Condition check resulted in ... being skipped` in the journal.
- **Stop it.** `systemctl --user disable --now project-sync.timer`; delete the two files in `~/.config/systemd/user/` to remove it (a delete is
  the owner's).
- **Limits.** (a) A host that is off at :00 runs once on the next boot (`Persistent=true`), at most one catch-up run. (b) A primary rate limit
  stops a run at once and the next hourly run carries on; two failed runs in a row show up in the SessionStart line. (c) **The 15 min timeout stops a large rewrite.** The FILED-DATE load took 15m22s, so a mass rewrite (a first load, a new field or
  a hash-version bump) runs by hand first, as the P3b and FILED-DATE loads did, then the timer only carries deltas. A killed run is safe: writes
  reconcile and the next run carries on. But `project_sync.py` handles no signal, so a run stopped by the timeout (SIGTERM) writes no
  `last-run.json` (the previous file stays) and no heartbeat (both are written only when the run ends). (d) Not measured yet: how
  the two hosts interact over many hourly runs; AC3 of the ticket reads the first runs back after the owner installs.

## Seat, linking by commit subject, Involved, Blocked by, Hotspot (`TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED`)

Hash `v5` adds three text fields to v4: **Involved**, **Blocked by**, **Hotspot**. `--init` creates them; a v4 item is rewritten once and is not a hand edit.
Measured basis, taken on origin/main 77e4aeb72 and its filing-commit descendant 84b44272c (the only difference is two ticket files, and the Hotspot counts were
re-checked on both and are identical): the live Project had 328 items; 47 showed "seat not recorded", 19 of them not Done.

- **(a) Seat of a hand-added worktree.** `python3 tools/sessions/record_seat.py <worktree> <seat> [--replace] [--dry-run]` writes the record `launch.py --worktree`
  writes (it calls `state.write_bound_worktree(..., explicit=True)`; `status.py` shows it as `writing in`). It refuses an unknown seat, the main checkout or a path that
  is not a linked worktree, a worktree already recorded for another seat, and a seat whose record points at a different live worktree. It never guesses a seat from a
  branch name. **The record holds ONE worktree per seat**: a seat that runs two lane worktrees can record one of them (`--replace` moves it). Each host records its own
  worktrees; a u24 seat runs the one-time backfill for the u24 lane worktrees (the CLI is not run for another host's worktrees).
- **(b) A branch works a ticket by its commit subjects.** In a worktree's own commits (`git log --no-merges HEAD --not origin/main`, so a commit already on origin/main
  never counts), a ticket is *worked* when its id LEADS a subject and that commit touches a file outside `agent-working/` and `docs/`. Anything else is *cited*: an id in
  the middle of a subject, a filing/notes commit, a docs-only commit. A worked ticket reads In progress through the same path a changed `inprogress/` ticket file does
  (Stale and the seat follow); a ticket already Done on origin/main, or with no file there, is skipped. A cited ticket changes no Status. The edge is pinned in both
  directions: a commit touching only a `tests/` config is worked, the same commit touching only `docs/` is cited. A wrong guess shows the wrong Status until the next
  sync. Only checked-out worktrees are read, as for every other branch fact; `origin/*` branches nobody has checked out here are not.
- **(c) Involved** is the set of seats recorded for the worktrees whose own commit subjects name the ticket (worked or cited) plus the seats of a branch that changes its
  file, unioned across hosts through `Host facts` (`involved=`). Basis: on ubuntu 9 of 11 worktree branches with ticket facts have a recorded seat; of 32 tickets named by
  such a branch, 3 have two or more seats. A worktree with no recorded seat adds nothing, so **Involved is empty for lane branches with no recorded seat until the
  `record_seat.py` backfill runs on u24**. Comment parsing is not shipped: in the last 100 #715 comments (2026-10-22..2026-10-26) 38 name a ticket id and none starts
  `<seat>, <date>:` (0%); the openers are `approval: ...`.
- **(d) Blocked by** lists the ticket ids on a line-start `waits on`, `waiting on`, `blocked by` or `depends on` line of the ticket that are not Done on origin/main; an id
  with no ticket file there is left out with a finding. Only 1 of 223 open tickets has such a line today. **Parked is not derived.** `Blocked` itself comes from the
  ticket's `## Status` body line reading `BLOCKED` (`parse_copy`: `blocked = section("Status").upper() == "BLOCKED"`), so a Parked-like ticket shows today as a ticket
  Status of BLOCKED plus a waits-on line naming the ticket it waits for. A branch that is old because it waits on something (the STALEMATE F1 shape) **still reads Stale**
  after this ships. Parked is deferred to `TCK-20261119-PROJECT-VIEW-PARKED-STATE-FROM-A-TICKET-BODY-MARKER-LINE`.
- **(e) Hotspot** is, of the `src/*.py` files in the ticket's own `## Related Code Areas`, the one cited by the most open tickets (todos and inprogress) on origin/main, empty when
  none is cited by 2 or more tickets; ties break by path order; directories and non-`src/` paths never count. On 77e4aeb72: 123 open tickets cite a src `.py` file, 152
  distinct files, 57 cited by 2 or more; top `intelligence.py` 19, `tactical.py` 13, `kernel.py` 12, `core/state.py` 12.

Every new derivation prints ran / skipped / errored in the dry-run notes (`subject-link: ...`, `hotspot: ...`); a lookup that fails leaves the field empty and adds a finding. An
update line shows the new Involved / Blocked by / Hotspot value next to the changed-field name. Exit code and `--apply` behaviour are unchanged for the existing fields.

### Limits, the u24 dry run, and the live write after this lands (same ticket)

- **A squash-merged branch kept as a worktree.** `--not origin/main` cannot tell a squash-merged branch's commits from live ones, so before a worktree's subject links are
  used, `gh pr list --state merged --head <branch>` (the read-only `pr list` the guard already allows) is asked once per branch that has a worked-by-subject ticket not already
  in its changed files; a merged PR means its subject links are skipped (counted in the `subject-link:` note), and a failed lookup links nothing and adds a finding. Measured on
  the 16 branch-only citations: they sit on 26 branches (local and origin); 6 of those branches have a merged PR (including `rpg-ubuntu-group-id-alloc-impl`, which carried
  one of the five tickets the rule would otherwise have moved), 20 do not, 0 lookup errors. Cost: a branch name reused after its PR merged, with new commits, is skipped too.
- **Reading only checked-out worktrees.** On ubuntu `subject-link` links 0 tickets (it reads 16 worktrees; the candidate branches are `origin/*` refs nobody has checked out
  here). Reading remote branches is `TCK-20261119-PROJECT-SYNC-READS-REMOTE-BRANCHES-NOT-ONLY-CHECKED-OUT-WORKTREES` (not started here). The coin fix, STALEMATE F1 and #965
  cannot be read from ubuntu.
- **The u24 dry run (a u24 seat runs it; its moved list goes to lead-planner and agent-working-planner before any live write).** On the u24 host, from its repo checkout:
  `python3 tools/sessions/project_sync.py --root . --fetch` (read only: git verb allowlist, `gh pr list` and `gh api repos/...` reads, a live Project read). To rehearse the
  seat backfill without touching live records, use a scratch seat-state root: `mkdir /tmp/seat-scratch`, then for each lane worktree
  `python3 tools/sessions/record_seat.py --state-root /tmp/seat-scratch <worktree> <seat>`, then
  `python3 tools/sessions/project_sync.py --root . --state-root /tmp/seat-scratch`. The dry run prints `seat state root: <path> (--state-root)`; both flags require an
  existing directory (a missing one exits 2, never a fallback to the real root), `project_sync` only reads it, and `record_seat` writes only under it. Compare the coin
  fix, STALEMATE F1 and #965 rows against the before run (`git archive origin/main` of the old tree) on the same origin/main SHA.
- **Seat names.** `record_seat.py` accepts only roster seats (`registries/session_roles.yaml`). The ticket names `rpg-implementer-2` / `rpg-implementer-3` as the owners of
  `m1kind5` / `coinsink`; the roster here holds `rpg-implementer` and `rpg-implementer-ubuntu` and no `-2` / `-3`, so those two names would be refused as unknown seats. The u24
  backfill must use a roster seat name, or the roster gains the seats first (a decision for rpg-planner / lead-planner).
- **Lanes left "seat not recorded".** With one recorded worktree per seat, a u24 seat with N lane worktrees leaves N-1 unrecorded. The count is unmeasured: it needs the list of
  the ~15 u24 lane worktrees and the seat each belongs to, which only the u24 host has; a u24 seat can print it with `git worktree list` against the `record_seat.py` results.
- **The hash bump rewrite.** The ubuntu dry run plans 314 updates and 1 create: about 900 field writes (changed fields plus `Source` and `Sync hash` per row), so at the 1 s
  write pacing at least about 15 minutes (the FILED-DATE load of 328 items took 15m22s). Run it by hand first, not on the timer. A secondary rate limit is waited out; a primary
  one stops the run, and the next run reconciles (the partial item shows "hand edit" lines that the rerun overwrites).
- **The live write is a step after this lands, not a code deliverable.** Once the code is on main: (1) a u24 seat runs the dry run above and shows the three owner cases correct;
  (2) its moved list goes to lead-planner and agent-working-planner; (3) the owner logs a yes; (4) `python3 tools/sessions/project_sync.py --init` (creates Involved,
  Blocked by, Hotspot), then `--apply` by hand.

### Filing copies, the order of the first live run, and what stays incomplete (`TCK-20261119-SUBJECT-LINK-FOLLOWS-A-TICKET-FILED-ONLY-ON-AN-UNPUSHED-BRANCH`)

- **A ticket filed on an unpushed branch and worked on a lane branch.** When origin/main has no file for a ticket a worktree works by subject, the link reads this host's own
  filing copy (a changed `todos/` or `inprogress/` file found on any worktree of the host), so the ticket reads In progress with the lane branch's seat. An id with no file on
  origin/main and none on this host stays unlinked and is named in the `subject-link:` notes; a ticket Done on origin/main stays Done; a cited-only or docs-only branch changes
  nothing; a host without the filing copy writes no fact for it from the subject link alone (it reads the other host's segment and agrees).
- **A host that only cites a ticket reads origin's copy.** A branch whose commit subjects merely name a ticket gets an Involved entry and no domain, and never blanks the ticket's
  Title / Tier / Layer / Priority (an earlier cut did, on Done rows; the dry run's `grep -c "Title, "` is the check, 0 after the fix).
- **The order of the first live run (one order for the owner).** `--apply` refuses before its first write when the Project lacks Involved, Blocked by or Hotspot ("run --init first",
  exit 2): the hourly timer then fails every tick and the board freezes. The OLD code run against a Project that already has the three fields prints the same plan, no hand edits
  and exits 0 (tested on origin/main 77e4aeb72 with synthetic items), so `--init` before the code lands is safe. Each host's sync is lock-free across hosts (they write separate
  `Host facts` segments) but one `--apply` per host at a time is now enforced by a non-blocking lock (`~/.local/state/rpg-project-sync/apply.lock`; a second apply exits 0 with
  "another --apply is running", so a hand-run apply and a timer tick on one host cannot write together). The order, on each host with a timer (`project-sync.timer`; ubuntu's commands
  below, u24's are lead-planner-u24's to run, relayed by lead-planner):
  1. stop the timer: `systemctl --user stop project-sync.timer`;
  2. whoever holds the sync token on that host (`~/.config/rpg-project-sync/token`, mode 600, never printed or copied) runs, once for the whole Project, from the main checkout:
     `python3 tools/sessions/project_sync.py --init` (creates exactly Involved, Blocked by, Hotspot; changes no Status option; a second `--init` reports nothing created);
  3. the owner lands the PR, and each host fast-forwards its main checkout (`git pull --ff-only`);
  4. the token holder runs the first apply by hand, one host after the other: `python3 tools/sessions/project_sync.py --apply --fetch` (the first run rewrites about
     314 rows, see the count below; a secondary rate limit is waited out and a primary one stops the run, then the next run reconciles);
  5. start the timer again: `systemctl --user start project-sync.timer`.
  A stop in the middle (including the unit's 15-minute `TimeoutStartSec` SIGTERM) leaves the item it stopped in with new values and the old Sync hash; the next run prints `hand edit:` lines for
  that item. Those lines are findings printed next to the plan, not extra rewrites: the item is rewritten by the normal update the same run plans anyway.
- **First-run size.** The dry run on origin/main 77e4aeb72 plans 314 updates and 4 creates: about 813 field writes (changed fields plus `Source` and `Sync hash` per row, one more for a
  changed Title), at least about 14 minutes at the 1 s pacing.
- **What stays incomplete after it lands.** STALEMATE F1 is parked and will read In progress, not Parked, until `TCK-20261119-PROJECT-VIEW-PARKED-STATE-FROM-A-TICKET-BODY-MARKER-LINE`
  ships; #965's seat (an instance of a multi-session role) shows "not recorded" until `TCK-20261119-RECORD-SEAT-ACCEPTS-A-SESSION-INSTANCE-OF-A-MULTI-SESSION-ROLE` ships.

### Instance seats (`TCK-20261119-RECORD-SEAT-ACCEPTS-A-SESSION-INSTANCE-OF-A-MULTI-SESSION-ROLE`)

- **Accepted names.** `record_seat.py <worktree> <seat>` takes a roster role or an instance `<role>-<n>` with 2 <= n <= that role's `placement.max_sessions`. On this base
  that is `rpg-implementer-2..-4` and `rpg-implementer-ubuntu-2..-4` (both roles have `max_sessions: 4`; every other role has 1, so `rpg-planner-2` is refused). Refused as unknown
  seats: `-0`, `-1`, `-5`, a non-numeric or zero-padded suffix, a suffix on a one-session role. The bound is read from the roster, not copied.
- **Stored and shown exactly as given.** The record's key is the instance name (`<state root>/rpg-implementer-3/worktree.json`, the file `launch.py rpg-implementer-3 --worktree` already
  writes: no format change, no `state.py` change); nothing is written under the base role. `status.py` shows an instance row only when it has an explicit record, and
  `project_sync` names the instance as the Seat and in Involved.
- **One record per instance; one seat per worktree.** Two instances of one role can each hold a worktree. A worktree already recorded for any other role or instance is refused,
  in both directions (a base role onto an instance's worktree and the reverse); a seat with a live record for a different worktree needs `--replace`.
- **Precedence when both exist.** The launcher can write a base-role record and an instance record over time. The readers show the instance only: it is more specific than its own
  base role, so one worktree reads `rpg-implementer-3`, not both. A different role's instance does not displace the base role. Only an explicit record counts (a non-explicit one is
  the launcher's default path, not a batch worktree).
- **Count what exists today.** `python3 tools/sessions/record_seat.py --list` (read only; add `--state-root DIR` for a scratch root) prints every explicit record, role or instance, by its
  own name with `live` or `missing`, and the number of records. Run it on each host. ubuntu, measured on this base: 1 instance-keyed record, `rpg-implementer-ubuntu-2`, explicit and live
  (worktree `rpg-ubuntu-2`); it becomes visible with this change, so the first tick changes exactly one row on ubuntu (a Done ticket's Seat, Host facts and Involved; before/after dry run on
  origin/main ea3d374d0: 1 changed row). u24's count is not measured here; have a u24 seat run the same command.
- **The u24 backfill (a u24 step, run by lead-planner-u24 after this lands).** For each known lane worktree: `python3 tools/sessions/record_seat.py <worktree> <instance>` with the instance
  named by the owner of the lane (for example `m1kind5` -> `rpg-implementer-2`, `coinsink` -> `rpg-implementer-3`; rpg-planner confirms the rest), first with `--dry-run`, then
  `python3 tools/sessions/project_sync.py --root . --state-root <scratch>` to read it back. A lane whose seat already holds a different live worktree is refused without `--replace`.
- **No new field and no init step.** Seat and Involved already exist; merging this changes only the Seat and Involved text of rows whose worktree has an instance record.
