#!/usr/bin/env python3
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Reference example: organisation API-token TTL policies.

Reads the current per-token-type TTL policies for an org, and (when
opted in via ``EXAMPLE_APPLY_WRITES=true``) demonstrates two write
shapes: a partial update touching only one token type, and a
``reset_to_defaults()`` call.

Environment:

    TFE_TOKEN     org-owner token
    TFE_ADDRESS   HCP Terraform / Terraform Enterprise URL
    TFE_ORG       organisation name

    Optional:
    EXAMPLE_APPLY_WRITES   "true" / "false"  (default: "false")
        When true: PATCH the team-token TTL to 30 days, then
        ``reset_to_defaults()``. Read-only operations always run.

Re-runs are idempotent.
"""

from __future__ import annotations

import os
import sys

from pytfe import TFEClient
from pytfe.errors import TFEError
from pytfe.models import (
    DEFAULT_MAX_TTL_MS,
    OrgTokenTTLPolicyUpdateOptions,
)


def _print_policies(client: TFEClient, organization: str) -> None:
    policies = list(client.organization_token_ttl_policies.list(organization))
    if not policies:
        print("  (none — server reports no per-token-type policies set)")
        return
    for p in policies:
        days = (p.max_ttl_ms or 0) // 86_400_000
        print(f"  {p.token_type!s:>40}  max_ttl_ms={p.max_ttl_ms:>14,}  (~{days} days)")


def main() -> int:
    organization = os.environ["TFE_ORG"]
    apply_writes = os.environ.get("EXAMPLE_APPLY_WRITES", "").lower() in (
        "1",
        "true",
        "yes",
    )

    client = TFEClient()

    try:
        print(f"=== Current policies for {organization} ===")
        _print_policies(client, organization)

        if not apply_writes:
            print(
                "\nSet EXAMPLE_APPLY_WRITES=true to demonstrate a partial "
                "update + reset_to_defaults()."
            )
            return 0

        print("\n[EXAMPLE_APPLY_WRITES=true] tightening team token TTL to 30 days")
        client.organization_token_ttl_policies.update(
            organization,
            OrgTokenTTLPolicyUpdateOptions(team="30d"),
        )

        print("\nPost-update policies:")
        _print_policies(client, organization)

        print("\n[EXAMPLE_APPLY_WRITES=true] reset_to_defaults() — all 4 types -> 2y")
        client.organization_token_ttl_policies.reset_to_defaults(organization)

        print("\nFinal policies (should all be the 2-year default):")
        _print_policies(client, organization)
        print(f"\n(default = {DEFAULT_MAX_TTL_MS:,} ms = 2 years)")
        return 0

    except TFEError as exc:
        print(f"\nTFE error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
