"""TCK-20261116-A-TEST-KERNEL-DOES-NOT-DEGRADE-BECAUSE-AN-EARLIER-TEST-USED-MEMORY: the lodging test kernel does not read the process's live memory.

The default governor derives its tier from the process RSS against ``max_ram_mb``. A whole-tree AST scan in an earlier test raised the RSS for good, so the next kernel
started DEGRADED and decided less often (a decision count of 1 where the low-hp test needs 2). The helper pins ``PinnedNormalGovernor`` by default. Here the RSS signal is
raised above the profile's ``max_ram_mb`` directly, so no heavy run is needed."""
from __future__ import annotations

import pytest

from src.engine.observability import SignalCollector
from tests.unit.engine.lodging_kernel import REACH, hero, kernel, profile


@pytest.fixture
def huge_rss(monkeypatch):
    """What the process looks like after a large scan: the sampled RSS far above the profile's limit."""
    over = profile().max_ram_mb * 20.0
    monkeypatch.setattr(SignalCollector, "collect_platform_signals", lambda self, tick, interval_override=None: {"rss_mb": over, "memory_trend": 0.0})


def test_the_helper_kernel_stays_normal_when_the_process_rss_is_over_the_profile_limit(huge_rss):
    k = kernel([hero(1, REACH[0])])
    try:
        for _ in range(3):
            k.tick_once()
        assert k._status.current_mode.name == "NORMAL"
    finally:
        k.shutdown()


def test_a_caller_can_still_pass_its_own_governor(huge_rss):
    from src.engine.governor import ResourceGovernor
    own = ResourceGovernor()
    k = kernel([hero(1, REACH[0])], governor=own)
    try:
        assert k._governor is own
    finally:
        k.shutdown()


def test_the_low_hp_target_decides_at_least_twice_with_the_rss_over_the_limit(huge_rss, monkeypatch):
    """The failing test itself, run under the raised RSS: it asserts its own decision count (>= 2), which a DEGRADED kernel did not reach."""
    from tests.unit.tactical.test_low_hp_retreat_gate import test_a_held_retreat_does_not_walk_a_stored_target_through_the_kernel as target
    target(monkeypatch)
