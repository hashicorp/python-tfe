# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Models for the organisation API-token TTL policy resource.

Exposes the per-token-type "max TTL" knobs that pair with the
``max_ttl_enabled`` toggle on the parent ``Organization``. The upstream
endpoints are:

- ``GET   /api/v2/organizations/{org}/token-ttl-policies``
- ``PATCH /api/v2/organizations/{org}/token-ttl-policies``

with JSON:API type ``organization-token-ttl-policies``.

The list payload returns one item per token type. The update payload
sends one item per token type the caller wants to change.

**Token-type spelling note.** This API uses
``token-type=audit_trails`` (UNDERSCORE) for the audit-trail policy
entry. That's deliberately different from the audit-trail token
*creation* surface elsewhere in the API which uses
``audit-trails`` (HYPHEN). The :class:`TokenPolicyType` enum below
mirrors the TTL-specific spelling exactly so the two surfaces don't get
accidentally cross-wired.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# 2 years in milliseconds — the documented default the upstream applies
# when no per-token policy is set. Exported for callers who want to
# reset to defaults without recomputing.
DEFAULT_MAX_TTL_MS: int = 63_072_000_000


class TokenPolicyType(str, Enum):
    """Token types accepted by the org TTL policy endpoint.

    See the module docstring for the audit-trails spelling rationale.
    """

    ORGANIZATION = "organization"
    TEAM = "team"
    USER = "user"
    AUDIT_TRAILS = "audit_trails"


class OrgTokenTTLPolicy(BaseModel):
    """One token-type / max-TTL entry as returned by the list endpoint."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str | None = None
    token_type: TokenPolicyType | None = Field(default=None, alias="token-type")
    max_ttl_ms: int | None = Field(default=None, alias="max-ttl-ms")


class OrgTokenTTLPolicyUpdateOptions(BaseModel):
    """Update options addressed by token type.

    Each of the four fields accepts either:

    - An ``int`` (raw milliseconds, e.g. ``63_072_000_000`` for 2 years).
    - A duration string (``"1h"``, ``"30d"``, ``"6mo"``, ``"2y"``). Parsed
      by :func:`parse_ttl_to_ms` at payload-build time.
    - ``None`` (omit this entry — the server keeps the existing policy
      for that token type).

    At least one field must be supplied; ``to_payload()`` raises
    :class:`pytfe.errors.RequiredFieldMissing` if you build a no-op
    update.
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    organization: int | str | None = None
    team: int | str | None = None
    user: int | str | None = None
    audit_trails: int | str | None = None

    def to_payload(self) -> list[dict[str, Any]]:
        """Serialize to the JSON:API ``data`` array. Each non-``None``
        field becomes one ``{type, attributes: {token-type, max-ttl-ms}}``
        entry. Empty result is an error — see class docstring.
        """
        # Local import to avoid a cycle: errors imports models indirectly
        # through other modules.
        from ..errors import RequiredFieldMissing

        items: list[dict[str, Any]] = []
        for field_name, token_type in [
            ("organization", TokenPolicyType.ORGANIZATION),
            ("team", TokenPolicyType.TEAM),
            ("user", TokenPolicyType.USER),
            ("audit_trails", TokenPolicyType.AUDIT_TRAILS),
        ]:
            raw = getattr(self, field_name)
            if raw is None:
                continue
            ms = parse_ttl_to_ms(raw) if isinstance(raw, str) else int(raw)
            items.append(
                {
                    "type": "organization-token-ttl-policies",
                    "attributes": {
                        "token-type": token_type.value,
                        "max-ttl-ms": ms,
                    },
                }
            )
        if not items:
            raise RequiredFieldMissing(
                "OrgTokenTTLPolicyUpdateOptions requires at least one of "
                "organization, team, user, or audit_trails to be set."
            )
        return items


# ---------------------------------------------------------------------------
# Duration parser
# ---------------------------------------------------------------------------

# Suffix multipliers expressed in milliseconds. Matches the duration
# strings the Terraform provider accepts for the same setting.
_TTL_SUFFIX_MS: dict[str, int] = {
    "ms": 1,
    "s": 1_000,
    "m": 60 * 1_000,
    "h": 60 * 60 * 1_000,
    "d": 24 * 60 * 60 * 1_000,
    "w": 7 * 24 * 60 * 60 * 1_000,
    # "month" is approximated as 30 days, matching the provider's
    # convention. Use exact day counts (``90d``) when you need precision.
    "mo": 30 * 24 * 60 * 60 * 1_000,
    "y": 365 * 24 * 60 * 60 * 1_000,
}

# Tuple form ordered by suffix length DESCENDING so "mo" wins over "m"
# during prefix matching.
_TTL_SUFFIXES_ORDERED = sorted(_TTL_SUFFIX_MS.keys(), key=len, reverse=True)

_TTL_RE = re.compile(r"^\s*(\d+)\s*([a-zA-Z]+)\s*$")


def parse_ttl_to_ms(value: str) -> int:
    """Parse a duration string like ``"2y"``, ``"30d"``, ``"6mo"`` or
    ``"500ms"`` into milliseconds.

    Accepted suffixes: ``ms`` (milliseconds), ``s`` (seconds),
    ``m`` (minutes), ``h`` (hours), ``d`` (days), ``w`` (weeks),
    ``mo`` (months — approximated as 30 days), ``y`` (years — 365 days).

    Raises ``ValueError`` on malformed input or unrecognised suffix.
    """
    if not isinstance(value, str):
        raise ValueError(f"parse_ttl_to_ms expected str, got {type(value).__name__}")
    match = _TTL_RE.match(value)
    if not match:
        raise ValueError(
            f"could not parse TTL string {value!r}; expected '<number><unit>' "
            "where unit is one of: ms, s, m, h, d, w, mo, y"
        )
    number = int(match.group(1))
    suffix = match.group(2).lower()
    # Try longest-first so "mo" matches before "m".
    for candidate in _TTL_SUFFIXES_ORDERED:
        if suffix == candidate:
            return number * _TTL_SUFFIX_MS[candidate]
    raise ValueError(
        f"unrecognised TTL unit {match.group(2)!r}; expected one of: "
        "ms, s, m, h, d, w, mo, y"
    )


__all__ = [
    "DEFAULT_MAX_TTL_MS",
    "OrgTokenTTLPolicy",
    "OrgTokenTTLPolicyUpdateOptions",
    "TokenPolicyType",
    "parse_ttl_to_ms",
]
