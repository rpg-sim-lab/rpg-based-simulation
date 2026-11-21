---
status: historical
layer: economy
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261118-A-SERVICE-PAYMENT-WITH-NO-PAYEE-DESTROYS-COIN
phase: done
date: 2026-11-19
tags: []
---

# Plan
1. Price helper `service_price` = max(0, gold_cost - gold_delta); `paid` = min(payer's running gold, price) (CLAMP, owner decision 44; designer re-ruling Option B).
2. Debit == credit == `paid` (building, else named treasury); no payee: debit 0, `payee_missing` counted (observability only, `PayeeMissingCounts` in core/conservation.py).
3. Tests: resolver balance test over every source_kind; the t3181 shape at resolver and apply level; two charges over the purse; owner-approved edits to two existing tests.
4. Own-job: 4 cells at 5000 ticks, spied plus plain twin; docs: Bible 03, parity TOWN-203, divergence 2.217, mechanisms.yaml, resource_conservation_contract.md.
