# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import SkipJsonSchema

_TRUTHY = ("1", "true", "yes", "on")

#: HTTP methods that never mutate server state.
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


@dataclass(frozen=True)
class RequestInfo:
    """A request about to be issued, as seen by :attr:`TFEConfig.before_request`.

    Attributes:
        method: The HTTP method, upper-cased.
        path: The API path or absolute URL, exactly as the caller passed it.
        is_write: True when ``method`` is not one of :data:`SAFE_METHODS`.
        resource: Best-effort first path segment after ``/api/v2/``, or None
            for absolute blob URLs and unrecognised paths.
    """

    method: str
    path: str
    is_write: bool
    resource: str | None


def _resource_of(path: str) -> str | None:
    """Best-effort resource name for a request path."""
    marker = "/api/v2/"
    index = path.find(marker)
    if index == -1:
        return None
    tail = path[index + len(marker) :].lstrip("/")
    if not tail:
        return None
    segment = tail.split("?", 1)[0].split("/", 1)[0]
    return segment or None


def request_info(method: str, path: str) -> RequestInfo:
    """Build a :class:`RequestInfo` for a method/path pair."""
    upper = method.upper()
    return RequestInfo(
        method=upper,
        path=path,
        is_write=upper not in SAFE_METHODS,
        resource=_resource_of(path),
    )


class TFEConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    address: str = Field(
        default_factory=lambda: os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    token: str = Field(default_factory=lambda: os.getenv("TFE_TOKEN", ""))
    timeout: float = Field(
        default_factory=lambda: float(os.getenv("TFE_TIMEOUT", "30"))
    )
    verify_tls: bool = Field(
        default_factory=lambda: os.getenv("TFE_VERIFY_TLS", "true").lower()
        not in ("0", "false", "no")
    )
    user_agent_suffix: str | None = None
    max_retries: int = Field(
        default_factory=lambda: int(os.getenv("TFE_MAX_RETRIES", "5"))
    )
    backoff_base: float = 0.5
    backoff_cap: float = 8.0
    backoff_jitter: bool = True
    http2: bool = True
    proxies: str | None = None
    ca_bundle: str | None = Field(
        default_factory=lambda: os.getenv("SSL_CERT_FILE", None)
    )

    read_only: bool = Field(
        default_factory=lambda: os.getenv("PYTFE_READ_ONLY", "").lower() in _TRUTHY
    )
    """Block every non-safe HTTP method at the transport.

    Set this when handing a client to an AI agent that must not mutate state.
    It is enforced for *every* request the client makes, including the
    absolute-URL configuration-version and registry-module uploads that do not
    go through ``HTTPTransport.request``.
    """

    before_request: SkipJsonSchema[Callable[[RequestInfo], None] | None] = Field(
        default=None, exclude=True
    )
    """Called with a :class:`RequestInfo` immediately before each request.

    Raise from the hook to block the request; the exception propagates to the
    caller unchanged. Excluded from serialization and JSON Schema because a
    callable is neither dumpable nor describable.
    """

    @classmethod
    def from_env(cls) -> TFEConfig:
        return cls()
