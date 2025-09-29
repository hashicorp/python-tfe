from __future__ import annotations

from typing import Any


def build_headers(user_agent_suffix: str | None = None) -> dict[str, str]:
    ua = "python-tfe/0.1"
    if user_agent_suffix:
        ua = f"{ua} {user_agent_suffix}"
    return {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
        "User-Agent": ua,
    }


def parse_error_payload(payload: dict[str, Any]) -> list[dict | str]:
    errs = payload.get("errors")
    if isinstance(errs, list):
        return errs
    if "message" in payload:
        return [{"detail": payload.get("message")}]
    return []
