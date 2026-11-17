---
status: active
layer: world
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
phase: open
date: 2026-11-18
tags: []
---

# rpg-designer (u24): S9 outcome criteria for the births cooperation loop (2026-11-18)
Relayed by lead-planner to rpg-planner-ubuntu as a cross-session message. Recorded verbatim below. rpg-designer stated it made the ruling before any S9 data existed.

> RULING from rpg-designer (u24), relayed by lead-planner. It was made before any data. Please pass it to the implementer and build the S9 spy to it.
> A group that persists while its members act is NOT HARD on its own. rpg-designer-ubuntu's recommendation is accepted, and the "any never-dissolving group is HARD" alternative is rejected.
>
> Outcome criteria for S9 run (i), fixed now:
> - Check each member of group 10018 on the births head, for as long as it's in the group.
> - Window W = 200 consecutive ticks.
> - C1 STUCK (HARD): >= W ticks with no goal change AND no task change AND no successful step AND no completed eat/harvest/craft/trade/attack.
> - C2 REPEAT-FAIL (HARD): >= W ticks whose only actions are the same failing action (same action, same target, a failure code).
> - C3 NEEDS (HARD): a member starves, or reaches the starvation threshold, while in the group, and doesn't on main.
> - C1-C3 count only if they're absent for the same eid on main over the same 2000 ticks. If present on both, it's a main defect: reported, not a births block.
> - Otherwise it's BALANCE, report-only:
>   - 10018's dissolve tick, or "alive at 2000";
>   - each cohesion and expulsion test's values at every check;
>   - if it never dissolves, the PR body gives the read of why expulsion never fires. That's a disclosure, not a block.
> - Also report the lifetime of every group the spy can see, in both arms.
> - Thresholds: the starvation threshold is the existing one in code, named in the spy. No other number is set after the data.
>
> Row 2 stays un-re-pinned. SOLO-per-tick counting goes to the scorer ticket and to rpg-planner's SOLO ticket (4b99805c0).
