"""Town-tile healing obeys the starving line (Bible 01 Staged Starvation D36 and Natural Healing D42): at hunger >= 95 nothing heals, so a starving body in town
loses HP on the starvation schedule and gains none; one point below the line it still heals as before. Each starving case has a control that the same setup heals
without the gate, so the test could fail."""
from __future__ import annotations

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.engine import town_resolution
from src.engine.starvation import STARVING_LINE, hp_loss
from src.engine.town_resolution import TownResolutionSystem

TILE = (5, 5)
MAX_HP = 20


def _body(hunger: float, hp: int = 10, eid: int = 3):
    return V2EntityBuilder(eid).kind("peasant").location(float(TILE[0]), float(TILE[1])).combat(hp=hp, max_hp=MAX_HP).biological(hunger=hunger).build()


def _state(entity, tick: int = 40) -> AuthoritativeState:
    return AuthoritativeState(tick=tick, seed=1, entities={entity.id: entity}, town_tiles={TILE})


def _town_heal(entity, tick: int = 40) -> int:
    """The hp the town-tile healing grants the body on this town-resolution pass (0 when it grants none)."""
    out = TownResolutionSystem.resolve(_state(entity, tick), StateUpdate())
    upd = out.entity_updates.get(entity.id)
    return int(upd.combat.hp_delta or 0) if upd is not None and upd.combat is not None else 0


def test_the_line_is_the_one_the_starvation_drain_uses():
    assert STARVING_LINE == 95


@pytest.mark.parametrize("hunger", [95, 96, 100])
def test_a_starving_body_on_a_town_tile_gets_no_heal(hunger):
    assert _town_heal(_body(hunger)) == 0


@pytest.mark.parametrize("hunger", [0, 50, 84, 94, 94.9])
def test_a_body_below_the_line_on_a_town_tile_still_heals_as_before(hunger):
    assert _town_heal(_body(hunger)) == 1


def test_the_boundary_is_94_against_95():
    assert (_town_heal(_body(94)), _town_heal(_body(95))) == (1, 0)


def test_a_full_health_body_is_never_healed_in_town():
    assert _town_heal(_body(10, hp=MAX_HP)) == 0


def test_a_starving_body_in_town_loses_hp_on_the_starvation_schedule_and_gains_none():
    """Replay the apply path's loss with the town pass's heal: the net is exactly the drain's schedule."""
    hp, ticks = 10, range(1, 2400)
    losses = sum(hp_loss(95.0, MAX_HP, t, 3) for t in ticks)
    assert losses > 0
    for t in ticks:
        hp += _town_heal(_body(95.0, hp=hp), tick=t)
        hp -= hp_loss(95.0, MAX_HP, t, 3)
    assert hp == 10 - losses


def test_control_the_same_starving_setup_heals_when_the_gate_is_lifted(monkeypatch):
    """Failing control: with the line out of reach the starving body is healed again, so the zero above is the gate's doing and not the setup's."""
    monkeypatch.setattr(town_resolution, "STARVING_LINE", 1000)
    assert _town_heal(_body(100)) == 1


# ---- the tick a body crosses the line: the gate reads the hunger the apply path tests the drain against (post-accrual), not the prior tick's
from src.engine.biological_needs import need_rates  # noqa: E402
from src.engine.apply import ApplyPath  # noqa: E402
from src.engine.cadence import SystemCadence  # noqa: E402

CROSSING = STARVING_LINE - need_rates(_body(0))[0] / 2  # one biological accrual step carries it over the line


def test_a_body_that_crosses_the_line_this_tick_gets_no_town_heal_this_tick():
    body = _body(CROSSING)
    assert body.biological.hunger < STARVING_LINE  # the prior state is still under the line
    assert _town_heal(body, tick=40) == 0


def test_the_crossing_body_is_not_healed_through_the_real_apply_path_either():
    body = _body(CROSSING, hp=10)
    state = _state(body, tick=40)
    out = TownResolutionSystem.resolve(state, StateUpdate())
    after = ApplyPath.apply_generation(state, out, next_tick=41, cadence=SystemCadence(), passive=True)
    assert after.entities[body.id].biological.hunger >= STARVING_LINE  # it did cross on this apply
    assert after.entities[body.id].combat.hp <= 10  # and gained nothing


def test_control_the_crossing_body_is_healed_when_the_gate_reads_the_prior_hunger(monkeypatch):
    """Failing control: a gate on the prior tick's hunger lets the crossing body heal once, which is the leak the post-accrual read closes."""
    monkeypatch.setattr(town_resolution, "_hunger_when_applied", lambda entity, tick, cadence: entity.biological.hunger)
    assert _town_heal(_body(CROSSING)) == 1


def test_a_body_just_under_the_line_on_a_tick_with_no_biological_step_still_heals():
    """With a biological cadence of 4 the apply tick 41 does not accrue (41 % 4 != 0), so hunger stays under the line and the heal stands."""
    out = TownResolutionSystem.resolve(_state(_body(CROSSING), tick=40), StateUpdate(), SystemCadence(biological=4))
    assert out.entity_updates[3].combat.hp_delta == 1


@pytest.mark.parametrize("hunger,cadence", [(0.0, 1), (50.0, 1), (94.96, 1), (94.9, 4), (99.99, 1), (100.0, 1), (100.0, 4), (95.0, 7)])
def test_hunger_after_accrual_is_the_inline_accrual_expression(hunger, cadence):
    """The shared helper is the expression the apply path used inline, clamp at 100 included."""
    from src.engine.biological_needs import hunger_after_accrual

    body = _body(hunger)
    assert hunger_after_accrual(body, cadence) == min(100.0, hunger + need_rates(body)[0] * cadence)
