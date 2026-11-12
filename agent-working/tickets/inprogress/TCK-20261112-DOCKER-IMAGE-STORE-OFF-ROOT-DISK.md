---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261112-DOCKER-IMAGE-STORE-OFF-ROOT-DISK
phase: inprogress
date: 2026-11-12
tags: [platform]
---

# TCK-20261112-DOCKER-IMAGE-STORE-OFF-ROOT-DISK

## Title
Plan moving Docker's containerd image store off the root disk, so builds and image layers stop filling /

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Owner yes, 2026-11-12 (#715 6828616413): file a ticket that PLANS moving the image store off `/`.

Facts, checked by platform-planner on 2026-11-12:
- Docker 29.3.1 runs with the containerd image store: `docker info` shows driver-type `io.containerd.snapshotter.v1`. `/etc/docker/daemon.json` holds only `"data-root": "/data/docker"`, so volumes and Docker's own state live on `/data`.
- Image content, snapshots and the build cache live under containerd's root, which defaults to `/var/lib/containerd` on `/` (/dev/sda2, 49G). `/etc/containerd/config.toml` sets only `disabled_plugins = ["cri"]` (no `root`).
- `/` reached 100% on 2026-11-11, which is the root cause of TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE. It needed two `docker builder prune` runs from the owner.
- One backend build costs about 1.4 GB of cache plus 0.25 GB of image (docker system df, 2026-11-12 run record).
- Now: images 7.425 GB, build cache 2.039 GB, volumes 666.8 MB. `/` is at 73% (13G free), `/data` at 84% (16G free).

## Scope
Planning only. The deliverable is a runbook `docs/runbooks/docker-image-store-move.md`, plus this ticket's staging artifacts.
1. Compare two options, with sources (Docker and containerd docs for 29.x):
   - A: set containerd's `root` to `/data/containerd` in `/etc/containerd/config.toml`, then stop docker and containerd, copy the old root, and start them again;
   - B: turn off the containerd snapshotter (`"features": {"containerd-snapshotter": false}` in daemon.json), so images use the classic graph driver under data-root `/data/docker`. Existing images then become invisible and need re-pulling or rebuilding.
   Also state which one Docker 29 supports long term.
2. Space: the owner measures what moves (`sudo du -sh /var/lib/containerd`) against `/data`'s free space (16G, and an 85% working gate). Say what to prune first, and in what order, so the move fits.
3. Restart impact:
   - which containers stop, and their restart policies;
   - on 2026-11-12, `docker ps -a` showed only `cool_curie` (github-mcp-server, running) plus one exited unnamed container, and no `portal-*` containers;
   - re-check this at planning time, and name the owner-facing effects (the MCP server restarts).
4. Every privileged command is written as plain shell for the owner to run (no `!` prefix). No agent runs sudo, edits `/etc`, or restarts docker or containerd.
5. A dry check afterwards: `docker info` shows the new root or driver, `docker images` lists the images (option A) or is re-pulled (option B), the `/data/docker/volumes` mountpoints are unchanged, and `df` shows `/` freed.
6. A rollback for each option (revert the config, restart, keep the old directory until verified), plus a point after which the old data is deleted (the owner's call).

## Out of Scope
- Running any of it: the restart is a separate owner yes plus timing (lead-planner, 2026-11-12).
- Deleting anything on `/` (the owner's).

## Acceptance Criteria
- The runbook names a recommended option with sources, a measured space plan, the restart impact, owner-run commands, a dry check and a rollback (validated: review by platform-planner, then lead).
- No command in the runbook prints or puts a secret on argv (validated).

## Related Tickets
- TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE (done; the incident).
- TCK-20261020-DISK-FILL-ALERT-TUNING (parked; host-disk alerting).

## Related Docs
docs/runbooks/disk-space.md
docs/runbooks/records/2026-11-12-loki-volume-and-api-dashboard.md

## Related Stored Artifacts
agent-working/stored_artifacts/TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE/run-2026-11-12/

## Related Code Areas
docs/runbooks/disk-space.md

## Assumptions / Open Questions
- Agents can't read `/var/lib/containerd` (it's root-only), so its size has to come from the owner.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
