---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261112-DOCKER-IMAGE-STORE-OFF-ROOT-DISK
phase: investigation
date: 2026-11-12
tags: [platform]
artifact_type: investigation
---

# Investigation: TCK-20261112-DOCKER-IMAGE-STORE-OFF-ROOT-DISK

Planning only. Nothing was run with privileges, nothing under `/var/lib/containerd` or `/data/docker` was read (both are root-only), no service was restarted. Host facts were read on 2026-11-12 between 15:55Z and 16:15Z with ordinary commands (`docker info`, `ps`, `df`, `stat -f`, `du` on readable paths, `cat` of two non-secret config files). Documentation was read through web fetches; where a page is silent, this file says "not found".

## 1. The host

| fact | value |
|---|---|
| Docker Engine | 29.3.1, Ubuntu 25.10, one context (`default`, `unix:///var/run/docker.sock`), no rootless engine |
| Image store | containerd image store: `docker info` shows Storage Driver `overlayfs`, driver-type `io.containerd.snapshotter.v1` |
| Docker's own data | `/etc/docker/daemon.json` is `{"data-root": "/data/docker"}`; named volumes live there (666.8 MB in 6 volumes; `platform_grafana_data` 599.6 MB, `platform_loki_data` 1.5 MB) |
| Which containerd | the SYSTEM one: `dockerd -H fd:// --containerd=/run/containerd/containerd.sock` and `/usr/bin/containerd` run as root services (`docker` and `containerd` both `active`); this is not the embedded containerd (that is a 29.7.0+ experimental feature) |
| containerd config | `/etc/containerd/config.toml` holds one line, `disabled_plugins = ["cri"]`, and no `root`, so containerd's root is the default `/var/lib/containerd`, on `/` |
| Live restore | `Live Restore Enabled: false` |
| Containers | `docker ps -a`: only `cool_curie` (`ghcr.io/github/github-mcp-server`), running, restart policy `no` |
| `docker system df` (16:13Z) | images 16 (7.425 GB, 1.651 GB reclaimable, 1 in use), build cache 31 entries (2.039 GB, 1.426 GB reclaimable), volumes 666.8 MB |
| `/var/lib/containerd` | **7.2G**, from the owner's `sudo du -sh /var/lib/containerd` (relayed by lead, 2026-11-12, after the owner's prunes; `/` was at 70 to 73%) |
| Filesystems (`stat -f`, 16:13Z) | `/` (/dev/sda2, 49G): 72.04% by `df`; `/data` (/dev/sdb1, 99G): used 78.0 GiB, available 15.6 GiB, 83.35% by `df`, 79.51% by Loki's formula (4.60% of its blocks are reserved) |

One backend build costs about 1.4 GB of build cache plus 0.25 GB of image (the 2026-11-12 run record). The cause of `/` reaching 100% on 2026-11-11 was this store plus two builds' cache (TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE).

## 2. What Docker's and containerd's documentation say

Quotes are short and verbatim from the pages read (all fetched 2026-11-12).

- **Default.** "The containerd image store is the default storage backend for Docker Engine 29.0 and later on fresh installations." (https://docs.docker.com/engine/storage/containerd/). The 29.0.0 release notes say the same; an install upgraded from an earlier version "continues using the legacy graph drivers (overlay2) until you enable the containerd image store" (same page). This host's driver-type shows it is on the containerd store, whichever way it got there.
- **Enable and disable.** Enable: `{"features": {"containerd-snapshotter": true}}` in `daemon.json`, then restart Docker (same page). **Disabling with `false` is not shown on any page read.** The dockerd reference says "The optional field `features` in `daemon.json` lets you enable or disable specific daemon features." So `"containerd-snapshotter": false` is an inference from that general rule, to be checked by `docker info` after a restart.
- **Switching hides images.** "Switching storage backends temporarily hides images and containers created with the other backend"; images from the other backend "remain on disk but become hidden" and reappear on switching back. The docs' advice for moving them: "push them to a registry first, or use `docker save` to export them", and "starting fresh ... is the recommended approach" (containerd page).
- **Where the content is.** "containerd uses a separate storage path from the Docker data directory." The `data-root` option "does not affect image and container data stored in `/var/lib/containerd` when using the containerd image store" (https://docs.docker.com/engine/daemon/). And "containerd's storage is not automatically moved to that location" with "You need to configure containerd's data directory separately to avoid filling your root partition" (containerd page). So `data-root` already points at `/data/docker`, and that is exactly why the store stayed on `/`.
- **How to relocate it (option A's own source).** The daemon page, section "Configure the data directory location": "To change the storage location of containerd snapshotters, use the system containerd configuration file:", followed by an `/etc/containerd/config.toml` with `version = 2` and a top-level `root = "/mnt/containerd-data"`. The containerd man page: `root` is "The root directory for containerd metadata. (Default: "/var/lib/containerd")"; `state` defaults to `/run/containerd`; both are top-level keys before any `[table]`. containerd's own operations guide: "`root` will be used to store any type of persistent data for containerd" and "They should not be tampered with as corruption and bugs can and will happen." Not found: a documented procedure for moving an existing root, and any statement that containerd migrates it. (The "Configure the data directory location" how-to the containerd page links to returned 404.)
- **Two copies of every layer.** "containerd stores images in both compressed and uncompressed formats" (containerd page), which is why the store is larger than `docker system df` shows.
- **Long-term support of the classic driver.** Not found. Neither the containerd page nor the 29.x release notes (read in full) state a deprecation or end of support for overlay2; the dockerd reference still says "`overlay2` is the preferred storage driver for all currently supported Linux distributions, and is selected by default." (That sentence is on the current page; it does not say for how long.) The 29.0.0 notes deprecate cgroup v1, not graph drivers. The deprecated-features page linked from the notes returned 404.
- **Build-cache garbage collection.** "GC is configured in the `daemon.json` configuration file" with keys such as `"builder": {"gc": {"enabled": true, "defaultKeepStorage": "20GB"}}`; policy entries use `reservedSpace`, `keepDuration`, `filter`, `all` (https://docs.docker.com/build/cache/garbage-collection/). That page gives 20GB as the Docker Desktop default and states no default for Docker Engine; it does **not** say whether the `daemon.json` policy applies with the containerd image store. Not found: containerd content GC, and whether `docker image prune` frees containerd's blobs and snapshots (the containerd page only says "Regularly prune unused images with `docker image prune`").
- **Prune commands.** `docker image prune` removes dangling images; `-a` "also remove all images not referenced by any container". `docker builder prune` has `--all`, `--filter until=...`, `--keep-storage` ("Amount of disk space to keep for cache", no unit format shown) and `--force`. `docker system prune` does not touch volumes unless `--volumes` is given, and that flag is described as pruning anonymous volumes (https://docs.docker.com/reference/cli/docker/image/prune/, `.../builder/prune/`, `.../system/prune/`).

## 3. The two options

| | A: move containerd's root to `/data/containerd` | B: turn the containerd snapshotter off |
|---|---|---|
| Change | add `root = "/data/containerd"` to `/etc/containerd/config.toml`; stop docker and containerd; copy; start | `"features": {"containerd-snapshotter": false}` in `daemon.json`; restart docker |
| Images | all kept, nothing re-pulled or rebuilt | hidden, not deleted: every image must be re-pulled or rebuilt (16 here; the backend image costs a build) |
| `/` | freed after the owner deletes the old root | **not** freed by the switch: the hidden images stay on disk in `/var/lib/containerd` until removed another way (no documented way found) |
| `/data` | gains the 7.2G | gains the re-pulled images, unpacked once (smaller than A: no compressed copy) |
| Restart | Docker and containerd (both) | Docker only |
| Support | follows the Docker 29 default direction; the `root` setting is Docker's own documented method | returns to the classic driver, which the docs still call preferred on current distributions, with no stated long-term plan; the `false` form is an inference |
| Risk | a copy of a root that "should not be tampered with" (hence a rename, not a delete, and a rollback) | losing images' local-only layers (none are local-only here besides the built backend image) |
| Fit to `/data` | needs the room first (section 4) | needs room for re-pulled images |

**Recommendation: A.** It is the method Docker documents for this exact problem, it keeps every image, it frees `/` for good, and it stays on the store Docker 29 now defaults to. B does not free `/` by itself and needs re-pulls. The plan keeps B as the fallback if `/data` cannot be given the room.

## 4. Space: the first precondition is room on `/data`

Arithmetic from the live numbers (16:13Z; `stat -f` on `/data`: 25,721,923 blocks of 4 KiB, 5,270,146 free, 4,086,451 available) and the owner's 7.2G:

| | now | after +7.2G |
|---|---|---|
| used | 78.0 GiB | 85.2 GiB |
| available | 15.6 GiB | 8.4 GiB |
| by `df` (used / (used + avail)) | 83.35% | **91.04%** |
| by Loki's formula ((Blocks-Bfree)/Blocks) | 79.51% | **86.85%** |

- Our run gate is 85% by `df`; the move alone puts `/data` at 91%, above it. Loki's throttle line (90%) is at 88.3 GiB used: after the move there would be 3.1 GiB of headroom, and one backend build adds about 1.4 GiB of cache.
- **So `/data` needs room BEFORE the move.** To land at 85% by `df`: free **5.7 GiB** first; at 80% (a comfortable margin, and room for a build): free **10.3 GiB**. The plan states 10 GiB as the target and 5.7 GiB as the floor.
- What `/data` holds (read as ordinary user; `/data/docker` is unreadable to me; `docker system df` puts its named volumes at 666.8 MB, and its other contents are not visible): `/data/vboxuser`, which I can read, accounts for 78G of the 78.0 GiB used. By size: `Work` 55G (of which `rpg-based-simulation` 21G, with 16G in its `.claude/worktrees`; `groups_base` 9.4G; `simq_sweep` 4.3G; others 2 to 3G each), `.local` 11G (`lib` 5.5G, `share` 4.7G), `.vscode-server` 4.2G, `.npm` 2.2G, `tmp` 2.0G, `aw-pytest-tmp` 1.4G, `playwright-browsers` 867M, `.antigravity` 528M, `aw-r0` 503M. The cheap and re-creatable ones (caches and temp): `.npm` 2.2G, `tmp` 2.0G, `aw-pytest-tmp` 1.4G, `playwright-browsers` 0.9G: about 6.5 GiB, which clears the 5.7 GiB floor but not the 10 GiB target. The rest is listed for size only and is not proposed as reclaimable: it is the owner's call, and each worktree, `groups_base` and `simq_sweep` must be checked for unpushed or unsaved work first (removing a worktree is the owner's alone).
- **Moving less.** Everything that is pruned on `/` first is not copied: `docker builder prune` (1.4 GB reclaimable per `docker system df`) and `docker image prune -a` (1.65 GB reclaimable; it removes every image no container references, here 15 of 16, which then have to be re-pulled or rebuilt; the owner chooses). Docker's figures and `du`'s differ because of the compressed copies, so the owner re-runs `sudo du -sh /var/lib/containerd` after pruning and the plan uses that number.
- **Keeping the cache bounded afterwards.** The build cache regrows about 1.4 GiB per backend build. Two controls: (1) the `builder.gc` policy in `daemon.json` (keys per the GC page); whether it applies under the containerd image store is **not documented**, so the plan tests it (a build, then `docker buildx du`) and falls back to (2); (2) a `docker builder prune --keep-storage <size>` before each heavy run, plus the pre-run `df` gate already in `docs/runbooks/log-shipping.md` (85% on `/` and `/data`).

## 5. Restart impact (re-checked at planning time)

- Engine: one context, no rootless engine; lead confirms no `portal-*` images or containers (the earlier note came from before the reboot).
- Now: only `cool_curie` (`github-mcp-server`) is on this engine, running, restart policy `no`; `docker ps -a` lists nothing else (no exited container this time). The owner confirms nothing else, and re-runs `docker ps -a` just before the restart.
- Live restore is off, so stopping Docker stops `cool_curie`, and with restart policy `no` it does not come back by itself: whoever uses the MCP server starts it again.
- During the window (stop to start, minutes) every Docker client gets "cannot connect"; any build in progress fails.
- Option A restarts both docker and containerd; option B only docker.

## 6. Open items

- The exact `containerd` flavour of the copy (`rsync -aHAXS` with `--numeric-ids`, run as root with both services stopped) is standard practice, not documented by containerd; the plan treats it as the copy method and verifies by a dry-run `rsync` showing no differences and by the dry checks in the runbook.
- Whether `daemon.json` `builder.gc` applies under the containerd image store: not documented; tested after the move.
- Whether `"containerd-snapshotter": false` works as written: not documented; matters only for option B.
- Docker's and containerd's behaviour at version 29.3.1 was read from current documentation, not from the 29.3.1 source.
