---
status: active
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20261115-PROJECT-SYNC-HOST-TIMER
phase: open
date: 2026-11-15
tags: [planning, delivery]
---

# TCK-20261115-PROJECT-SYNC-HOST-TIMER

## Title
`project_sync.py` P3c: systemd user timer templates that run the sync hourly on each host, capped and staggered, with the owner's install step documented

## Status
OPEN

## Tier
hotfix

## Type
feature

## Priority
P2

## Request Summary
Child P3c of TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW.
- **Owner decisions:** #715 6881411615.
  - Item 1, "Accept all (Recommended)": an hourly systemd user timer on each host, staggered with u24 at :00 and ubuntu at :30,
    capped, exempt from HOST FREE, fetching on every run, with linger enabled.
  - Item 3: P3c follows P3b.
- **Installing the timer is the owner's standing approval for unattended `--apply` writes to Project 1 from that host.** The owner
  installs it on each host. No seat installs, enables or starts it.
- **Order:** dispatch only **after P3b (TCK-20261115-PROJECT-SYNC-ALL-LANES) merges** and its first load is done, so the timer's
  first run writes only deltas.
- **Tier:** hotfix, because there is no Python logic: two unit templates, a doc section and a test of the template text.

## Scope
1. **Templates** in `tools/sessions/systemd/`:
   - **`project-sync.service`:**
     - `Type=oneshot`;
     - `WorkingDirectory=` the main checkout;
     - `ExecStart=` the repo `.venv` python running `tools/sessions/project_sync.py --apply --fetch`;
     - `ExecCondition=` a one-line check that skips the run when `MemAvailable` is below 1 GB (a skip is not a failure);
     - `Nice=19`, `IOSchedulingClass=idle`, `CPUQuota=25%`, `MemoryMax=256M`;
     - `TimeoutStartSec=` about 15 min, so a hung run is stopped.
   - **`project-sync.timer`:** `OnCalendar=*-*-* *:00:00` for u24 and `*:30:00` for ubuntu. The doc gives the per-host line, or an
     override drop-in. Also `Persistent=true` and `RandomizedDelaySec=60`.
   - systemd's oneshot unit keeps runs from overlapping.
2. **Docs:** a new "Running on a timer" section in `docs/guidelines/session_roles/project_sync_dry_run.md`:
   - the owner's install commands per host: copy to `~/.config/systemd/user/`, `systemctl --user daemon-reload`,
     `systemctl --user enable --now project-sync.timer`, and `loginctl enable-linger $USER`;
   - how to read it: `systemctl --user list-timers` and `journalctl --user -u project-sync`, plus the last-run file from P3b;
   - how to stop it: `systemctl --user disable --now project-sync.timer`;
   - the HOST FREE exemption and why: one run is about 43 s, 38 MB and about 0.5 CPU, measured 2026-11-15;
   - the standing-approval sentence.
3. **Tests, no network** (about 3):
   - the templates parse as INI and carry each cap;
   - ExecStart names `--apply --fetch` and the repo venv;
   - no template contains a token path or a token value.

## Out of Scope
- Installing, enabling or starting the timer on any host. The owner does that.
- Any change to sync logic. That is P3b.
- cron or a SessionStart hook (rejected in the options draft).

## Acceptance Criteria
1. Scope items 1-3 are built, and the scoped tests pass.
2. `systemd-analyze --user verify` passes on both templates on u24. This is read-only and installs nothing.
3. After the merge, the owner installs on u24 and on ubuntu. The first timer run on each host must show rc 0 in the journal and in
   the last-run file, and a later dry run must show nothing to do. The seat reads these back and does not install.

## Related Tickets
- TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW (parent)
- TCK-20261115-PROJECT-SYNC-ALL-LANES (P3b, goes first)
- TCK-20261114-PROJECT-CLIENT-WRITE-PACING (P3a)

## Related Docs
- `docs/guidelines/session_roles/project_sync_dry_run.md`
- Options draft (main checkout): `.claude/handover/drafts/project-sync-p3-timer-options-2026-11-15.md`

## Related Stored Artifacts

## Related Code Areas
- `tools/sessions/systemd/` (new), `tests/tools/`

## Assumptions / Open Questions
- **Simpler-fix check (6698958617):** the owner could write the unit by hand from the doc, with no templates in the repo. That costs
  no code, but the caps and stagger then drift per host. With templates, both hosts run the same caps, and a test guards them.
- The epic closes when P3 runs on both hosts (epic AC3).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
