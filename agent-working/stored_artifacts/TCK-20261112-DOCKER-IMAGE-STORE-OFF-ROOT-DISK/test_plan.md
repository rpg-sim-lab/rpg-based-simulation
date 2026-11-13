---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261112-DOCKER-IMAGE-STORE-OFF-ROOT-DISK
phase: test_plan
date: 2026-11-12
tags: [platform]
artifact_type: test_plan
---

# Test plan: TCK-20261112-DOCKER-IMAGE-STORE-OFF-ROOT-DISK

Planning only: nothing here is run against the Docker engine. The checks are on the runbook and its sources; the runbook's own dry checks are the owner's, run on the day.

## Static checks on the runbook (run now)

- C1. Frontmatter valid (`validate_frontmatter.py --content-type doc`); the file is under `docs/runbooks/` and linked from `docs/runbooks/README.md` and `docs/runbooks/disk-space.md`.
- C2. **No secret and no `!` prefix.** A scan of the runbook for lines that start with `!`, for the words `password`, `token`, `topic`, `secret` as values, and for `[0-9a-f]{32,}` strings: counts must be 0 (an explanation that mentions the word "secret" is reviewed by eye).
- C3. **Every privileged command is plain shell, one per line.** A scan that no code line contains ` then ` or `&&` joining a `sudo` command to another (counts), and that every `sudo` line is inside a fenced block.
- C4. **The numbers match.** The `stat -f` figures and the arithmetic in `investigation.md` section 4 are recomputed by a short script in the check (the same 91.04% / 86.85% / 5.7 GiB / 10.3 GiB); the runbook quotes the same figures.
- C5. **Quotes match their sources.** Each quoted sentence in the runbook and the investigation is checked against the fetched page text recorded in the report (done by reading; sources listed in `investigation.md`).
- C6. Paths guard and REGISTRY no-drift pass.

## What the owner runs on the day (the runbook's dry checks; recorded in the runbook, not here)

`docker info -f '{{.DriverStatus}} {{.DockerRootDir}}'` unchanged driver and data-root; `sudo containerd config dump | grep -E '^(root|state) '` shows the new root; `docker images` lists the expected images; `docker volume inspect` mountpoints under `/data/docker/volumes` unchanged; `df` shows `/` freed only after the old root is deleted; one build and one `docker builder prune --keep-storage` show the cache stays bounded; `docker buildx du` after a build tests whether the `daemon.json` GC applies.

## Limits

No part of the procedure is exercised by an agent (the ticket forbids it). The acceptance is review: platform-planner, then lead.
