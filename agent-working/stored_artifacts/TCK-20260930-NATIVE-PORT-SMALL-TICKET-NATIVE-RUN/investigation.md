---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN
artifact_type: investigation
tags: [ai, agent-monitoring]
---

# Investigation — TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN

Written at close, 2026-11-16. Findings from the three runs, with run ids, tokens and wall time in the ticket's Test Summary:

- The fail path works: `Scope:tag_registry.check_tags_registered` fails through the attested route and the run returns `TAGS_NOT_REGISTERED` (80.8 s, 449,009 tokens).
- The Plan gate works: an unresolved question stopped the run with `NEEDS_HUMAN_INPUT` and the owner answered it.
- Attested gates through Test passed with matching backstop rows; the 2026-10-09 truncated-command failure did not recur.
- The Test phase ran the whole of `tests/tools` in one uncapped process and hit `OSError: Cannot allocate memory` (57 failures, 7 errors). The same tests passed when run capped. Filed as TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS.
- The native run's own report contained claims that did not hold on checking (the ticket lists them).
