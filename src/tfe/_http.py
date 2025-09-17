from __future__ import annotations

import re
import time
from collections.abc import Mapping
from typing import Any
from urllib.parse import urljoin

import anyio
import httpx

from ._jsonapi import build_headers, parse_error_payload
from .errors import (
    AuthError,
    NotFound,
    RateLimited,
    ServerError,
    TFEError,
)

_RETRY_STATUSES = {429, 502, 503, 504}

ABSOLUTE_URL_RE = re.compile(r"^https?://", re.I)


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
        proxies: dict | None,
        ca_bundle: str | None,
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
        self._sync = httpx.Client(
            http2=http2, timeout=timeout, verify=ca_bundle or verify_tls
        )  # proxies=proxies
        self._async = httpx.AsyncClient(
            http2=http2, timeout=timeout, verify=ca_bundle or verify_tls
        )  # proxies=proxies

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
        headers: dict[str, str] | None = None,
        allow_redirects: bool = True,
    ) -> httpx.Response:
        url = self._build_url(path)
        hdrs = dict(self.headers)
        if headers:
            hdrs.update(headers)
        attempt = 0
        # print(method, url, params, json_body, hdrs)
        while True:
            try:
                resp = self._sync.request(
                    method,
                    url,
                    params=params,
                    json=json_body,
                    headers=hdrs,
                    follow_redirects=allow_redirects,
                )
            except httpx.HTTPError as e:
                if attempt >= self.max_retries:
                    raise ServerError(str(e)) from e
                self._sleep(attempt, None)
                attempt += 1
                continue
            if resp.status_code in _RETRY_STATUSES and attempt < self.max_retries:
                retry_after = _parse_retry_after(resp)
                self._sleep(attempt, retry_after)
                attempt += 1
                continue
            # print(resp)
            self._raise_if_error(resp)
            return resp

    async def arequest(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        allow_redirects: bool = True,
    ) -> httpx.Response:
        url = f"{self.base}{path}"
        hdrs = dict(self.headers)
        hdrs.update(headers or {})
        attempt = 0
        while True:
            try:
                resp = await self._async.request(
                    method,
                    url,
                    params=params,
                    json=json_body,
                    headers=hdrs,
                    follow_redirects=allow_redirects,
                )
            except httpx.HTTPError as e:
                if attempt >= self.max_retries:
                    raise ServerError(str(e)) from e
                await self._asleep(attempt, None)
                attempt += 1
                continue
            if resp.status_code in _RETRY_STATUSES and attempt < self.max_retries:
                retry_after = _parse_retry_after(resp)
                await self._asleep(attempt, retry_after)
                attempt += 1
                continue
            self._raise_if_error(resp)
            return resp

    def _sleep(self, attempt: int, retry_after: float | None) -> None:
        if retry_after is not None:
            time.sleep(retry_after)
            return
        delay = min(self.backoff_cap, self.backoff_base * (2**attempt))
        time.sleep(delay)

    async def _asleep(self, attempt: int, retry_after: float | None) -> None:
        if retry_after is not None:
            await anyio.sleep(retry_after)
            return
        delay = min(self.backoff_cap, self.backoff_base * (2**attempt))
        await anyio.sleep(delay)

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
            maybe_detail = errors[0].get("detail")
            maybe_title = errors[0].get("title")
            if isinstance(maybe_detail, str) and maybe_detail:
                msg = maybe_detail
            elif isinstance(maybe_title, str) and maybe_title:
                msg = maybe_title

        if status in (401, 403):
            raise AuthError(msg, status=status, errors=errors)
        if status == 404:
            raise NotFound(msg, status=status, errors=errors)
        if status == 429:
            ra = _parse_retry_after(resp)
            raise RateLimited(msg, status=status, errors=errors, retry_after=ra)
        if status >= 500:
            raise ServerError(msg, status=status, errors=errors)
        raise TFEError(msg, status=status, errors=errors)


def _parse_retry_after(resp: httpx.Response) -> float | None:
    ra = resp.headers.get("Retry-After")
    if not ra:
        return None
    try:
        return float(ra)
    except Exception:
        return None
