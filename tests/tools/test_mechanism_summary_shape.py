"""validate() checks the shape of the optional per-mechanism `summary` (TCK-20261111-MECHANISM-SUMMARY-FIELD-SHAPE-CHECK)."""
from pathlib import Path

import pytest
import yaml

from tools.mechanism_registry import registry

_REPO = Path(__file__).resolve().parents[2]


def _data(**extra):
    mech = {"id": "m1", "layer": "L", "state": next(iter(sorted(registry.VALID_STATES)))}
    mech.update(extra)
    return {"layers": {"L": {}}, "mechanisms": [mech]}


def _summary_errors(**extra):
    return [e for e in registry.validate(_data(**extra)) if "summary" in e]


# The fixture is a bare one-mechanism file, so validate() also reports unrelated orphan-system errors; a
# summary only counts as "valid" when it adds nothing to that baseline.
_BASELINE = registry.validate(_data())


def test_absent_summary_is_valid():
    assert registry.validate(_data()) == _BASELINE


def test_valid_summary_passes():
    assert registry.validate(_data(summary="Settles a fight in plain words.")) == _BASELINE


@pytest.mark.parametrize("bad", [42, None, ["a"], {"a": 1}, True])
def test_non_string_summary_is_one_error_naming_the_mechanism(bad):
    errors = _summary_errors(summary=bad)
    assert len(errors) == 1 and "m1" in errors[0]


@pytest.mark.parametrize("bad", ["", "   ", "\n"])
def test_empty_summary_is_one_error(bad):
    errors = _summary_errors(summary=bad)
    assert len(errors) == 1 and "m1" in errors[0]


@pytest.mark.parametrize("bad", ["one\ntwo", "one\r\ntwo", "a\rb"])
def test_multi_line_summary_is_one_error(bad):
    errors = _summary_errors(summary=bad)
    assert len(errors) == 1 and "single line" in errors[0]


def test_committed_registry_has_no_summary_errors():
    data = yaml.safe_load((_REPO / "registries" / "mechanisms.yaml").read_text(encoding="utf-8"))
    assert [e for e in registry.validate(data) if "summary" in e] == []


def test_trailing_line_break_only_is_a_blank_edge_not_multi_line():
    # Surrounding whitespace is stripped once, then both line-break tests run on the stripped text.
    assert _summary_errors(summary="One line.\n") == []
    assert _summary_errors(summary="One line.\r\n") == []
    assert len(_summary_errors(summary="One\rline")) == 1
