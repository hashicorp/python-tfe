# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Logging primitives for the pytfe SDK.

Design notes
------------
The SDK integrates with Python's standard ``logging`` module. By default the
``pytfe`` logger has a ``NullHandler`` attached, so the library is silent
unless the caller opts in — either by configuring ``logging`` themselves
or by calling :func:`setup_logging`, which honours the ``PYTFE_LOG``
environment variable (``debug`` or ``info``).

Logger namespace
~~~~~~~~~~~~~~~~

  * ``pytfe``           — root namespace; rarely emits directly
  * ``pytfe.transport`` — HTTP transport request/response/retry trace

Anything sensitive (the ``Authorization`` bearer token, any header that
looks like a credential, common JSON keys such as ``token`` / ``password``
/ ``secret``) is replaced with ``**REDACTED**`` before being handed to the
logger. Bodies are truncated to ``PYTFE_LOG_TRUNCATE_BYTES`` (default
``1024``) so DEBUG-level traffic doesn't fill a TTY when listing 10,000
workspaces.

"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Mapping
from typing import Any

import httpx

__all__ = [
    "logger",
    "transport_logger",
    "setup_logging",
    "RoundTrip",
    "redact_headers",
    "REDACTED",
]

REDACTED = "**REDACTED**"

# Per-namespace loggers. Library code uses these directly; users wire
# handlers/levels onto them.
logger: logging.Logger = logging.getLogger("pytfe")
transport_logger: logging.Logger = logging.getLogger("pytfe.transport")

# Library best practice: install a NullHandler so the absence of caller
# configuration doesn't trigger "No handlers could be found" warnings or
# bubble logs up to the root logger.
if not any(isinstance(h, logging.NullHandler) for h in logger.handlers):
    logger.addHandler(logging.NullHandler())


# Header names that should never appear in plain text. Matched
# case-insensitively against incoming/outgoing headers.
_SENSITIVE_HEADER_NAMES = frozenset(
    {
        "authorization",
        "cookie",
        "set-cookie",
        "proxy-authorization",
        "x-tfc-task-signature",
    }
)

# Header-name substrings that imply sensitivity even when not in the
# explicit list above (third-party run-task webhooks, custom signing
# headers, etc.).
_SENSITIVE_HEADER_SUBSTRINGS = ("token", "secret", "password", "api-key", "apikey")

# JSON keys whose values are redacted recursively in body dumps.
# Both snake_case and hyphenated forms are listed because the JSON:API
# wire format hyphenates ("private-key") and the comparison below is a
# case-insensitive set membership test, not a normalising one.
# X.509 certificate fields ("idp-cert", "certificate") are deliberately
# NOT redacted — those are public material by design and redacting them
# hurts debugging without protecting anything.
_SENSITIVE_JSON_KEYS = frozenset(
    {
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "password",
        "private_key",
        "private-key",
        "client_secret",
    }
)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return max(int(raw), 96)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _is_sensitive_header(name: str) -> bool:
    n = name.lower()
    if n in _SENSITIVE_HEADER_NAMES:
        return True
    return any(s in n for s in _SENSITIVE_HEADER_SUBSTRINGS)


def redact_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Return a copy of ``headers`` with sensitive values replaced."""
    return {k: (REDACTED if _is_sensitive_header(k) else v) for k, v in headers.items()}


def setup_logging() -> None:
    """Convenience configurator driven by environment variables.

    Honours:

      * ``PYTFE_LOG``                  — ``debug`` or ``info`` (case-insensitive).
                                          Anything else is ignored.
      * ``PYTFE_LOG_HTTPX``            — if truthy, also raise ``httpx`` to the
                                          same level so low-level connection
                                          activity is visible.

    Calls ``logging.basicConfig`` with a one-line format if no handlers are
    already configured on the root logger. Idempotent and safe to call
    multiple times.
    """
    env = (os.environ.get("PYTFE_LOG") or "").strip().lower()
    if env not in {"debug", "info"}:
        return

    level = logging.DEBUG if env == "debug" else logging.INFO

    # Only configure handlers if the root logger has none — don't fight
    # callers who've already set up their own logging.
    if not logging.getLogger().handlers:
        logging.basicConfig(
            format="[%(asctime)s %(name)s %(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    logger.setLevel(level)

    if _env_bool("PYTFE_LOG_HTTPX", default=False):
        logging.getLogger("httpx").setLevel(level)


class RoundTrip:
    """Format an httpx request/response pair for debug logging.

    Parameters
    ----------
    response:
        The ``httpx.Response`` returned by the transport. Its ``request``
        attribute supplies the outbound side.
    debug_headers:
        When ``True``, include request/response headers in the formatted
        output. Defaults to the value of ``PYTFE_LOG_HEADERS`` (false).
    debug_truncate_bytes:
        Per-string truncation budget. Defaults to ``PYTFE_LOG_TRUNCATE_BYTES``
        (``1024``). Values below ``96`` are clamped up.
    raw:
        When ``True``, mark the bodies as ``[raw stream]`` and skip body
        formatting. Use this for binary content (state-version downloads,
        configuration-version tarballs, etc.).
    """

    def __init__(
        self,
        response: httpx.Response,
        *,
        debug_headers: bool | None = None,
        debug_truncate_bytes: int | None = None,
        raw: bool = False,
    ) -> None:
        self._response = response
        self._raw = raw
        self._debug_headers = (
            debug_headers
            if debug_headers is not None
            else _env_bool("PYTFE_LOG_HEADERS", default=False)
        )
        self._debug_truncate_bytes = max(
            debug_truncate_bytes
            if debug_truncate_bytes is not None
            else _env_int("PYTFE_LOG_TRUNCATE_BYTES", 1024),
            96,
        )

    # ------------------------------------------------------------------
    # Public formatting
    # ------------------------------------------------------------------

    def generate(self) -> str:
        request = self._response.request
        # httpx.URL has .path / .query (bytes) — render in a way matching
        # what the wire saw, but with query unquoted for human reading.
        from urllib.parse import unquote, urlparse

        url = urlparse(str(request.url))
        query = f"?{unquote(url.query)}" if url.query else ""
        path = unquote(url.path) or "/"

        sb: list[str] = [f"> {request.method} {path}{query}"]

        if self._debug_headers:
            for k, v in redact_headers(dict(request.headers)).items():
                sb.append(f"> * {k}: {self._only_n_bytes(v)}")

        if self._raw and request.content:
            sb.append("> [raw stream]")
        elif request.content:
            sb.append(self._redacted_dump("> ", request.content))

        sb.append(
            f"< {self._response.status_code} {self._response.reason_phrase or ''}".rstrip()
        )

        if self._debug_headers:
            for k, v in redact_headers(dict(self._response.headers)).items():
                sb.append(f"< * {k}: {self._only_n_bytes(v)}")

        if self._raw:
            sb.append("< [raw stream]")
        else:
            try:
                content = self._response.content
            except Exception:
                content = b""
            if content:
                sb.append(self._redacted_dump("< ", content))

        return "\n".join(sb)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.generate()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _only_n_bytes(self, s: str) -> str:
        encoded = s.encode("utf-8", errors="replace")
        if len(encoded) <= self._debug_truncate_bytes:
            return s
        truncated = encoded[: self._debug_truncate_bytes].decode(
            "utf-8", errors="replace"
        )
        return (
            f"{truncated}... ({len(encoded) - self._debug_truncate_bytes} more bytes)"
        )

    def _redacted_dump(self, prefix: str, body: bytes | str) -> str:
        if isinstance(body, bytes):
            try:
                body = body.decode("utf-8")
            except UnicodeDecodeError:
                body = repr(body[:64]) + " ...binary..."
        if not body:
            return ""
        try:
            parsed = json.loads(body)
        except (json.JSONDecodeError, TypeError):
            return "\n".join(
                f"{prefix}{line}" for line in self._only_n_bytes(body).splitlines()
            )
        marshalled = self._recursive_marshal(parsed, self._debug_truncate_bytes)
        rendered = json.dumps(marshalled, indent=2, sort_keys=True)
        return "\n".join(f"{prefix}{line}" for line in rendered.splitlines())

    def _recursive_marshal(self, v: Any, budget: int) -> Any:
        if isinstance(v, dict):
            out: dict[str, Any] = {}
            for k in sorted(v.keys()):
                if isinstance(k, str) and k.lower() in _SENSITIVE_JSON_KEYS:
                    out[k] = REDACTED
                    continue
                marshalled = self._recursive_marshal(v[k], budget)
                out[k] = marshalled
                budget -= len(str(marshalled))
            return out
        if isinstance(v, list):
            out_list: list[Any] = []
            for i, item in enumerate(v):
                if i > 0 and budget <= 0:
                    out_list.append(
                        f"... ({len(v) - len(out_list)} additional elements)"
                    )
                    break
                marshalled = self._recursive_marshal(item, budget)
                out_list.append(marshalled)
                budget -= len(str(marshalled))
            return out_list
        if isinstance(v, str):
            return self._only_n_bytes(v)
        return v


# Auto-apply environment configuration at import. This is what makes
# ``PYTFE_LOG=debug python my_script.py`` work without the caller adding
# any code. Safe by design:
#
#   * No-op unless ``PYTFE_LOG`` is set to ``debug`` or ``info``.
#   * Only calls ``logging.basicConfig`` if the root logger has no
#     handlers, so existing caller configuration is preserved.
#   * Only sets the level on the ``pytfe`` namespace; the root logger
#     and other libraries are untouched.
setup_logging()
