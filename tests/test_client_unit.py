"""WLC-free unit tests for the RESTCONF client + config.

No live C9800 needed - httpx.MockTransport supplies canned responses, so these run
anywhere (CI included). Run: `uv run pytest`.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest

from wlc_mcp.client import YANG_JSON, WLCAPIError, WLCClient, WLCConnectionError
from wlc_mcp.config import Settings, load_settings


def run(coro):
    return asyncio.run(coro)


def _settings(**kw) -> Settings:
    d = dict(base_url="https://wlc.example.com", username="admin", password="pw",
             verify_ssl=False, timeout=5, retries=2)
    d.update(kw)
    return Settings(**d)


def _client(handler, **kw) -> WLCClient:
    c = WLCClient(_settings(**kw))
    c._http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        auth=httpx.BasicAuth("admin", "pw"),
        headers={"Accept": YANG_JSON, "Content-Type": YANG_JSON},
        follow_redirects=True)
    return c


# --------------------------------------------------------------------------
# config: scheme added, /restconf normalized off, missing raises
# --------------------------------------------------------------------------
def test_load_settings_adds_scheme(monkeypatch):
    monkeypatch.setattr("wlc_mcp.config.load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("WLC_URL", "198.18.128.70")
    monkeypatch.setenv("WLC_USERNAME", "admin")
    monkeypatch.setenv("WLC_PASSWORD", "pw")
    assert load_settings().base_url == "https://198.18.128.70"


def test_load_settings_strips_restconf_suffix(monkeypatch):
    monkeypatch.setattr("wlc_mcp.config.load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("WLC_URL", "https://198.18.128.70/restconf/data")
    monkeypatch.setenv("WLC_USERNAME", "admin")
    monkeypatch.setenv("WLC_PASSWORD", "pw")
    assert load_settings().base_url == "https://198.18.128.70"


def test_load_settings_missing_url_raises(monkeypatch):
    monkeypatch.setattr("wlc_mcp.config.load_dotenv", lambda *a, **k: None)
    monkeypatch.delenv("WLC_URL", raising=False)
    monkeypatch.delenv("WLC_HOST", raising=False)
    with pytest.raises(RuntimeError):
        load_settings()


# --------------------------------------------------------------------------
# _url: model path -> /restconf/data/...; absolute /restconf and http as-is
# --------------------------------------------------------------------------
def test_url_builds_restconf_data_path():
    c = _client(lambda _r: httpx.Response(204))
    assert c._url("Cisco-IOS-XE-wireless-wlan-cfg:wlan-cfg-data") == \
        "https://wlc.example.com/restconf/data/Cisco-IOS-XE-wireless-wlan-cfg:wlan-cfg-data"
    assert c._url("/restconf/") == "https://wlc.example.com/restconf/"
    assert c._url("https://other/x") == "https://other/x"


# --------------------------------------------------------------------------
# request: yang-data headers + JSON body; content-type dispatch; 204 -> None
# --------------------------------------------------------------------------
def test_request_sends_yang_json_headers_and_body():
    seen = {}

    def handler(req):
        seen["accept"] = req.headers.get("accept")
        seen["ctype"] = req.headers.get("content-type")
        seen["body"] = req.content
        return httpx.Response(201)

    run(_client(handler).post("Cisco-IOS-XE-native:native/radius", json_body={"x": 1}))
    assert seen["accept"] == YANG_JSON and seen["ctype"] == YANG_JSON
    assert b'"x"' in seen["body"]


def test_204_returns_none():
    assert run(_client(lambda _r: httpx.Response(204)).delete("x")) is None


def test_json_response_parsed():
    def handler(_r):
        return httpx.Response(200, json={"data": 1}, headers={"content-type": YANG_JSON})
    assert run(_client(handler).get("x")) == {"data": 1}


# --------------------------------------------------------------------------
# RESTCONF error extraction: errors.error[].error-message
# --------------------------------------------------------------------------
def test_restconf_error_extraction():
    def handler(_r):
        return httpx.Response(400, json={"errors": {"error": [
            {"error-tag": "invalid-value", "error-message": "unknown WLAN"}]}})
    with pytest.raises(WLCAPIError) as ei:
        run(_client(handler).get("x"))
    assert ei.value.status_code == 400 and "unknown WLAN" in str(ei.value)


# --------------------------------------------------------------------------
# transport-error wrapping + retry (RESTCONF/nginx not up yet)
# --------------------------------------------------------------------------
def test_transport_error_wrapped_as_connection_error():
    calls = {"n": 0}

    def handler(_r):
        calls["n"] += 1
        raise httpx.ConnectError("connection refused")

    with pytest.raises(WLCConnectionError) as ei:
        run(_client(handler, retries=0).get("x"))
    assert ei.value.status_code == 0 and calls["n"] == 1


def test_transient_transport_error_is_retried():
    calls = {"n": 0}

    def handler(_r):
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("nginx not up yet")
        return httpx.Response(204)

    run(_client(handler, retries=2).get("x"))
    assert calls["n"] == 2
