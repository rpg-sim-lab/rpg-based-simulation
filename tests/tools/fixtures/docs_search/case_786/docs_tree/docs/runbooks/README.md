---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability]
---

21: | `ApiErrorRateHigh` | 2m | [api-latency-slo.md](api-latency-slo.md) | not drilled |
22: | `LogShippingErrors` | 10m | [log-shipping.md](log-shipping.md) | live proof: a stopped promtail, a fresh promtail against the 403, and a quiet stack (see the promtail record) |
23: | `RedisDown` (cause alert) | 30s | [redis-down.md](redis-down.md) | the Redis-stop drill under load (see `records/`) |
