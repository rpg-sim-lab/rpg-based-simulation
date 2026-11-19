---
status: active
layer: engine
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261118-CAMPAIGN-RUNNER-AND-RESTORED-BODIES-SKIP-THE-BUILD-TIME-SENSES-CHECK
date: 2026-11-19
---

# Test plan

- tests/unit/domains/campaigns/test_campaign_bodies_senses.py: unprofiled kind refused naming the site; human builds as before; runner likewise.
- tests/unit/engine/test_restored_body_senses.py: unit refusals (name, cause, missing species); slow restore under content A (state hash equal) and B (refused before any tick).
- tests/unit/content/test_species_null_sense_profile.py: null profile at load names the species.
- tests/unit/world/test_v2entitybuilder_sites_check_senses.py: source scan with an allowlist and a stale-entry guard.
- Regression sweep: campaigns unit, checkpoint tests, content tests, perc02a tests, scenario runtime and its API, campaign integration.

## Proof Plan
- Level: unit, plus one slow save/restore test; no kernel or heavy run.
- Proof kind: regression and refusal tests.
- Oracle source: the rpg-designer rulings (restore strict with a typed error and cause; campaign and runner refuse only an in-content unprofiled species) and divergence 2.210 item 3.
- Expected effect: a body whose species lost its profile is refused before any tick at restore, and at build on the campaign and runner paths; an unknown fixture kind builds at the campaign and runner sites and is refused at restore.
- Selected commands: `python3 -m pytest -q --basetemp=/data/vboxuser/pytest_h1 tests/unit/engine/test_restored_body_senses.py tests/unit/domains/campaigns/test_campaign_bodies_senses.py tests/unit/content/test_species_null_sense_profile.py tests/unit/world/test_v2entitybuilder_sites_check_senses.py`, plus the checkpoint-path and campaign suites listed in the ticket.
