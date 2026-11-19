---
status: historical
layer: economy
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261118-A-SERVICE-PAYMENT-WITH-NO-PAYEE-DESTROYS-COIN
phase: done
date: 2026-11-19
tags: []
---

# Investigation
- Root cause (designer, inspected on 51a6516cf): bed_delta (lodging.py:157) and the inn meal (building_services.py:78) price through gold_delta with gold_cost 0, so the old affordability test never refused them; credit was min(gold, price), debit the full price.
- Trace (S9, summary_sink.txt 13430e6e): on 414fb74f7, cf s46, REST at building 20003 resolved at state tick 3181 with payer 9 holding 0; coin check first read -10 at tick 3182; a same-tick INHERIT hid it from the apply clamp.
- Latent on main: in 51a6516cf cells the apply clamp absorbed 2,751 over-debits (own-job, summary 87266f83); the loss shows only when a same-tick arrival reveals it.
