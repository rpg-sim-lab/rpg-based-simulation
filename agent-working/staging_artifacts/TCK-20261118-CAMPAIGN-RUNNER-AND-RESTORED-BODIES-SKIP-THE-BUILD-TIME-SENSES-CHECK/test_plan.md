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
