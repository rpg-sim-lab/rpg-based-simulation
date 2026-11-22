---
status: active
layer: simulation
authority: P1
audience: agent
artifact_type: report
ticket_id: TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES
date: 2026-11-21
tags: []
---

# O3 trace brief from rpg-planner (u24), relayed word for word

Provenance: rpg-planner (u24) -> lead-planner-u24 -> lead-planner -> rpg-planner-ubuntu, session message 2026-11-21. The u24 file is `.claude/handover/drafts/rpg-planner-o3-trace-brief.md` (sha256 cd27e75a88f8a39d…, as relayed). Owner ruling option A (#715 7063603750): the whole gate re-record waits for this trace; the gate v3 recorded after it becomes M1's reference, and births waits for that re-record. The ticket is on u24's rpg-planner-tickets-5 at 9b282b821 and not yet pushed.

Lead-planner's notes, outside the brief (word for word):
- The scope is bigger than the first ask: 3 seeds (s42, s45, plus the s43 control) x 2 arms (NEW 87792e3e8, BASE e72270894) x plain + spy = 12 processes. On cores 4-5 that's at most 2 at a time, so please put a time estimate in the record set.
- BASE e72270894 predates #978/#981/#980. Running it from the shared .venv (main's lock) is fine if the kit imports work there, but state it in the record set.
- Routing: when the kit is ready, send me its shas (spy, summarizer, runner, launcher, controls) before or alongside the designer ask. I'll forward them to rpg-planner (u24) through lead-planner-u24, so it can check them before the designer approves.

----- BRIEF -----
# O3 trace brief (rpg-planner, 2026-11-21): FLW meat attacks on people, for an ubuntu lane
## Why
Owner-ordered attribution before the gate re-record. FLW meat O3.attacks_on_people per seed s42..s46: baseline v2 (e72270894) 0,0,0,3,0, candidate (87792e3e8) 51,5,0,59,5. Your split (#715 7063400557): #953 night +17.6 alone, #954 suspended-project expiry +19.6 alone, #955 PERC-02a brings it to +23.4. rpg-designer ruled it a BUG CANDIDATE until this trace clears it (rule pre-set before data, below).
## Cells
- frontier_living_world s42 and s45 (the two heavy seeds) and s43 (REQUIRED quiet control: 5 in the candidate; all rules apply and must not fire on a normal seed).
- 5000 ticks (the gate length; state it in the output); 5000t = 2.08 days at 2400 t/day.
- Two arms, each on a FRESH git archive tree: NEW = main 87792e3e8; BASE = e72270894 (the v2 run's sha), so both arms get the same report at the same length.
- Each cell: the PLAIN twin first, then the spy, with twin hash equality (the spy must not perturb the run). That's 6 plain + 6 spy = 12 processes.
## What the spy records (read-only wrappers, no production change)
For every attack event whose victim is a person (the gate's own O3 definition; quote the counting code with file:line in the kit note): tick, attacker id/kind/species/diet, victim id/kind, hit or miss, the victim's outcome at the end of the engagement.
Derived in the summarizer:
(a) UNIT: O3's count as the gate defines it, plus engagements (attacks by one attacker on one victim with gaps <= 50t; a gap > 50t opens a new one).
(b) per attacker: id, kind, species, diet, engagements, hits, distinct victims, day/night split of engagements (calendar.is_night; day = the waking half from t3000).
(c) per (attacker, victim) pair: engagements and outcome (victim killed / fled / attacker fled / unresolved at run end).
(d) per engagement: inside the attacker's kind's active period (SURV-08) or not.
(e) per hit: the victim's state (asleep / lodged / awake), its movement mode, and whether its next tactical decision is flight (or fight).
Also: which entities the gate places in the 'meat' group for O3, and how (file:line).
## Pre-set rule (rpg-designer, BEFORE data)
INTENDED only if ALL hold in every seed with >= 10 engagements:
R1 every attacker in the meat group has a meat diet (if not, a metric-grouping finding for testing, and that seed is no evidence).
R2 no single attacker has > 50% of the seed's engagements.
R3 no attacker has > 3 engagements on people per in-game day (2400t).
R4 no (attacker, victim) pair has >= 5 engagements.
R5 >= 90% of engagements inside the attacker's active period.
R6 in every seed with >= 10 HITS on people, NEW's hits per engagement (median and max) <= 2x BASE's, OR (BASE has no engagements AND NEW's max <= 10 hits); else a BUG CANDIDATE (fight-duration change), naming the engagements.
R7 no person takes >= 3 hits while asleep or lodged without waking, and no person takes >= 5 consecutive hits with no flight or fight decision between them; else a BUG CANDIDATE (wake-on-hit or freeze defect).
Any miss = BUG CANDIDATE with the attacker ids named. Rules only tighten.
## Facts already established (inspected by rpg-planner on 87792e3e8)
- O3 counts HITS: src/observability/run_ledger.py _count_attacks (~:282-293) adds +1 per entity update with combat.attacker_id set and hp_delta < 0; src/observability/rpg_gate_metrics.py _combat_rows (~:398-410) sums the victim_person == "1" keys. There is no engagement grouping.
- The meat row is chosen by diet: kind_group = species_kind_group(species_of(entity)) (src/ai/goals/kind_group.py); _is_wild_meat_eater keeps attackers where _group_has(group,'meat') and not a person (rpg_gate_metrics.py ~:139-143). Group 'none' (the undead) cannot be in the FLW meat row.
- Gate artifacts are unreachable from u24 (HTTP 403 on the blob hosts), so BASE is the trace's own BASE arm.
- When bisecting, use each report's own `sha` field, not the run's headSha (run 44046941133 measured d42be44ab, not 61a5a9206).
## Approval path
1. The kit (spy, summarizer, runner, launcher) plus planted controls for the engagement split and R1-R7 (for R6/R7, one firing and one non-firing case) go to rpg-designer for sha approval, via rpg-planner and the leads.
2. Trees built and verified against ls-tree; no data/runs.
3. The ubuntu lead records the S9 (own job, trees and shas) before the start.
4. The run, then raw JSONs, then rpg-designer's own recount. Nothing is deleted; out dirs are new.
----- END -----
