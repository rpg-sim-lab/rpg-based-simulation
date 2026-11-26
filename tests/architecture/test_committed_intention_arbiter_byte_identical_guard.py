"""
Architecture guard for TCK-20260812-COMMITTED-INTENTION-SEQUENCE.

The ticket's central design premise is that a CommittedIntention materializes
as an ordinary tier-5 GoalScore candidate that competes through the
completely unmodified evaluate_project_switch() arbiter. This test pins the
golden SHA-256 hash of that function's source, captured before any
implementation work in this ticket began, so any future edit to the arbiter
itself (accidental or otherwise) fails loudly here instead of silently
invalidating STRAT-185/186/187.
"""
import hashlib
import inspect

import src.systems.strategic_systems.project_switch_rules as switch_rules
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem

# 96 lines, captured pre-TCK-20260812-COMMITTED-INTENTION-SEQUENCE as 635bc4f274f3110c8bd0c130a85bc548e517b4247df33cf426bcec81e6eb80f3.
# Updated deliberately by TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK: evaluate_project_switch now calls suspend_record(current, tick): every SUSPENDED writer sets the clock (N10 ruling, 5b726a2f).
# The only guarded-source change is `replace(current, status=ProjectStatus.SUSPENDED)` -> `suspend_record(current, current_tick)`. Lead (testing authority) yes relayed by rpg-planner; #715 testing-authority record: 6941681673.
# Updated deliberately by TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH (STRAT-359 / divergence 2.228; lead testing-authority yes, #715 7181074486; rpg-designer ruling ff02a9df: STRAT-185/186/187 hold):
# K3 changes the arbiter by design. evaluate_project_switch now calls escalated_need_takes_switch(...) and then ordinary_switch_allows(...), the old lock/margin body moved (the same logic and comments; the scale helpers, constants and threat test are
# read through SwitchEnv) and proven equal by a pre-refactor oracle over 360 combinations. The guard's premise is now "no committed-intention-specific rule in the arbiter", not "byte-identical": the rule is keyed on kind plus need state, never on the
# candidate's source, so a materialized HUNGER or FATIGUE intention gets what a live need candidate gets. The guard does not shrink to the wrapper: the delegated functions and SwitchEnv are pinned below, one golden each.
_GOLDEN_SHA256 = "0bf539bdc723869ed3db344d4f0b19a49773076955dfd0f3f3b275cfcb2f72f6"
_GOLDEN_RULE_SHA256 = "7478a764625842fba898a0944b0bdb01c52598aa77d2e0e1971e5d3867c7e42f"  # project_switch_rules.escalated_need_takes_switch
_GOLDEN_ORDINARY_SHA256 = "41c089008af6fea8f4f0c8f670161d504f303a436447d8fba2ea0f9f5bf882a3"  # project_switch_rules.ordinary_switch_allows (the pre-K3 lock-and-margin body, moved)
_GOLDEN_ENV_SHA256 = "e9edc0afe2f4a9294397cb6d2b34458b9eb1a5f2b5ca7da5ac792aad87ee3997"  # project_switch_rules.SwitchEnv (what the ordinary decision reads from intelligence)


def test_evaluate_project_switch_source_hash_unchanged():
    src = inspect.getsource(StrategicIntelligenceSystem.evaluate_project_switch)
    assert hashlib.sha256(src.encode()).hexdigest() == _GOLDEN_SHA256, (
        "evaluate_project_switch() body changed -- this ticket (TCK-20260812-COMMITTED-INTENTION-SEQUENCE) "
        "requires it to stay byte-identical (AC3). If a change here is genuinely intended for other reasons, "
        "update _GOLDEN_SHA256 deliberately and note why in the commit, not as a silent side effect of this ticket."
    )


def _sha(obj) -> str:
    return hashlib.sha256(inspect.getsource(obj).encode()).hexdigest()


def test_the_arbiter_functions_evaluate_project_switch_delegates_to_are_pinned_too():
    """TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH: the arbiter's logic lives in project_switch_rules.py since K3; each function is pinned so the guard does not shrink to the wrapper."""
    assert _sha(switch_rules.escalated_need_takes_switch) == _GOLDEN_RULE_SHA256, "escalated_need_takes_switch() changed; update the golden deliberately (STRAT-359, divergence 2.228)."
    assert _sha(switch_rules.ordinary_switch_allows) == _GOLDEN_ORDINARY_SHA256, "ordinary_switch_allows() (the STRAT-005/006/186 lock-and-margin body) changed; update the golden deliberately."
    assert _sha(switch_rules.SwitchEnv) == _GOLDEN_ENV_SHA256, "SwitchEnv changed; update the golden deliberately."
