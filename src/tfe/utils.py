from __future__ import annotations

import re
import time
from collections.abc import Callable, Mapping
from typing import Any

_STRING_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{2,}$")
_WS_ID_RE = re.compile(r"^ws-[A-Za-z0-9]+$")


def poll_until(
    fn: Callable[[], bool],
    *,
    interval_s: float = 5.0,
    timeout_s: float | None = 600,
) -> bool:
    start = time.time()
    while True:
        value = fn()
        if value:
            return True
        if timeout_s is not None and (time.time() - start) > timeout_s:
            raise TimeoutError("Timed out")
        time.sleep(interval_s)


def valid_string(v: str | None) -> bool:
    return v is not None and str(v).strip() != ""


def valid_string_id(v: str | None) -> bool:
    return v is not None and _STRING_ID_PATTERN.match(str(v)) is not None


def _safe_str(v: Any, default: str = "") -> str:
    return v if isinstance(v, str) else (str(v) if v is not None else default)


def looks_like_workspace_id(value: Any) -> bool:
    """True if value matches "ws-<alnum>" pattern."""
    return isinstance(value, str) and bool(_WS_ID_RE.match(value))


def encode_query(params: Mapping[str, Any] | None) -> str:
    """
    Best-effort encoder for JSON:API-style query dicts into a query string.
    Keeps keys like "page[number]" intact. Values that are lists/tuples are joined with commas.
    """
    if not params:
        return ""
    parts: list[str] = []
    for k, v in params.items():
        if v is None:
            continue
        if isinstance(v, (list, tuple)):
            sv = ",".join(str(x) for x in v)
        else:
            sv = str(v)
        parts.append(f"{k}={sv}")
    return ("?" + "&".join(parts)) if parts else ""
