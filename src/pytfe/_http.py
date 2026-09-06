# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import logging
import random
import re
import time
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import urljoin

import httpx

from ._jsonapi import build_headers, parse_error_payload
from ._logging import RoundTrip, transport_logger
from .config import RequestInfo, request_info
from .errors import (
    AuthError,
    NotFound,
    RateLimited,
    ReadOnlyViolation,
    ServerError,
    TFEError,
)

_RETRY_STATUSES = {429, 502, 503, 504}

ABSOLUTE_URL_RE = re.compile(r"^https?://", re.I)


class _NoStoreCookies(httpx.Cookies):
    """A cookie jar that never retains anything.

    This SDK authenticates with a bearer token, never cookies. Some endpoints
    (notably ``/api/meta/ip-ranges``) return a session cookie which, if kept,
    silently overrides bearer auth and produces 401/404 on later requests.
    Refusing at the jar covers the upload paths that bypass ``request()``.
    """

    def extract_cookies(self, response: httpx.Response) -> None:
        return None


#: Actionable next step per HTTP status, surfaced as ``TFEError.hint``.
def _hint_for(status: int, errors: list[dict | str]) -> str | None:
    if status == 401:
        return (
            "Token missing, invalid, or expired. Set TFE_TOKEN or TFEConfig(token=...)."
        )
    if status == 403:
        return (
            "Token lacks permission for this organization/workspace. Check team "
            "access and token type (user/team/organization)."
        )
    if status == 404:
        return (
            "Not found. Verify names with client.organizations.list() or "
            "client.workspaces.list('<org>')."
        )
    if status == 409:
        return (
            "Conflict - often a locked workspace or a run already in progress. "
            "See pytfe.workflows.workspace_status / lock / unlock."
        )
    if status == 422:
        fields = _invalid_fields(errors)
        if fields:
            return "Invalid request fields: " + "; ".join(fields)
        return (
            "The API rejected the request body. Check required fields and enum values."
        )
    if status == 429:
        return "Rate limited. The transport already retried; slow down or reduce concurrency."
    if status >= 500:
        return "Server error. Retry later, or check the Terraform Enterprise instance health."
    return None


def _invalid_fields(errors: list[dict | str]) -> list[str]:
    """Map JSON:API 422 ``source.pointer`` values to Python option field names."""
    out: list[str] = []
    for err in errors:
        if not isinstance(err, dict):
            continue
        pointer = (err.get("source") or {}).get("pointer")
        if not isinstance(pointer, str) or "/" not in pointer:
            continue
        wire = pointer.rsplit("/", 1)[-1]
        detail = err.get("detail") or err.get("title") or ""
        out.append(f"'{wire}' (options field '{wire.replace('-', '_')}'): {detail}")
    return out


class HTTPTransport:
    def __init__(
        self,
        address: str,
        token: str,
        *,
        timeout: float,
        verify_tls: bool,
        user_agent_suffix: str | None,
        max_retries: int,
        backoff_base: float,
        backoff_cap: float,
        backoff_jitter: bool,
        http2: bool,
        proxies: str | None,
        ca_bundle: str | None,
        read_only: bool = False,
        before_request: Callable[[RequestInfo], None] | None = None,
    ):
        self.base = address.rstrip("/")
        self.headers = build_headers(user_agent_suffix)
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        self.timeout = timeout
        self.verify = verify_tls
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_cap = backoff_cap
        self.backoff_jitter = backoff_jitter
        self.http2 = http2
        self.proxies = proxies
        self.ca_bundle = ca_bundle
        self.read_only = read_only
        self.before_request = before_request
        # The gate lives on the httpx client, not in request(), because two
        # upload paths (configuration_version.upload_tar_gzip and
        # registry_module.upload_tar_gzip) issue self._sync.put(...) directly
        # and never reach request(). An event hook is the only chokepoint that
        # sees every request this client makes.
        self._sync = httpx.Client(
            http2=http2,
            timeout=timeout,
            verify=ca_bundle or verify_tls,
            proxy=proxies,
            event_hooks={"request": [self._gate]},
        )
        # A Set-Cookie from any endpoint would otherwise override bearer auth on
        # later requests. request() clears the jar per response, but the two
        # bypass PUTs above do not, so refuse cookies at the jar instead.
        self._sync.cookies = _NoStoreCookies()

    def _gate(self, request: httpx.Request) -> None:
        """Enforce read-only and run the caller's ``before_request`` hook.

        Runs for every request the underlying client issues, including the
        absolute-URL uploads that bypass :meth:`request`.
        """
        info = request_info(request.method, str(request.url))
        if self.read_only and info.is_write:
            raise ReadOnlyViolation(info.method, info.path)
        if self.before_request is not None:
            self.before_request(info)

    def _build_url(self, path: str) -> str:
        # IMPORTANT: don't prefix absolute URLs (hosted_state, signed blobs, etc.)
        if ABSOLUTE_URL_RE.match(path):
            return path
        return urljoin(self.base, path.lstrip("/"))

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        allow_redirects: bool = True,
        include_auth: bool = True,
    ) -> httpx.Response:
        url = self._build_url(path)
        hdrs = dict(self.headers)
        if not include_auth:
            hdrs.pop("Authorization", None)
        if headers:
            hdrs.update(headers)
        attempt = 0
        while True:
            try:
                resp = self._sync.request(
                    method,
                    url,
                    params=params,
                    json=json_body,
                    content=data,
                    headers=hdrs,
                    follow_redirects=allow_redirects,
                )
            except httpx.HTTPError as e:
                transport_logger.debug(
                    "transport exception on %s (attempt %d): %s",
                    method,
                    attempt,
                    e,
                )
                if attempt >= self.max_retries:
                    raise ServerError(str(e)) from e
                self._sleep(attempt, None)
                attempt += 1
                continue
            # Belt and braces with the _NoStoreCookies jar installed in
            # __init__: callers (and tests) may swap out self._sync, which
            # would otherwise silently drop the jar-level guarantee.
            if self._sync.cookies:
                self._sync.cookies.clear()
            if resp.status_code in _RETRY_STATUSES and attempt < self.max_retries:
                retry_after = _parse_retry_after(resp)
                transport_logger.info(
                    "retrying %s after %s (status=%d, attempt=%d)",
                    method,
                    f"{retry_after:.2f}s" if retry_after else "backoff",
                    resp.status_code,
                    attempt,
                )
                self._sleep(attempt, retry_after)
                attempt += 1
                continue
            # When the caller explicitly opted out of redirect-following,
            # surface 3xx responses to them (so they can read Location)
            # rather than treating them as errors.
            if not allow_redirects and 300 <= resp.status_code < 400:
                self._log_round_trip(resp)
                return resp
            self._log_round_trip(resp)
            self._raise_if_error(resp)
            return resp

    def _log_round_trip(self, resp: httpx.Response) -> None:
        """Emit a DEBUG-level request/response trace when enabled.

        Cheap when disabled: ``isEnabledFor(DEBUG)`` short-circuits before any
        body decoding or JSON parsing happens.
        """
        if not transport_logger.isEnabledFor(logging.DEBUG):
            return
        # Treat binary content types as raw streams so we don't try to JSON
        # parse a state-version download or a CV tarball.
        ct = (resp.headers.get("content-type") or "").lower()
        raw = not (
            "json" in ct
            or ct.startswith("text/")
            or ct == ""
            or "application/vnd.api+json" in ct
        )
        transport_logger.debug("\n%s", RoundTrip(resp, raw=raw).generate())

    def _sleep(self, attempt: int, retry_after: float | None) -> None:
        if retry_after is not None:
            time.sleep(retry_after)
            return
        delay = min(self.backoff_cap, self.backoff_base * (2**attempt))
        if self.backoff_jitter:
            # Without jitter, every worker sharing a client wakes at the same
            # instants after a 429 and thunder-herds the API. Full jitter, as
            # in the AWS "Exponential Backoff and Jitter" guidance.
            delay = random.uniform(0, delay)
        time.sleep(delay)

    def _raise_if_error(self, resp: httpx.Response) -> None:
        status = resp.status_code

        if 200 <= status < 300:
            return
        try:
            payload: Any = resp.json()
        except Exception:
            payload = {}
        errors = parse_error_payload(payload)
        msg: str = f"HTTP {status}"
        if errors:
            # Handle case where errors might contain strings instead of dicts
            first_error = errors[0]
            if isinstance(first_error, dict):
                maybe_detail = first_error.get("detail")
                maybe_title = first_error.get("title")
                if isinstance(maybe_detail, str) and maybe_detail:
                    msg = maybe_detail
                elif isinstance(maybe_title, str) and maybe_title:
                    msg = maybe_title
            elif isinstance(first_error, str):
                msg = first_error

        hint = _hint_for(status, errors)

        if status in (401, 403):
            raise AuthError(msg, status=status, errors=errors, hint=hint)
        if status == 404:
            raise NotFound(msg, status=status, errors=errors, hint=hint)
        if status == 429:
            ra = _parse_retry_after(resp)
            raise RateLimited(
                msg, status=status, errors=errors, retry_after=ra, hint=hint
            )
        if status >= 500:
            raise ServerError(msg, status=status, errors=errors, hint=hint)
        raise TFEError(msg, status=status, errors=errors, hint=hint)


def _parse_retry_after(resp: httpx.Response) -> float | None:
    ra = resp.headers.get("Retry-After")
    if not ra:
        return None
    try:
        return float(ra)
    except Exception:
        return None
