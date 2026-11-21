"""F2 v2.2a (rpg-designer REQUIRED 2): decision 32's "ignore" posture with a goal that became suppressed is the SAME stand as having no goal (an idle update that keeps the strategic update), never
None (None means "go on to fight"), so a suppressed walk does not turn into an attack."""
from dataclasses import replace

from src.core.strategic import BlockerState
from src.engine.tactical_hold import notice_unengaged_hostile
from src.strategy.destination_suppression import access_blocker_id
from tests.unit.engine.test_notice_unengaged_hostile import GOAL, _consumers, _hostile, _state, _walker  # noqa: F401  (the fixture is autouse by name)


def _suppressed(walker):
    blocker = BlockerState(id=access_blocker_id((int(GOAL[0]), int(GOAL[1]))), kind="access", subject=str(GOAL), suppression_until_tick=500, giveup_count=1)
    return replace(walker, strategic=replace(walker.strategic, blockers={blocker.id: blocker}))


def test_an_ignored_hostile_with_a_suppressed_goal_stands_and_does_not_fight():
    w, h = _suppressed(_walker(posture="ignore")), _hostile()
    update = notice_unengaged_hostile(_state(w, h), w, h, [h], None)
    assert update is not None, "None would hand the tick to the attack branch"
    assert update.navigation is None and update.task is None  # a stand: no target_set, no ATTACK, no KEEP_WALKING
    no_goal = _walker(posture="ignore", target=None)
    plain = notice_unengaged_hostile(_state(no_goal, h), no_goal, h, [h], None)
    assert (update.navigation, update.task) == (plain.navigation, plain.task)  # exactly the `goal is None` case


def test_the_same_walk_still_keeps_walking_when_the_goal_is_open():
    w, h = _walker(posture="ignore"), _hostile()
    update = notice_unengaged_hostile(_state(w, h), w, h, [h], None)
    assert update.task.payload_set["reason"] == "KEEP_WALKING" and update.navigation.target_set == GOAL
