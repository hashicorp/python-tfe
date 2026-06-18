# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

import httpx

from pytfe._http import HTTPTransport
from pytfe.config import TFEConfig


def _make_transport() -> HTTPTransport:
    cfg = TFEConfig()
    return HTTPTransport(
        cfg.address,
        "tok",
        timeout=cfg.timeout,
        verify_tls=cfg.verify_tls,
        user_agent_suffix=None,
        max_retries=1,
        backoff_base=0.01,
        backoff_cap=0.02,
        backoff_jitter=False,
        http2=False,
        proxies=None,
        ca_bundle=None,
    )


def test_http_transport_init():
    t = _make_transport()
    assert t.base.startswith("https://")


def test_request_does_not_persist_cookies():
    """A Set-Cookie in a response must not leak into subsequent requests.

    ``/api/meta/ip-ranges`` returns an ``_atlas_session_data`` session cookie;
    if the shared client retained it, that session would override bearer auth
    on later requests and the API would respond 404/401.
    """
    t = _make_transport()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"set-cookie": "_atlas_session_data=abc123; path=/"},
            json={"api": []},
        )

    t._sync = httpx.Client(transport=httpx.MockTransport(handler))

    t.request("GET", "/api/meta/ip-ranges")

    assert dict(t._sync.cookies) == {}
