---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, security]
---

# Runbook: rotate the local ntfy alert topic

Owner-run. No agent runs these steps, reads `docker/secrets/ntfy_topic` or `docker/secrets/ntfy_token`, or sees the new value: the new topic is set by you in the secret file and never appears in git, #715, tickets, handovers or agent output. Ticket: `TCK-20261112-ROTATE-LOCAL-NTFY-TOPIC`. The alerting setup this changes is in the header of `compose.yaml` and in [alerting-pipeline.md](alerting-pipeline.md).

**Run from:** the checkout that holds your `docker/secrets/` files (on this host: `/data/vboxuser/Work/rpg-based-simulation/.claude/worktrees/platform`). The compose project name comes from the directory name, because `compose.yaml` sets no top-level `name:`, so that checkout is project `platform`. Running `docker compose` from any other checkout (the main checkout `rpg-based-simulation`, or another worktree) creates a SECOND project. It gets its own fresh volumes, for example `rpg-based-simulation_ntfy_data`, and fails on the missing secret files. This happened on 2026-11-12. Before the first compose command, confirm where you are:

```
pwd
docker compose ls
```

`docker compose ls` must list `platform` (if the stack is up), and `pwd` must be the checkout above. If `docker compose ls` shows a project you didn't mean to start, take it down from the checkout that started it, with `docker compose down` and no `-v`, before you go on.

## Why, and how much it matters

The local topic in `docker/secrets/ntfy_topic` (gitignored) was echoed in an agent's terminal on 2026-10-26 (an `ntfy access` command prints it on success). Rotate it as hygiene. Know the actual exposure: ntfy here runs with `auth-default-access: deny-all`, so **knowing the topic is not enough** to read or write it. Reading needs a login (your admin user) and writing needs Grafana's token, which belongs to a user with write-only access to that one topic. The topic works as a password only where anonymous access is allowed, and here it is not.

## Where the topic can show up (what was found)

- **On a command line.** `ntfy access` takes the topic only as a positional argument: in `cmd/access.go` at ntfy v2.37.2 it is `c.Args().Get(1)`, with a single flag, `--reset`, and no stdin, file or environment source. So it cannot be kept off a process's argument list entirely. The setup in `compose.yaml` used to pass it as `ntfy access grafana "$(cat docker/secrets/ntfy_topic)" write-only` through `docker compose exec`, which put it in the `docker` process arguments on the host (visible to any local user in `ps` while it ran) as well as in the container. The commands below pass it through the **environment** instead (`docker exec -e NTFY_TOPIC`), which keeps it off the host command line and out of shell history; it is still in the **container's** process list for the milliseconds `ntfy access` runs, which this CLI does not avoid.
- **On the terminal.** `ntfy access` prints "granted ... access to topic <topic>" on success. Every command below that grants access discards its output (`> /dev/null`). (Checked 2026-11-12 in an isolated throwaway ntfy container with a made-up topic: the output contained the topic.)
- **In the secret file.** `docker/secrets/ntfy_topic` is mode 644 because Grafana's container user must read it through the bind mount, so any local user of this host can read it. That is accepted for this single-user host (the note in `compose.yaml`).
- **Not an option adopted here: declarative provisioning.** ntfy also reads `NTFY_AUTH_ACCESS='grafana:<topic>:wo'` (and `NTFY_AUTH_USERS`, `NTFY_AUTH_TOKENS`) at start; no argument then carries the topic, and "when entries are removed, they are deleted from the database". But `auth-access` needs the user to be provisioned too (a bcrypt hash in `NTFY_AUTH_USERS`, with `$` escaping), and the docs warn that a user created by hand and then added to the config is "upgraded" to provisioned, and **deleted** if later removed from it. That is a bigger change to a working setup, so this runbook keeps the CLI and says so; it is a possible later step.
- The Grafana contact point reads the topic from `/run/secrets/ntfy_topic` when it starts (`$__file{}` in `docker/grafana/provisioning/alerting/contact-points.yaml`), so Grafana must be recreated after the file changes.

## Before you start

Check the path is ignored by git (stop if this prints nothing), that the stack's ntfy is running, and see what is subscribed on your side:

```
git check-ignore -q docker/secrets/ntfy_topic && echo ignored-ok
docker compose --profile observability up -d ntfy
docker compose --profile observability ps -q ntfy
```

## Rotate (owner-run, one command per line)

1. Keep the old topic in a private copy, only for the check at the end, and make the new one in a separate file (neither is printed):

```
umask 077
cp docker/secrets/ntfy_topic docker/secrets/ntfy_topic.old
openssl rand -hex 16 > docker/secrets/ntfy_topic.new
chmod 644 docker/secrets/ntfy_topic.new
```

2. Revoke everything Grafana's user can access on the old topic. This names the user, not the topic, so no topic is on any command line. From here until step 4, alerts fail with 403:

```
docker exec "$(docker compose --profile observability ps -q ntfy)" ntfy access --reset grafana > /dev/null
```

3. Put the new topic in place:

```
mv docker/secrets/ntfy_topic.new docker/secrets/ntfy_topic
```

4. Grant Grafana write-only access to the new topic (through the environment, output discarded):

```
NTFY_TOPIC="$(cat docker/secrets/ntfy_topic)" docker exec -i -e NTFY_TOPIC "$(docker compose --profile observability ps -q ntfy)" sh -c 'exec ntfy access grafana "$NTFY_TOPIC" write-only' > /dev/null
```

5. Recreate Grafana so it reads the new file (a `mv` replaces the file, and the old bind mount would keep the old one):

```
docker compose --profile observability up -d --force-recreate grafana
```

6. Re-subscribe your own client. Read the new topic once, in a terminal that no agent shares, and enter it in your ntfy app (remove the old subscription first). Your admin login can subscribe; the topic never needs to appear anywhere else:

```
cat docker/secrets/ntfy_topic
```

## Check (counts and status codes only; no topic is printed)

Anonymous access to the old and the new topic is refused (the topic is sent to curl on stdin, not on the command line). Expected `403` for both:

```
printf 'url = "http://127.0.0.1:2586/%s/json?poll=1"\n' "$(cat docker/secrets/ntfy_topic.old)" | curl -s -K - -o /dev/null -w '%{http_code}\n'
printf 'url = "http://127.0.0.1:2586/%s/json?poll=1"\n' "$(cat docker/secrets/ntfy_topic)" | curl -s -K - -o /dev/null -w '%{http_code}\n'
```

(Replace `2586` if you set `NTFY_PORT`.) Grafana's user has exactly one write-only entry; this prints a count, never the topic:

```
docker exec "$(docker compose --profile observability ps -q ntfy)" ntfy access grafana | grep -c 'write-only access to topic'
```

Expected `1`. The real proof is a fired alert reaching your client on the new topic, which is a short stack run that needs lead-planner's heavy-slot go: see the "Fire test" below. When it passes, remove the old copy:

```
rm docker/secrets/ntfy_topic.old
```

## The token

Rotating the topic does not require rotating Grafana's token: the token's power comes from the `grafana` user's access list, which steps 2 and 4 reset and re-grant for the new topic only, it is write-only, and the token was never echoed (only the topic was). If the **token** itself is ever exposed, delete the user and set it up again, with no token on a command line:

```
docker exec "$(docker compose --profile observability ps -q ntfy)" ntfy user del grafana
```

then repeat the user, access and token steps from the header of `compose.yaml` (the `token add` step pipes the new token straight into `docker/secrets/ntfy_token`). ntfy's documentation shows `ntfy user del` and `ntfy token remove` but **does not say that deleting a user also removes its tokens**, so check, by count only (the listing prints token values, so it is never shown):

```
docker exec "$(docker compose --profile observability ps -q ntfy)" ntfy token list grafana | grep -c 'tk_'
```

Expected `1` (only the new token). If it is more, the old token survived: removing it needs the token on a command line (`ntfy token remove grafana <token>`), a short, local exposure you decide to accept; do not paste it anywhere else.

## Fire test (after you have rotated; needs lead-planner's slot go)

Stop `redis-exporter` for about three minutes, as in the 2026-11-12 compose-bumps run (`docs/runbooks/records/2026-11-11-compose-image-bumps.md`, section 3, row 4): `TargetDown` for redis fires and a `[firing]` message reaches your client **on the new topic**, then start it again and the `[resolved]` message arrives. The old topic must still answer 403 to an anonymous read (the first check above). No topic value goes into any evidence file; evidence is scanned by counts.
