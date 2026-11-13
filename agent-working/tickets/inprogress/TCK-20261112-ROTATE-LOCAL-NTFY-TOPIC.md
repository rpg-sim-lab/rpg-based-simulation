---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261112-ROTATE-LOCAL-NTFY-TOPIC
phase: inprogress
date: 2026-11-12
tags: [platform, security]
---

# TCK-20261112-ROTATE-LOCAL-NTFY-TOPIC

## Title
Rotate the local ntfy alert topic, which was once echoed in an agent terminal, by an owner-run procedure

## Status
INPROGRESS

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Owner yes, 2026-11-12 (#715 6828616413). The local ntfy topic in `docker/secrets/ntfy_topic` (gitignored) was echoed in an agent terminal on 2026-10-26. Rotate it. The new value is set by the owner in the secret file and never appears in git, #715, tickets, handovers or agent output (lead-planner, 2026-11-12).

## Scope
1. Write `docs/runbooks/ntfy-topic-rotation.md`, an owner-run procedure built from the setup steps at the top of `compose.yaml` (lines 11-18):
   - generate a new topic into `docker/secrets/ntfy_topic` (`openssl rand -hex 16 >`, mode 644 as documented);
   - revoke Grafana's write access on the old topic and grant it on the new one (`ntfy access`);
   - recreate grafana so it reads the new file;
   - re-subscribe the owner's client;
   - decide whether to rotate the token too, with a reason.
2. Secrets on argv: the setup's `ntfy access grafana "$(cat docker/secrets/ntfy_topic)"` puts the topic on a process command line (visible in `ps` on the host and in the container). Find out whether the ntfy CLI or server API can take it another way (stdin, a file, an HTTP call with `curl -K -`). If none can, say so and keep the exposure as short as possible. Correct the compose.yaml setup comment the same way.
3. Proof: one short fire test after the owner rotates (a heavy-slot go from lead-planner). A TargetDown alert reaches the owner on the NEW topic, and an anonymous read of the old topic is refused (403). No topic value goes into any evidence file; scan by counts.

## Out of Scope
- Changing the alerting rules or the contact-point shape.
- Agents reading or printing the secret files.

## Acceptance Criteria
- The runbook exists, and every secret-handling step is owner-run with no value printed (validated: review).
- After the owner's rotation, a firing alert arrives on the new topic and the old topic is refused (observed).
- 0 evidence files contain the old or new topic (validated: scan by counts).

## Related Tickets
- TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY (same batch).
- The ntfy setup: #640 and the 11-11 fire test in TCK-20261111-COMPOSE-IMAGE-BUMPS-WITH-STACK-PROOF.

## Related Docs
docs/runbooks/alerting-pipeline.md

## Related Stored Artifacts
None.

## Related Code Areas
compose.yaml
docker/grafana/provisioning/alerting/contact-points.yaml

## Assumptions / Open Questions
- Hotfix tier: the intent is self-evident (rotate a leaked local value), and the change is a runbook plus a comment fix.

## Implementation Notes
Status 2026-11-12: the runbook and the comment fix are written; the rotation and the fire test are the owner's and lead-planner's (pending).
- **Runbook:** `docs/runbooks/ntfy-topic-rotation.md` (owner-run; one command per line; no value printed). Steps: private copy of the old topic, a new one in a separate file, `ntfy access --reset grafana` (names the user, so no topic on a command line), install the new file, grant write-only through the environment, recreate Grafana (its `$__file{}` read happens at start), re-subscribe the owner's client; then counts-only checks and the fire test. Linked from `docs/runbooks/README.md` and `alerting-pipeline.md`.
- **Can `ntfy access` take the topic without argv? No.** In `cmd/access.go` at ntfy v2.37.2 (read through the GitHub API) the topic is `c.Args().Get(1)`; the only flag is `--reset`; there is no stdin, file or environment source. The topic therefore cannot be kept off a process's arguments entirely. What the runbook and the `compose.yaml` comment now do: pass it through the environment (`docker exec -e NTFY_TOPIC`), which keeps it off the host command line and out of shell history; it stays in the container's process list for the milliseconds the command runs.
- **The CLI echoes the topic on success** ("granted write-only access to topic <topic>"): that is how it was printed in an agent terminal on 2026-10-26. The commands now discard the output (`> /dev/null`).
- **`compose.yaml` setup comment corrected:** the `user add` line passes `NTFY_PASSWORD` through the environment instead of `-e NTFY_PASSWORD=<value>` on the command line, and the `access` line uses the environment form with discarded output, with a note on why.
- **Tested in an isolated throwaway container** (the pinned ntfy image already local; its own temporary auth database; no ports, no volumes; a made-up topic; removed afterwards; the stack's state was not touched): `sh` exists; `NTFY_PASSWORD` from the environment works for `ntfy user add`; `docker exec -e NAME` with no value forwards the host's value; `ntfy access` with the topic from the environment works, its output contains the topic, `ntfy access --reset grafana` revokes without naming the topic, and a grant is verifiable by count. Tested with `docker exec`; the runbook uses `docker exec` too (with the container id from `docker compose ps -q ntfy`).
- **Not adopted: declarative provisioning** (`NTFY_AUTH_ACCESS` and friends), which would keep the topic off every command line but needs the `grafana` user provisioned (bcrypt hash, `$` escaping) and deletes a hand-made user if it is later removed from the config. Documented in the runbook as a possible later step.
- **Token:** not rotated with the topic (its power comes from the user's access list, which is reset and re-granted; only the topic was echoed). The runbook gives the delete-and-recreate path and a count-only check, and says ntfy's docs do not state that deleting a user removes its tokens.

## Test Summary
- **validated (static):** the runbook has frontmatter and links valid; no line starts with `!`; no 32+ hex string; no command line carries a topic or token value; every topic-handling command either goes through the environment or stdin and discards or counts its output.
- **observed in the throwaway container:** the command forms above (exit codes 0; the echoed topic; the forwarded variable; reset and the count checks).
- **not observed (pending):** the owner's rotation, a firing alert on the NEW topic, and an anonymous read of the old topic refused (403). That needs the owner to rotate and lead-planner's heavy-slot go. Known gap: the fire-test proof is not yet observed.

## Files Changed
- `docs/runbooks/ntfy-topic-rotation.md` (new), `docs/runbooks/README.md`, `docs/runbooks/alerting-pipeline.md`.
- `compose.yaml`: the setup comment at the top (the `user add` and `access` lines and a note).

## Completion Summary

## Status note (2026-11-13)
Stays INPROGRESS: the runbook is committed, but acceptance needs the owner's rotation and a fire test (a lead slot). Not closed by the batch that carries the runbook.
