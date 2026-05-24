# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the pytfe._logging framework."""

from __future__ import annotations

import json
import logging
from unittest.mock import patch

import httpx
import pytest

from pytfe._logging import (
    REDACTED,
    RoundTrip,
    logger,
    redact_headers,
    setup_logging,
    transport_logger,
)


def _make_response(
    *,
    method: str = "GET",
    url: str = "https://app.terraform.io/api/v2/organizations/acme/workspaces",
    request_headers: dict[str, str] | None = None,
    request_content: bytes | None = None,
    status: int = 200,
    response_headers: dict[str, str] | None = None,
    response_content: bytes = b"",
) -> httpx.Response:
    req = httpx.Request(
        method, url, headers=request_headers or {}, content=request_content
    )
    return httpx.Response(
        status_code=status,
        headers=response_headers or {"content-type": "application/vnd.api+json"},
        content=response_content,
        request=req,
    )


class TestNamespace:
    def test_logger_is_named_pytfe(self):
        assert logger.name == "pytfe"
        assert transport_logger.name == "pytfe.transport"
        # transport_logger inherits from the pytfe root.
        assert transport_logger.parent is logger

    def test_null_handler_attached_by_default(self):
        """Library must not emit anything until the caller opts in."""
        assert any(isinstance(h, logging.NullHandler) for h in logger.handlers), (
            "the pytfe logger must ship with a NullHandler so library use does "
            "not trigger 'No handlers could be found' or bleed into the root logger"
        )


class TestRedactHeaders:
    @pytest.mark.parametrize(
        "header_name",
        [
            "Authorization",
            "authorization",
            "Cookie",
            "Set-Cookie",
            "Proxy-Authorization",
            "X-Tfc-Task-Signature",
            "X-Some-Token",
            "X-API-Key",
            "X-MY-PASSWORD-header",
            "x-secret-thing",
        ],
    )
    def test_redacts_known_sensitive_headers(self, header_name):
        out = redact_headers({header_name: "supersecret"})
        assert out[header_name] == REDACTED

    @pytest.mark.parametrize(
        "header_name",
        ["Content-Type", "Accept", "User-Agent", "X-Request-Id"],
    )
    def test_does_not_redact_normal_headers(self, header_name):
        out = redact_headers({header_name: "demo"})
        assert out[header_name] == "demo"


class TestSetupLogging:
    @pytest.fixture(autouse=True)
    def _reset_logger(self):
        # Each test starts with a clean level for the pytfe logger.
        original = logger.level
        yield
        logger.setLevel(original)

    def test_no_env_no_change(self, monkeypatch):
        """Calling setup_logging with no env var must be a no-op."""
        monkeypatch.delenv("PYTFE_LOG", raising=False)
        logger.setLevel(logging.WARNING)
        setup_logging()
        assert logger.level == logging.WARNING

    def test_pytfe_log_debug_sets_debug(self, monkeypatch):
        monkeypatch.setenv("PYTFE_LOG", "debug")
        setup_logging()
        assert logger.level == logging.DEBUG

    def test_pytfe_log_info_sets_info(self, monkeypatch):
        monkeypatch.setenv("PYTFE_LOG", "info")
        setup_logging()
        assert logger.level == logging.INFO

    def test_pytfe_log_garbage_is_ignored(self, monkeypatch):
        monkeypatch.setenv("PYTFE_LOG", "verbose-please")
        logger.setLevel(logging.WARNING)
        setup_logging()
        assert logger.level == logging.WARNING

    def test_env_var_alone_activates_logging_at_import(self):
        """``PYTFE_LOG=debug python script.py`` must work without the script
        calling ``setup_logging()`` explicitly. Verified by spawning a fresh
        Python with the env var and looking at stderr.
        """
        import subprocess
        import sys

        script = (
            "import logging\n"
            "from pytfe._logging import logger\n"
            # If auto-invoke at import worked, logger.level is DEBUG.
            "print('LEVEL', logging.getLevelName(logger.level))\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            env={"PYTFE_LOG": "debug", "PATH": "/usr/bin:/bin"},
            capture_output=True,
            text=True,
            check=True,
        )
        assert "LEVEL DEBUG" in result.stdout, (
            f"expected logger.level==DEBUG after import with PYTFE_LOG=debug;"
            f" stdout={result.stdout!r} stderr={result.stderr!r}"
        )

    def test_pytfe_log_httpx_lifts_httpx_logger(self, monkeypatch):
        monkeypatch.setenv("PYTFE_LOG", "info")
        monkeypatch.setenv("PYTFE_LOG_HTTPX", "true")
        httpx_logger = logging.getLogger("httpx")
        original = httpx_logger.level
        try:
            setup_logging()
            assert httpx_logger.level == logging.INFO
        finally:
            httpx_logger.setLevel(original)


class TestRoundTripBasics:
    def test_request_and_response_lines(self):
        resp = _make_response(
            response_content=b'{"data": [{"id": "ws-1", "type": "workspaces"}]}'
        )
        out = RoundTrip(resp).generate()
        # Request prefix and response prefix.
        assert out.startswith("> GET /api/v2/organizations/acme/workspaces")
        assert "< 200 OK" in out

    def test_headers_hidden_by_default(self):
        resp = _make_response(
            request_headers={"Authorization": "Bearer s3cr3t", "Accept": "*/*"},
            response_content=b"{}",
        )
        out = RoundTrip(resp).generate()
        # No header lines at all unless debug_headers=True.
        assert "Accept" not in out
        assert "Authorization" not in out

    def test_headers_when_enabled_are_redacted(self):
        resp = _make_response(
            request_headers={
                "Authorization": "Bearer the-actual-token-please-redact",
                "User-Agent": "pytfe/test",
            },
            response_content=b"{}",
        )
        out = RoundTrip(resp, debug_headers=True).generate()
        # Auth value never appears in the log.
        assert "the-actual-token-please-redact" not in out
        assert REDACTED in out
        # Non-sensitive header is fine. httpx lowercases header names.
        assert "user-agent: pytfe/test" in out.lower()


class TestRoundTripBodyRedaction:
    def test_json_body_redacts_sensitive_keys(self):
        body = json.dumps(
            {
                "data": {
                    "type": "team-tokens",
                    "attributes": {
                        "token": "super-secret-token-value",
                        "description": "harmless",
                    },
                }
            }
        ).encode()
        resp = _make_response(response_content=body)
        out = RoundTrip(resp).generate()
        assert "super-secret-token-value" not in out
        assert REDACTED in out
        assert '"description"' in out  # non-sensitive keys still present

    def test_nested_sensitive_key_is_redacted(self):
        body = json.dumps(
            {
                "data": [
                    {
                        "attributes": {
                            "secret": "nested-secret",
                            "name": "team-1",
                        }
                    }
                ]
            }
        ).encode()
        out = RoundTrip(_make_response(response_content=body)).generate()
        assert "nested-secret" not in out
        assert REDACTED in out

    def test_non_json_body_is_logged_verbatim_after_truncation(self):
        resp = _make_response(
            response_headers={"content-type": "text/csv"},
            response_content=b"workspace_name,id\nfoo,ws-1\n",
        )
        out = RoundTrip(resp).generate()
        assert "workspace_name,id" in out
        assert "foo,ws-1" in out


class TestRoundTripTruncation:
    def test_long_string_in_json_is_truncated(self):
        big = "x" * 5000
        body = json.dumps({"description": big}).encode()
        out = RoundTrip(
            _make_response(response_content=body), debug_truncate_bytes=200
        ).generate()
        assert "more bytes" in out
        # Original full payload must NOT survive.
        assert "x" * 5000 not in out

    def test_long_array_is_clipped(self):
        items = [{"i": i, "v": "x" * 50} for i in range(500)]
        body = json.dumps(items).encode()
        out = RoundTrip(
            _make_response(response_content=body), debug_truncate_bytes=200
        ).generate()
        assert "additional elements" in out

    def test_raw_body_marked_as_stream(self):
        # state-version download style — binary content
        resp = _make_response(
            response_headers={"content-type": "application/octet-stream"},
            response_content=b"\x00\x01\x02" * 1000,
        )
        out = RoundTrip(resp, raw=True).generate()
        assert "[raw stream]" in out
        assert "\x00\x01\x02" not in out


class TestTransportIntegration:
    """End-to-end: the HTTPTransport must emit one DEBUG round-trip per request
    when the pytfe.transport logger is at DEBUG, and zero log records when off."""

    def _make_transport(self, handler):
        from pytfe._http import HTTPTransport

        t = HTTPTransport(
            address="https://app.terraform.io",
            token="bearer-token-do-not-log",
            timeout=5,
            verify_tls=True,
            user_agent_suffix=None,
            max_retries=0,
            backoff_base=0,
            backoff_cap=0,
            backoff_jitter=False,
            http2=False,
            proxies=None,
            ca_bundle=None,
        )
        t._sync = httpx.Client(transport=httpx.MockTransport(handler))
        return t

    def test_no_logs_at_default_level(self, caplog):
        """With logging at WARNING (default), the transport must say nothing."""

        def handler(request):
            return httpx.Response(200, json={"data": []})

        t = self._make_transport(handler)
        # Ensure default level
        with patch.object(transport_logger, "level", logging.NOTSET):
            transport_logger.setLevel(logging.WARNING)
            with caplog.at_level(logging.WARNING, logger="pytfe.transport"):
                t.request("GET", "/api/v2/organizations/acme/workspaces")
            assert caplog.records == []

    def test_debug_emits_round_trip(self, caplog):
        """At DEBUG, exactly one round-trip log record per request."""

        def handler(request):
            return httpx.Response(
                200,
                json={"data": [{"id": "ws-1", "type": "workspaces"}]},
                headers={"content-type": "application/vnd.api+json"},
            )

        t = self._make_transport(handler)
        original = transport_logger.level
        try:
            with caplog.at_level(logging.DEBUG, logger="pytfe.transport"):
                t.request("GET", "/api/v2/organizations/acme/workspaces")
            assert len(caplog.records) == 1
            msg = caplog.records[0].getMessage()
            assert "GET /api/v2/organizations/acme/workspaces" in msg
            assert "< 200" in msg
            assert '"id"' in msg or "ws-1" in msg
            # And critically — the bearer token does NOT appear in the formatted
            # output because headers are off by default.
            assert "bearer-token-do-not-log" not in msg
        finally:
            transport_logger.setLevel(original)

    def test_retry_logs_at_info(self, caplog):
        """5xx that triggers a retry must produce an INFO line."""
        call_count = {"n": 0}

        def handler(request):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return httpx.Response(503)
            return httpx.Response(200, json={"data": []})

        from pytfe._http import HTTPTransport

        t = HTTPTransport(
            address="https://app.terraform.io",
            token="x",
            timeout=5,
            verify_tls=True,
            user_agent_suffix=None,
            max_retries=2,
            backoff_base=0,
            backoff_cap=0,
            backoff_jitter=False,
            http2=False,
            proxies=None,
            ca_bundle=None,
        )
        t._sync = httpx.Client(transport=httpx.MockTransport(handler))

        original = transport_logger.level
        try:
            with caplog.at_level(logging.INFO, logger="pytfe.transport"):
                t.request("GET", "/api/v2/organizations/acme/workspaces")
            info_records = [r for r in caplog.records if r.levelno == logging.INFO]
            assert any("retrying" in r.getMessage() for r in info_records), (
                "expected the transport to emit an INFO retry decision on 503"
            )
        finally:
            transport_logger.setLevel(original)
