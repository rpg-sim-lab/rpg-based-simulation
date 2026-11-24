---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261124-STATE-DIGEST-PROBE-SKIPS-A-SYNTHESIZED-RECORD-WHOSE-ID-WAS-REUSED
phase: done
date: 2026-11-24
tags: []
---

# investigation - TCK-20261124-STATE-DIGEST-PROBE-SKIPS-A-SYNTHESIZED-RECORD-WHOSE-ID-WAS-REUSED

visit() adds id(o) to seen; a synthesized record is installed, visited and freed when perturb restores the field, so its id can be reissued. Real address reuse could not be forced (the freed block is taken by other allocations); an id recycler patched in as probe.id models it.
