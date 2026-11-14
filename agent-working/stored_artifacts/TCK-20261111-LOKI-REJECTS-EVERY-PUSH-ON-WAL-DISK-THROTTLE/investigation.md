---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE
phase: investigation
date: 2026-11-12
tags: [platform, observability]
artifact_type: investigation
---

# Investigation: TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE

Read-only. No stack was started. Source read at tag v3.7.9 (the pinned image, `grafana/loki:3.7.9`) via raw.githubusercontent.com; the docs page is https://grafana.com/docs/loki/v3.7.x/configure/ (section `ingester`). The host numbers are from `stat -f` on 2026-11-12 (section 4).

## 1. Where the 94.8% comes from (scope item 1) - validated against source, not yet observed in a run

- Source: `pkg/ingester/wal_unix.go`. `checkDiskUsage` calls `syscall.Statfs(w.cfg.Dir, &stat)` and computes, in bytes (not inodes):
  `total = Blocks*Bsize; free = Bfree*Bsize; used = total - free; usage = used/total`.
  It uses `Bfree`, not `Bavail`. The blocks that ext4 reserves for root count as free.
- `pkg/ingester/wal.go`, `monitorDisk`: a 10 s ticker; `isThrottled := usage >= DiskFullThreshold`; it logs "disk usage exceeded threshold, throttling writes" with `usage_percent` and `threshold_percent`, and on the way back "disk usage below threshold, resuming writes". A failed Statfs logs "failed to check disk usage" and keeps the previous state.
- Config: `ingester.wal.disk_full_threshold`, flag `-ingester.wal-disk-full-threshold`, default `0.9`, `0` disables the throttle (doc line: "Threshold for disk usage (0.0 to 1.0) at which the WAL will throttle incoming writes. Set to 0 to disable throttling.").
- Path: `w.cfg.Dir`. The image's config (`cmd/loki/loki-docker-config.yaml`, copied to `/etc/loki/local-config.yaml`) has no `ingester:` block and only `common.path_prefix: /loki`, so the WAL dir is the built-in default or one derived from the path prefix. **Unverified:** whether it resolves to `/loki/wal` or to `wal` relative to the working directory `/`. Either way it is inside the container's writable layer, so it is the same filesystem. The run will tell (section 5).
- Why 94.8% fits a full `/`: this host's `/` has 5.14% of its blocks reserved (`Bfree - Bavail`, section 4). When `df` shows 100% with about 20 MB free, Loki's formula gives `1 - (0.0514 + 20 MB / 49 GB)` = about 94.8%. The logged figure was 94.80%. So Loki measured a full `/`, not `/data`.
- Corollary, and why `/data` at 83% was a red herring: with the containerd image store (`docker info`: `io.containerd.snapshotter.v1`, DockerRootDir `/data/docker`), container layers sit under `/var/lib/containerd` on `/`. This agrees with the 2026-11-12 correction in the ticket.
- Caveat: the figure is a fit to a formula and a measured reserve ratio, not a Loki-side measurement. The proof run records `df` and `stat -f` for `/` at Loki's start so the match can be checked (test_plan T2).

## 2. Why "Ingester is shutting down" (scope item 2) - validated against source

- `pkg/ingester/ingester.go`: `var ErrReadOnly = errors.New("Ingester is shutting down")`, with the comment "returned when the ingester is shutting down and a push was attempted".
- `Ingester.Push`: `else if i.readonly { return nil, ErrReadOnly }`, and then `if i.wal.IsDiskThrottled() { return nil, ErrReadOnly }`. So the disk throttle rejects every push with the **same error text** as a real shutdown.
- It is not a state machine. `i.readonly` is set only by `stopIncomingRequests()` from `stopping()`. The throttle sets only the WAL's `diskThrottled` flag, re-evaluated every 10 s, so Loki recovers by itself as soon as usage is below 90%. During the run the push errors continued from 16:34 to 16:37 because `/` stayed full until the owner's cleanup; nothing in Loki was stuck.
- The message is misleading to operators (it looks like a crash, and the container never stopped). That is worth a line in the runbook (plan step 5), not a code change.
- A separate path exists: a WAL write failing with ENOSPC increments `walDiskFullFailures` and triggers flush-on-shutdown. It was not what we saw (the log line was the threshold line).

## 3. Which services keep state where (input to the volume decision)

From `compose.yaml` at HEAD of this branch:

| service | state path | storage today |
|---|---|---|
| redis | /data | named volume `redis_data` |
| prometheus | /prometheus | named volume `prometheus_data` |
| grafana | /var/lib/grafana | named volume `grafana_data` |
| tempo | /var/tempo | named volume `tempo_data` |
| ntfy | /var/lib/ntfy | named volume `ntfy_data` |
| backend | /app/data | bind mount `./data` |
| **loki** | /loki (chunks, rules, WAL) | **none: the container's writable layer** |
| alloy | /var/lib/alloy/data | container layer by design (compose comment: read offsets are lost on recreate; it is a few MiB) |

So the decision on "prometheus/grafana/redis volumes" is already made in the repo: they have named volumes. Only Loki is missing one. No change to the others.

## 4. Host numbers (read-only, 2026-11-12, this VM)

| fs | Blocks | Bfree | Bavail | df-style used | Loki-style (Blocks-Bfree)/Blocks | reserved (Bfree-Bavail)/Blocks |
|---|---|---|---|---|---|---|
| `/` (/dev/sda2) | 12,821,880 | 2,298,548 | 1,639,131 | 86.52% | 82.07% | 5.14% |
| `/data` (/dev/sdb1) | 25,721,923 | 5,338,510 | 4,154,815 | 83.07% | 79.25% | 4.60% |

(4 KiB blocks. `/` was 100% during the run and is 86.5% now after the owner's `docker builder prune`.) Loki's figure is always lower than `df`'s by about the reserve, so its 90% line is crossed at about `df` 94.5%.

## 5. Open items the proof run settles

1. The WAL dir Loki resolves (`/loki/wal` or `/wal`). Check with the `ingester.go` startup log line and `docker diff` on the container.
2. That `docker volume inspect <project>_loki_data` gives a `Mountpoint` under `/data/docker/volumes`.
3. Alloy's memory with working pushes (scope item 5).

## 6. Not found

- `wal_windows.go` and `wal_disk_throttle_test.go` were not read; the test file may document intended behaviour.
- The metric name for the throttle (`walDiskFullFailures` is the Go field; its Prometheus name was not read). Needed only for the optional alert (plan, option D).
