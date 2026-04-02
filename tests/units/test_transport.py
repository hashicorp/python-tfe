# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from pytfe._http import HTTPTransport
from pytfe.config import TFEConfig


def test_http_transport_init():
    cfg = TFEConfig()
    t = HTTPTransport(
        cfg.address,
        "",
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
    assert t.base.startswith("https://")
