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
## Test Summary
## Files Changed
## Completion Summary
