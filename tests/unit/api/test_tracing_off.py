"""API request tracing (issue #622, R3) is a strict no-op while no OTLP endpoint is set."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from src.api.tracing import DEFAULT_SAMPLE_RATIO, sample_ratio, setup_tracing, tracing_enabled


@pytest.mark.parametrize("env", [{}, {"OTEL_EXPORTER_OTLP_ENDPOINT": ""}, {"OTEL_EXPORTER_OTLP_ENDPOINT": "   "}])
def test_off_returns_none_and_touches_nothing(env):
    class App:
        def __getattr__(self, name):  # any use of the app fails the test
            raise AssertionError(f"tracing touched app.{name} while off")

    assert tracing_enabled(env) is False
    assert setup_tracing(App(), environ=env) is None


def test_off_imports_no_opentelemetry_sdk_and_installs_nothing():
    """In a clean interpreter: build the real app with the endpoint unset, then look for any SDK import or log hook."""
    code = (
        "import logging, os, sys\n"
        "os.environ.pop('OTEL_EXPORTER_OTLP_ENDPOINT', None)\n"
        "factory = logging.getLogRecordFactory()\n"
        "from src.api.server import create_v2_app\n"
        "from src.config.profiles import PROD_SMALL\n"
        "app = create_v2_app(PROD_SMALL, seed=42, world_id='sandbox_world')\n"
        "assert not [m for m in app.user_middleware if 'opentelemetry' in repr(m)]\n"
        "bad = sorted(m for m in sys.modules if m.startswith(('opentelemetry.sdk', 'opentelemetry.instrumentation', 'opentelemetry.exporter')))\n"
        "assert not bad, bad\n"
        "assert logging.getLogRecordFactory() is factory\n"
        "print('OK')\n"
    )
    repo = Path(__file__).resolve().parents[3]
    env = {k: v for k, v in os.environ.items() if k != "OTEL_EXPORTER_OTLP_ENDPOINT"} | {"PYTHONPATH": str(repo)}
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=repo)
    assert result.returncode == 0, result.stderr[-800:]
    assert "OK" in result.stdout


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(None, DEFAULT_SAMPLE_RATIO), ("", DEFAULT_SAMPLE_RATIO), ("0.5", 0.5), ("1", 1.0), ("0", 0.0), ("2", DEFAULT_SAMPLE_RATIO), ("-1", DEFAULT_SAMPLE_RATIO), ("abc", DEFAULT_SAMPLE_RATIO)],
)
def test_sample_ratio_parsing(raw, expected):
    env = {} if raw is None else {"OTEL_TRACES_SAMPLER_ARG": raw}
    assert sample_ratio(env) == expected
