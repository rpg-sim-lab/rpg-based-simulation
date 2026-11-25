---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261123-A-SUBJECT-REMEMBERS-WHY-A-PLACE-FAILED-AND-RECONSIDERS-IT-BY-THAT-REASON
artifact_type: investigation
tags: []
---

# Investigation: the #996 rework

Written before code, from the approved design plus a grep of `rpg-stalemate-nav` at 4fb41f289. Evidence labels: inspected (read in source), executable (a test or script exists but was not run), executed (run), validated. Nothing here is executed; no pytest has run on this head.

## What was inspected
- `MemoryModel` (`src/core/cognition.py:339`) has six typed sub-models and no `navigation` field; the new one goes LAST with a FIELD_RULES row. (inspected)
- `giveup_filing_update` and `consume_giveup_records` live in `src/systems/strategic_systems/blocker_lifecycle.py:346/379`; `blocker_timeout_suppression` and the `giveup_count` comment are in `src/core/strategic.py:319/349`; `src/content/matrix.py:514` names `giveup_filing_update` as a runtime consumer of `access_giveup_limit`, so the content matrix evidence string must change with step 6. (inspected)
- Gate call sites by grep on this head: 19 lines of `propose_target(` and 5 of `destination_open(`; 37 lines containing `target_set=` (field definitions included). The design counts 20 + 5 = 25 gate calls and 28 writes. The difference is resolved by AST in step 2. (inspected, not reconciled)
- `data/content/strategy/` holds only `blocker_settings.yaml`; `navigation_experience_settings.yaml` is new. (inspected)

## Taken from the design, not re-inspected by me
Line references the design marks "(i)" (movement.py ring check, legality ReasonCodes, `SERVICE_KINDS` at building_services.py:29, STARVING_LINE 95, SLEEP_LINE 98, hold_mode, executor/worker re-emission lines) were inspected by rpg-designer and the lead at 4ab97912e. I re-check each at the step that touches it and record any difference here.

## Open items found so far
- `src/content/matrix.py:514` evidence string, the presenter file for the memory sub-model (named at investigation per the design), and the exact set of existing tests that call the gate without `purpose` are still to be listed in step 2.
- The checkpoint digest architecture test (`tests/architecture/test_state_digest_covers_every_field.py`) will cover the new fields; fixed-arity tuples are now perturbed in place by the main probe fix (#997).
