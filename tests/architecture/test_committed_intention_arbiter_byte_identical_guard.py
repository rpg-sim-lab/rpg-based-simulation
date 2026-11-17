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

from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem

# 96 lines, captured pre-TCK-20260812-COMMITTED-INTENTION-SEQUENCE as 635bc4f274f3110c8bd0c130a85bc548e517b4247df33cf426bcec81e6eb80f3.
# Updated deliberately by TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK: evaluate_project_switch now calls suspend_record(current, tick): every SUSPENDED writer sets the clock (N10 ruling, 5b726a2f).
# The only guarded-source change is `replace(current, status=ProjectStatus.SUSPENDED)` -> `suspend_record(current, current_tick)`. Lead (testing authority) yes relayed by rpg-planner; #715 testing-authority record: 6941681673.
_GOLDEN_SHA256 = "affc77cf0a7fa2c2a3477f5b4a961c3356ed19f09de384887027d287d29a684a"


def test_evaluate_project_switch_source_hash_unchanged():
    src = inspect.getsource(StrategicIntelligenceSystem.evaluate_project_switch)
    assert hashlib.sha256(src.encode()).hexdigest() == _GOLDEN_SHA256, (
        "evaluate_project_switch() body changed -- this ticket (TCK-20260812-COMMITTED-INTENTION-SEQUENCE) "
        "requires it to stay byte-identical (AC3). If a change here is genuinely intended for other reasons, "
        "update _GOLDEN_SHA256 deliberately and note why in the commit, not as a silent side effect of this ticket."
    )
