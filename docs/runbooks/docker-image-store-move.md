---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform]
---

# Runbook: move Docker's containerd image store off the root disk

Owner-run. No agent runs any command in this file: every `sudo` step, every edit of a file under `/etc`, and every stop or start of docker or containerd is the owner's. Ticket: `TCK-20261112-DOCKER-IMAGE-STORE-OFF-ROOT-DISK` (planning only; the restart needs its own owner yes and timing). Evidence and sources: `agent-working/staging_artifacts/TCK-20261112-DOCKER-IMAGE-STORE-OFF-ROOT-DISK/` (investigation, plan, test plan). Nothing in this file prints or takes a secret.

## Why

Docker 29 on this host uses the containerd image store. Docker's `data-root` (`/data/docker`, in `/etc/docker/daemon.json`) does not apply to it: image content, snapshots and the build cache live under containerd's own root, `/var/lib/containerd`, on `/` (49G). On 2026-11-11 `/` reached 100% (two backend builds, about 1.4 GB of cache each, on top of the images), which is what made Loki refuse every push (`docs/runbooks/records/2026-11-12-loki-volume-and-api-dashboard.md`). This runbook moves that root to `/data`.

## What it is, and the choice

| | A: move containerd's root to `/data/containerd` (**recommended**) | B: turn the containerd snapshotter off |
|---|---|---|
| Change | `root = "/data/containerd"` in `/etc/containerd/config.toml`; stop docker and containerd; copy; start | `"features": {"containerd-snapshotter": false}` in `daemon.json`; restart docker |
| Images | all kept | hidden, not deleted; re-pull or rebuild every one |
| Frees `/` | yes, after you delete the old root | **no**: hidden images stay in `/var/lib/containerd` |
| Restart | docker and containerd | docker |

Docker's documentation gives option A's method itself: "To change the storage location of containerd snapshotters, use the system containerd configuration file" with a top-level `root = "..."` (https://docs.docker.com/engine/daemon/, section "Configure the data directory location"). It also says containerd's storage "is not automatically moved" when `data-root` is set and that you "need to configure containerd's data directory separately". For B, no page read shows `false` written out; it is the general `features` rule. No page states a long-term plan for the classic driver. Use A unless `/data` cannot be given the room (below); then see "Option B" at the end.

## Facts at planning time (2026-11-12)

- Docker 29.3.1, Ubuntu 25.10, one docker context (`default`), no rootless engine. `dockerd` runs with `--containerd=/run/containerd/containerd.sock`, so the SYSTEM containerd (`containerd.service`) is the one that matters. `/etc/containerd/config.toml` holds only `disabled_plugins = ["cri"]`.
- `/var/lib/containerd` is **7.2G** (owner's `sudo du -sh`, after the prunes of 2026-11-12). Docker's own volumes (666.8 MB) are in `/data/docker/volumes` and do not move.
- `/` is at 72% (13.0 GiB free). `/data` is at 83.35% by `df` (78.0 GiB used, 15.6 GiB available of 98.1 GiB; 79.51% by Loki's formula).

## Restart impact

- **Currently only `cool_curie` (github-mcp-server) on this engine; owner to confirm nothing else.** Re-run `docker ps -a` just before the restart and stop if anything else is listed that you did not expect.
- `cool_curie` is not started by hand and has no restart policy of its own (`no`): Claude Code starts it from the repository's `.mcp.json`, server `github`, which runs `docker run -i --rm --env-file ${HOME}/.config/rpg-sim/github-mcp.env ghcr.io/github/github-mcp-server` (stdio, auto-remove). Live restore is off, so stopping docker kills it and `--rm` removes it. Every Claude Code session that uses it loses the GitHub MCP tools until that session reconnects the server (`/mcp`, reconnect) or restarts; the `gh` command line keeps working. Nobody runs a `docker run` for it by hand, so there is nothing to start again by hand.
- The compose stack is not running now (`docker ps -a` shows only `cool_curie`); if you start it later, it comes up on the new root.
- While docker is stopped (minutes), every docker client gets "cannot connect to the Docker daemon", and any build in progress fails. Do not start this during a stack run or a build.
- Option A restarts docker and containerd; option B restarts docker only.

## Step 0: make room on `/data` FIRST (the precondition)

The move adds 7.2G to `/data`. With the numbers above that takes `/data` from 83.35% to **91.04%** by `df` (and 79.51% to **86.85%** by Loki's formula): above our 85% run gate, and with only 3.1 GiB under Loki's 90% line, which one backend build (about 1.4 GiB of cache) would eat. So free room on `/data` before you move anything:

- to land at 85% by `df`, free **at least 5.7 GiB**; to land at 80% (recommended: it leaves room for builds), free **about 10.3 GiB**. Re-measure on the day (`df -h /data`), because the figures move.
- What is cheap and re-creatable (sizes as measured on 2026-11-12; yours to judge): `/data/vboxuser/.npm` 2.2G (`npm cache clean --force`), `/data/vboxuser/tmp` 2.0G, `/data/vboxuser/aw-pytest-tmp` 1.4G, `/data/vboxuser/playwright-browsers` 0.9G: about 6.5 GiB, which clears the floor but not the target. The rest is listed for size only, and none of it is proposed as reclaimable; each is the owner's call, and **check each one for unpushed or unsaved work first**: the git worktrees under `/data/vboxuser/Work/rpg-based-simulation/.claude/worktrees` (16G in all; removing a worktree is the owner's alone, and a worktree may hold unpushed commits), `/data/vboxuser/Work/groups_base` (9.4G), `/data/vboxuser/Work/simq_sweep` (4.3G), other projects under `/data/vboxuser/Work`, and `/data/vboxuser/.local` (11G). An agent does not delete or propose deleting any of it.
- If you cannot reach the floor, the honest answer is that `/data` needs more room first (a bigger disk), or use option B (smaller on `/data`, but `/` is not freed by it).

Do the cheap, re-creatable set above first (that is the default order). Then shrink what has to move, on `/` (cheaper there). The default is one command; the second is optional:

```
docker system df
docker builder prune -f
docker system df
sudo du -sh /var/lib/containerd
```

`docker builder prune -f` removes dangling build cache (add `-a` to remove all unused cache): about 1.4 GB reclaimable per `docker system df`. **Optional, not the default:** `docker image prune -a` removes every image no container references (here 15 of the 16, about 1.65 GB by Docker's figure), but the next stack run then has to re-pull about 4.7G of stack images and rebuild `platform-backend`, and that lands on `/data` anyway after the move; run it only if you need the room. It asks for confirmation; read the list. Neither command touches named volumes. Use the new `du` figure for the arithmetic above.

## Step 1: pre-checks

```
docker ps -a
docker info -f '{{.DriverStatus}}'
df -h / /data
findmnt -T /data
ls -ld /data/containerd
grep -n '^\[' /etc/containerd/config.toml
systemctl cat containerd.service | grep -n ExecStart
```

Expected: only `cool_curie` listed; `[[driver-type io.containerd.snapshotter.v1]]`; `/data` with the room from step 0; `/data` on `/dev/sdb1`; `ls` says `/data/containerd` does not exist; `grep` prints nothing (no `[table]` header in the file, so a new top-level `root` line is read as top-level). If `grep` prints a line, stop: a top-level key added after a table header would belong to that table. The `ExecStart` check must show a plain `ExecStart=/usr/bin/containerd` with no `--root` or `--config` (a `ExecStartPre=-/sbin/modprobe overlay` line is fine); otherwise the unit overrides `config.toml` and the `root` line would not take effect. Checked read-only on 2026-11-12: the unit has `ExecStart=/usr/bin/containerd` and no such flags.

## Step 2: stop docker and containerd

```
sudo systemctl stop docker.socket
sudo systemctl stop docker.service
sudo systemctl stop containerd.service
systemctl is-active docker.socket docker.service containerd.service
```

Expected: all three `inactive` (this is a check, not an assumption: the socket must really be stopped, or a client call would start docker again mid-copy). (`docker.socket` is stopped first because `dockerd -H fd://` is socket-activated: a client call would otherwise start docker again mid-copy.)

## Step 3: copy, and keep the original

```
sudo mkdir -p /data/containerd
sudo rsync -aHAXS --numeric-ids --info=progress2 /var/lib/containerd/ /data/containerd/
```

`-aHAXS` keeps permissions, owners, hard links, ACLs, extended attributes (overlayfs layers carry them) and sparse files. Verify with a dry run that lists nothing to do, and compare the sizes:

This first command is a DRY RUN (`-n`: it changes nothing). It deliberately has no `--delete`, so there is no destructive form of it to run by mistake; never add `--delete` to any rsync in this file. Without `--delete` it still lists every file that is in the source and missing or different in the copy (as `>f+++++++++`-style lines):

```
sudo rsync -aHAXSn --numeric-ids --itemize-changes /var/lib/containerd/ /data/containerd/
sudo du -sx /var/lib/containerd /data/containerd
```

The dry run must print no file lines; the two sizes should match closely.

## Step 4: point containerd at the new root

Back the file up, check it, add one top-level line:

```
sudo cp /etc/containerd/config.toml /etc/containerd/config.toml.bak-before-root-move
sudo cat /etc/containerd/config.toml
printf 'root = "/data/containerd"\n' | sudo tee -a /etc/containerd/config.toml
sudo cat /etc/containerd/config.toml
```

The file should now read `disabled_plugins = ["cri"]` followed by `root = "/data/containerd"` (no `[table]` header anywhere). Move the old root aside instead of deleting it, so the rollback is one rename:

```
sudo mv /var/lib/containerd /var/lib/containerd.old-before-move
```

## Step 5: start

```
sudo systemctl start containerd.service
sudo systemctl start docker.service
systemctl is-active docker.socket docker.service containerd.service
```

Expected: all three `active`. `docker.socket` was stopped in step 2; starting `docker.service` brings it back, and this check confirms it rather than assuming it.

## Step 6: dry checks (is it really on the new root, and is nothing lost)

```
sudo containerd config dump | grep -E '^(root|state) '
docker info -f '{{.DriverStatus}} {{.DockerRootDir}}'
docker images
docker volume ls
docker volume inspect platform_grafana_data -f '{{.Mountpoint}}'
sudo du -sh /data/containerd
df -h / /data
```

Expected: `root = "/data/containerd"` (and `state = "/run/containerd"`); the driver still `io.containerd.snapshotter.v1` and `DockerRootDir` still `/data/docker`; `docker images` lists the images that were there (fewer if you pruned `-a`); the volumes and their mountpoints under `/data/docker/volumes` unchanged; `/data/containerd` about the size copied; `/` unchanged until step 8 (the old root is only renamed). Then prove it works end to end: `docker run --rm hello-world` (needs a pull) or, for a built image, `docker compose --profile observability config -q` plus one `docker compose up -d redis` and `docker compose down` (no `-v`).

Leave it for a while (a day of normal use, one build) before step 8.

## Step 7: keep the build cache bounded

The cache regrows about 1.4 GB per backend build, now on `/data`. Two controls, in this order:

1. Put a limit into `/etc/docker/daemon.json` next to `data-root`, for example:

```
{
  "data-root": "/data/docker",
  "builder": { "gc": { "enabled": true, "defaultKeepStorage": "3GB" } }
}
```

   restart docker (`sudo systemctl restart docker`) and check after one build: `docker buildx du` should stay near the limit. **Docker's documentation does not say whether this policy applies with the containerd image store** (it documents the keys, https://docs.docker.com/build/cache/garbage-collection/); if the cache keeps growing, rely on 2.
2. Before each heavy run: `docker builder prune --keep-storage 3GB -f` (the docs describe `--keep-storage` as "Amount of disk space to keep for cache" and show no unit format; check that `3GB` is accepted), and the pre-run gate already in `docs/runbooks/log-shipping.md`: `df` below 85% on `/` and on `/data`.

## Step 8: only later, free `/`

When you are satisfied (the old root is the rollback until now):

```
df -h /
sudo rm -rf /var/lib/containerd.old-before-move
df -h /
```

That `rm` is yours to run, after a last look at the path. `/` should drop by about 7.2G (from about 72% to about 57% on today's figures).

## Rollback (option A), before step 8

```
sudo systemctl stop docker.socket
sudo systemctl stop docker.service
sudo systemctl stop containerd.service
sudo cp /etc/containerd/config.toml.bak-before-root-move /etc/containerd/config.toml
sudo mv /var/lib/containerd.old-before-move /var/lib/containerd
sudo systemctl start containerd.service
sudo systemctl start docker.service
docker info -f '{{.DriverStatus}}'
docker images
```

The old root was never modified (it was only renamed), so this returns to the exact previous state. Anything pulled or built since the move is on the new root and is lost from view until you move forward again; `/data/containerd` can stay for another attempt.

## Option B (if `/data` cannot take the room)

Not recommended, and it does not free `/`: with the snapshotter off, docker uses its classic overlay2 store under `/data/docker`, and the images in the containerd store become hidden, still occupying `/var/lib/containerd`. Docker's docs: switching backends "temporarily hides images and containers created with the other backend"; to keep an image, "push them to a registry first, or use `docker save` to export them". Steps:

```
docker ps -a
docker images
sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.bak-before-b
```

Edit `/etc/docker/daemon.json` to `{"data-root": "/data/docker", "features": {"containerd-snapshotter": false}}`, then `sudo systemctl restart docker` and check `docker info` shows `Storage Driver: overlay2`. (`false` is an inference from Docker's general `features` rule, not a documented example: if `docker info` still says `io.containerd.snapshotter.v1`, stop.) Then `docker images` is empty: re-pull or rebuild. To free `/` you would still have to remove containerd's content yourself; no documented way was found, so do not do it without a separate plan. Rollback: restore `daemon.json.bak-before-b` and restart docker; the hidden images reappear.

## Never

- Delete `/var/lib/containerd` before step 6 passes and you have used the new root for a while. containerd's operations guide says its `root` and `state` directories "should not be tampered with as corruption and bugs can and will happen".
- Run any of this while a build or the compose stack is running.
- Use `docker system prune --volumes` as a shortcut: it can remove volumes; the steps above never touch them.
