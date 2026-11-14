---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER
phase: open
date: 2026-11-15
tags: []
---

# TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER: test_plan

- Red now: every attacker of a group opportunity hit acts; cadence window per attacker. Green now (pins): bystander, single-attacker opportunity hit, ordinary attack, hazard/passive drain.
- To add after the ruling: skill and area paths write the tuple; felt_swing group row; digest changes with the field; checkpoint round trip / restore refusal per FIELD_RULES; grid row with a two-attacker group hit shared with ticket 2.
- Scoped command: pytest tests/unit/engine/test_group_hit_records_every_attacker.py tests/unit/engine/test_acting_hostile_is_an_act_not_a_state.py plus checkpoint/digest tests.
