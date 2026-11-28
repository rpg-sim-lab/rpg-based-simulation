---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261128-AN-ORDINARY-OBSERVER-CANNOT-SEE-A-STILL-SMALL-BODY-OR-A-MEDIUM-ONE-AT-NIGHT
artifact_type: investigation
tags: []
---

# Investigation: why an ordinary observer cannot see a still small body (or a still medium one at night)

**Written at close (2026-11-28), from the filing, PERC-02b's probe and the calibration table; evidence labels per line.**

- Cause (inspected, then executed by the PERC-02b probe, perc02b_gap/probe_c.out): the 02a gate scores sense x signal x (1 - 0.02 d) x terrain x (0.5 + 0.5 alertness) against threshold 0.2. A small body's visibility is `low` (0.3) and baseline vision is `medium` (0.6): the best case is 0.18 < 0.2, so a still small body is never seen beyond touch. At night vision drops two rungs (0.3), so a still medium body also scores 0.18.
- Why not just lower the threshold (executed, calib_table.out): a threshold under 0.135 opens a baseline observer's still hearing and smell (hearing medium x noise low x 0.75 = 0.135; smell low x scent medium x 0.75 = 0.135). Option C keeps the threshold (0.15) above that ceiling and raises the size levels instead (small medium_high, medium high), with a gentler fall-off (0.04, floor 0.05).
- Settings were hard-coded in the gate; they now live in data (one-record catalog family), validated at load (threshold must exceed the still-body ceiling at the default alertness).
- Owner ruling (#715 7237767905): the 02a rows reverse: seen by day at 3, unseen at 14, unseen at night at 3, plus the four two-tile rows.
- Own-job run (executed, run_go1; designer read 52d4175e): see the ticket's Test Summary. Open: hunts not exercised, the crowded_frontier engagement drop is unattributed (own follow-up ticket), perf about 12%.
