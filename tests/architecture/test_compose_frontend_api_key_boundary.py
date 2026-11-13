"""Static pins for the compose stack's API-key boundary (TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY and
TCK-20261112-COMPOSE-FRONTEND-API-DOCS-SCHEMA-NOT-PROXIED). No container is started: the behaviour was observed in the
2026-11-12 proof run (agent-working/stored_artifacts/TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY/run-2026-11-12/)."""

import re
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[2]
_NGINX = (_ROOT / "docker" / "nginx.conf").read_text(encoding="utf-8")
_TEMPLATE = (_ROOT / "docker" / "nginx-api-key.conf.template").read_text(encoding="utf-8")
_COMPOSE = yaml.safe_load((_ROOT / "compose.yaml").read_text(encoding="utf-8"))


def _location_block(name: str) -> str:
    match = re.search(r"location " + re.escape(name) + r" \{(.*?)\n    \}", _NGINX, re.S)
    assert match, f"nginx.conf has no `location {name}` block"
    return re.sub(r"#.*", "", match.group(1))


def _env_file_paths(service: str) -> list[str]:
    entries = _COMPOSE["services"][service].get("env_file", [])
    return [e["path"] if isinstance(e, dict) else e for e in entries]


def test_openapi_location_is_exact_and_carries_no_api_key():
    block = _location_block("= /openapi.json")
    assert "proxy_pass http://backend:8000;" in block
    assert 'proxy_set_header X-API-Key "";' in block, "an empty header also drops any client-sent key"
    assert "api-key.conf" not in block, "/openapi.json must never receive the injected key"


def test_only_api_and_openapi_are_proxied():
    code = re.sub(r"#.*", "", _NGINX)
    proxied = re.findall(r"location ([^{]+) \{[^}]*?proxy_pass", code)
    assert sorted(p.strip() for p in proxied) == ["/api/", "= /openapi.json"]


def test_api_location_includes_the_rendered_key_file():
    assert "include /tmp/api-key.conf;" in _location_block("/api/")


def test_template_is_one_line_with_one_variable():
    assert _TEMPLATE.count("${") == 1
    assert _TEMPLATE.strip() == 'proxy_set_header X-API-Key "${FRONTEND_API_KEY}";'


def test_key_pair_is_split_so_each_service_loads_only_its_own_file():
    assert _env_file_paths("backend") == ["./docker/secrets/backend.env"]
    assert _env_file_paths("frontend") == ["./docker/frontend.defaults.env", "./docker/secrets/frontend.env"]
    for service in ("backend", "frontend"):
        for entry in _COMPOSE["services"][service]["env_file"]:
            if isinstance(entry, dict):
                assert entry.get("required") is False, "an absent key file must leave the stack fail-closed, not break it"


def test_tracked_frontend_defaults_define_an_empty_key():
    text = (_ROOT / "docker" / "frontend.defaults.env").read_text(encoding="utf-8")
    assert [ln for ln in text.splitlines() if ln and not ln.startswith("#")] == ["FRONTEND_API_KEY="]


def test_backend_and_frontend_publish_on_loopback_by_default():
    for service, var in (("backend", "BACKEND_BIND"), ("frontend", "FRONTEND_BIND")):
        ports = [str(p) for p in _COMPOSE["services"][service]["ports"]]
        assert any(p.startswith("${" + var + ":-127.0.0.1}:") for p in ports), (service, ports)
