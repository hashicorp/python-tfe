# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Organisation API-token TTL policy resource.

Manages the maximum lifetime of API tokens minted in an organisation,
broken down by token type. Pairs with the ``max_ttl_enabled`` toggle on
the parent ``Organization`` (use
``client.organizations.update_default_settings`` or
``client.organizations.update`` to flip it on/off).
"""

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from ..errors import ERR_INVALID_ORG
from ..models.org_token_ttl_policy import (
    DEFAULT_MAX_TTL_MS,
    OrgTokenTTLPolicy,
    OrgTokenTTLPolicyUpdateOptions,
    TokenPolicyType,
)
from ..utils import valid_string_id
from ._base import _Service


def _parse_policy(data: dict[str, Any]) -> OrgTokenTTLPolicy:
    attrs = data.get("attributes") or {}
    return OrgTokenTTLPolicy.model_validate({"id": data.get("id"), **attrs})


class OrganizationTokenTTLPolicies(_Service):
    """Resource for ``/api/v2/organizations/{org}/token-ttl-policies``.

    Two operations: list (one entry per token type the org has policies
    for) and update (PATCH a partial set; unchanged token types keep
    their existing TTLs). ``reset_to_defaults`` is a convenience that
    PATCHes all four token types to the documented 2-year default.
    """

    def list(self, organization: str) -> Iterator[OrgTokenTTLPolicy]:
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)
        # The endpoint is not documented as paginated; we iterate the
        # single returned ``data`` array directly rather than going
        # through the generic paginating helper which would inject
        # unwanted ``page[...]`` query params.
        r = self.t.request(
            "GET", f"/api/v2/organizations/{organization}/token-ttl-policies"
        )
        for item in r.json().get("data") or []:
            yield _parse_policy(item)

    def update(
        self,
        organization: str,
        options: OrgTokenTTLPolicyUpdateOptions,
    ) -> builtins.list[OrgTokenTTLPolicy]:
        """PATCH a partial set of token-type policies. Returns the full
        post-update policy list as the server reports it."""
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)
        body = {"data": options.to_payload()}
        r = self.t.request(
            "PATCH",
            f"/api/v2/organizations/{organization}/token-ttl-policies",
            json_body=body,
        )
        return [_parse_policy(item) for item in r.json().get("data") or []]

    def reset_to_defaults(self, organization: str) -> builtins.list[OrgTokenTTLPolicy]:
        """Reset all four token types to the documented 2-year default
        (``DEFAULT_MAX_TTL_MS = 63_072_000_000``).
        """
        return self.update(
            organization,
            OrgTokenTTLPolicyUpdateOptions(
                organization=DEFAULT_MAX_TTL_MS,
                team=DEFAULT_MAX_TTL_MS,
                user=DEFAULT_MAX_TTL_MS,
                audit_trails=DEFAULT_MAX_TTL_MS,
            ),
        )


__all__ = ["OrganizationTokenTTLPolicies", "TokenPolicyType"]
