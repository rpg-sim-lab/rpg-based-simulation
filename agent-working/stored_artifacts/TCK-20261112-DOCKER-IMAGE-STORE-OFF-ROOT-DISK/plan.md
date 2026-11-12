---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261112-DOCKER-IMAGE-STORE-OFF-ROOT-DISK
phase: plan
date: 2026-11-12
tags: [platform]
artifact_type: plan
---

# Plan: TCK-20261112-DOCKER-IMAGE-STORE-OFF-ROOT-DISK

Standard tier, **planning only**. The deliverable is the owner-run runbook `docs/runbooks/docker-image-store-move.md` plus this ticket's staging artifacts. Findings and sources: `investigation.md`. No privileged command is run by an agent, nothing under `/etc` is edited, docker and containerd are not restarted, and nothing in `/var/lib/containerd` or `/data/docker` is read. The restart itself needs a separate owner yes and timing.

## Recommendation

**Option A: set containerd's `root` to `/data/containerd`.** It is the method Docker's own daemon documentation gives for relocating the containerd image store; it keeps every image; it frees `/` for good; it stays on the store Docker 29 now defaults to. Option B (snapshotter off) hides images, needs a re-pull or rebuild of all of them, and does not free `/`; it is kept in the runbook as the fallback if `/data` cannot be given room.

## The first precondition: room on `/data`

With the owner's 7.2G (`sudo du -sh /var/lib/containerd`, 2026-11-12) the move takes `/data` from 83.35% to 91.04% by `df` (79.51% to 86.85% by Loki's formula): above our 85% gate, and 3.1 GiB under Loki's 90% line. So the runbook's step 0 is to free **at least 5.7 GiB** (to land at 85%) and, recommended, **about 10.3 GiB** (80%, room for builds) on `/data` BEFORE the move. The readable, re-creatable candidates sum to about 6.5 GiB (`.npm`, `tmp`, `aw-pytest-tmp`, `playwright-browsers`): that clears the floor but not the target; the remainder is the owner's call (worktrees, sweep outputs, other projects), and the runbook only lists sizes. If the floor cannot be reached, the plan's honest answer is that `/data` needs more room first. Pruning on `/` before the copy (`docker builder prune`, `docker image prune -a`) shrinks what moves.

## Runbook contents (done in this ticket)

1. Why; the option table; the facts at planning time.
2. **Restart impact**, with platform-planner's wording: currently only `cool_curie` (github-mcp-server) on this engine, owner to confirm nothing else, re-run `docker ps -a` just before the restart. Added: restart policy `no` and live restore off, so it does not come back by itself; the window is minutes; do not start during a build or a stack run.
3. Step 0 room and prunes; step 1 pre-checks; step 2 stop (socket first); step 3 copy with `rsync -aHAXS --numeric-ids`, kept original, dry-run verification; step 4 config edit with a backup and a check for `[table]` headers, then the old root is renamed, not deleted; step 5 start; step 6 dry checks (`containerd config dump`, `docker info`, `docker images`, volume mountpoints, `df`) and an end-to-end test; step 7 bound the build cache (`builder.gc` in `daemon.json`, then `docker builder prune --keep-storage`, plus the pre-run `df` gate); step 8 free `/` later.
4. Rollback for A (one rename and the config backup) and for B (restore `daemon.json`).
5. Every privileged command is plain shell, one per line, no `!` prefix, nothing joined with "then", no secret on any line.

Also: a pointer from `docs/runbooks/README.md` and from `docs/runbooks/disk-space.md`.

## What is not claimed

- The copy method (`rsync -aHAXS`) and `containerd config dump` as the check are standard practice, not documented by containerd; the dry checks verify the result.
- Whether `builder.gc` in `daemon.json` applies under the containerd image store is not documented: step 7 tests it and names the fallback.
- `"containerd-snapshotter": false` is an inference from Docker's general `features` rule.
- No statement on the long-term support of the classic driver was found.
- The plan was not exercised on this host; nothing here was run beyond reading.

## Review

platform-planner first, then lead (the ticket's acceptance). The owner supplies the figures that move: the new `du` after the prunes, and `/data` room on the day.
