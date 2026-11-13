---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261113-PROOF-RUN-EXPECTS-AI-WORKER-LAG-NODATA
phase: open
date: 2026-11-13
tags: [platform, observability]
---

# TCK-20261113-PROOF-RUN-EXPECTS-AI-WORKER-LAG-NODATA

## Title
Stack proof runs without ai_worker always show AiWorkerLagHigh alerting (NoData by design); say so in the run procedure

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Owner yes, 2026-11-13 (lead-planner's relay, #715). In the 2026-11-12 ntfy fire test (TCK-20261112-ROTATE-LOCAL-NTFY-TOPIC), the 11-service proof path left out ai_worker, watchdog and frontend, as the 11-11 and 11-12 runs did. One Grafana instance stayed `alerting` for the whole run. It is inferred to be `AiWorkerLagHigh`: `rules-worker.yaml`, `noDataState: Alerting`, and with no ai_worker there is no `sim_stream_consumer_lag` series. That is the rule's designed behaviour: `docs/runbooks/ai-worker-lag.md`, "Why NoData fires the lag alert", says a stopped worker is the failure to catch. The run procedure doesn't say this, so a "no other alert pending" pre-fire check can never pass on that path. On 11-12 the run was held for 9 minutes and the alert was misattributed twice.

## Scope
- Keep the rule as it is. `noDataState: Alerting` is the designed signal for a stopped worker, and changing it to OK would hide a dead ai_worker. This is platform-planner's call, against lead-planner's lean (noDataState OK or a guard). The reason is the ai-worker-lag runbook's own rationale.
- Document the expectation where proof runs are planned:
  - `docs/runbooks/alerting-pipeline.md`: a "Proof runs without ai_worker" note. On the named-service path, `AiWorkerLagHigh` is alerting (NoData) from about 2 min after start, and stays alerting until ai_worker runs. A fire test therefore attributes delivery by ntfy's `ntfy_messages_published_success` counter delta, and the pre-fire check is "nothing else alerting except AiWorkerLagHigh".
  - The same line in `docs/runbooks/ntfy-topic-rotation.md`, "Fire test" section.
  - A pointer in `docs/runbooks/ai-worker-lag.md`.
- Also note there: `platform-ai_worker` and `platform-watchdog` images are not built on this host (11-12), so a full `--profile observability up --no-build` fails with "No such image". The named-service list from the 11-12 records is the proof path.
- Verify the inference if it can be done without credentials, for example from Grafana's `grafana_alerting_alerts` per rule if a label exposes the rule. Otherwise keep it stated as inferred.

## Out of Scope
- Changing `rules-worker.yaml`.
- Building the ai_worker or watchdog images.

## Acceptance Criteria
- The three runbooks state the expected alert, the counter-based attribution and the named-service path (validated: review).
- No rule or compose change (validated: diff).

## Related Tickets
- TCK-20261112-ROTATE-LOCAL-NTFY-TOPIC (where it was seen; same branch).
- TCK-20261018-AI-WORKER-SCRAPE-AND-LAG-ALERT (done; added the rule, record docs/runbooks/records/2026-10-26-ai-worker-lag-alert.md).

## Related Docs
docs/runbooks/ai-worker-lag.md
docs/runbooks/alerting-pipeline.md
docs/runbooks/ntfy-topic-rotation.md

## Related Stored Artifacts
None.

## Related Code Areas
docker/grafana/provisioning/alerting/rules-worker.yaml

## Assumptions / Open Questions
- Hotfix tier: documentation only, with self-evident intent.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
