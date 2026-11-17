"""World farm step one (T1 to T3): the producer and the anomaly worker resolve ONE stream name and ONE Redis URL.

No Redis server is started: only the resolvers and the names derived from them are checked.
"""

import pytest

from src.observability.anomaly.worker import config_from_env
from src.observability.config import ObservabilityConfig
from src.observability.stream.consumer import RedisStreamConsumer

_VARS = ("SIM_STREAM_NAME", "RPG_STREAM_NAME", "SIM_REDIS_URL", "RPG_REDIS_URL", "SIM_STREAM_BACKEND", "SIM_CONSUMER_GROUP")

# (env, expected stream name, expected redis url): SIM_ first, then RPG_, then the producer's default.
_CASES = {
    "sim_only": ({"SIM_STREAM_NAME": "world_a", "SIM_REDIS_URL": "redis://sim:6379/1"}, "world_a", "redis://sim:6379/1"),
    "rpg_only": ({"RPG_STREAM_NAME": "world_b", "RPG_REDIS_URL": "redis://rpg:6379/2"}, "world_b", "redis://rpg:6379/2"),
    "both": (
        {"SIM_STREAM_NAME": "world_a", "RPG_STREAM_NAME": "world_b", "SIM_REDIS_URL": "redis://sim:6379/1", "RPG_REDIS_URL": "redis://rpg:6379/2"},
        "world_a",
        "redis://sim:6379/1",
    ),
    "neither": ({}, "simulation:events", "redis://localhost:6379/0"),
}


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for name in _VARS:
        monkeypatch.delenv(name, raising=False)


@pytest.mark.parametrize("case", sorted(_CASES))
def test_worker_config_matches_the_producer_resolvers(monkeypatch, case):
    env, stream, url = _CASES[case]
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    config = config_from_env()
    assert ObservabilityConfig.get_stream_name() == stream
    assert ObservabilityConfig.get_redis_url() == url
    assert config.stream_name == ObservabilityConfig.get_stream_name()
    assert config.redis_url == ObservabilityConfig.get_redis_url()


def test_two_worlds_get_separate_streams_groups_and_dlqs(monkeypatch):
    names = {}
    for world in ("world_a", "world_b"):
        monkeypatch.setenv("SIM_STREAM_NAME", world)
        config = config_from_env()
        consumer = RedisStreamConsumer(redis_url=config.redis_url, stream_name=config.stream_name, group_name=config.consumer_group)
        names[world] = (ObservabilityConfig.get_stream_name(), config.stream_name, consumer.dlq_stream_name)
    assert names["world_a"] == ("world_a", "world_a", "world_a:dlq")
    assert names["world_b"] == ("world_b", "world_b", "world_b:dlq")


def test_default_stream_is_unchanged_and_shared_by_every_reader_and_writer():
    assert ObservabilityConfig.get_stream_name() == "simulation:events"
    assert config_from_env().stream_name == "simulation:events"
    assert RedisStreamConsumer().stream_name == "simulation:events"


def test_the_other_worker_settings_are_unchanged(monkeypatch):
    monkeypatch.setenv("SIM_STREAM_BACKEND", "memory")
    monkeypatch.setenv("SIM_CONSUMER_GROUP", "observatory:farm")
    config = config_from_env()
    assert config.stream_backend == "memory"
    assert config.consumer_group == "observatory:farm"
    assert config_from_env.__module__ == "src.observability.anomaly.worker"
