# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import os

from pydantic import BaseModel, Field


class TFEConfig(BaseModel):
    address: str = Field(
        default_factory=lambda: os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    token: str = Field(default_factory=lambda: os.getenv("TFE_TOKEN", ""))
    timeout: float = float(os.getenv("TFE_TIMEOUT", "30"))
    verify_tls: bool = os.getenv("TFE_VERIFY_TLS", "true").lower() not in (
        "0",
        "false",
        "no",
    )
    user_agent_suffix: str | None = None
    max_retries: int = int(os.getenv("TFE_MAX_RETRIES", "5"))
    backoff_base: float = 0.5
    backoff_cap: float = 8.0
    backoff_jitter: bool = True
    http2: bool = True
    proxies: str | None = None
    ca_bundle: str | None = os.getenv("SSL_CERT_FILE", None)

    @classmethod
    def from_env(cls) -> TFEConfig:
        return cls()
