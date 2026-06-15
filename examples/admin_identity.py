#!/usr/bin/env python3
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Reference example: TFE admin identity APIs (SAML / SCIM / SCIM tokens).

All three resources are TFE-only — running this example against HCP
Terraform (SaaS) returns 404 on every call. The script never enables or
disables SAML/SCIM by default; it only reads the current state. To
exercise the write paths, set ``EXAMPLE_APPLY_WRITES=true``.

Environment:

    TFE_TOKEN     site-admin token
    TFE_ADDRESS   TFE base URL (e.g. https://tfe.example.com)

    Optional:
    EXAMPLE_APPLY_WRITES     "true" / "false"  (default: "false")
        Set to "true" to perform a no-op SAML update, a no-op SCIM
        update, and to mint + immediately revoke a throwaway SCIM
        token. Read-only operations always run.
"""

from __future__ import annotations

import os
import sys

from pytfe import TFEClient
from pytfe.errors import NotFound, TFEError
from pytfe.models import (
    AdminSAMLSettingsUpdateOptions,
    AdminSCIMSettingsUpdateOptions,
    AdminSCIMTokenCreateOptions,
)


def banner(s: str) -> None:
    print()
    print("=" * 64)
    print(s)
    print("=" * 64)


def _read_saml(client: TFEClient) -> None:
    banner("SAML settings")
    saml = client.admin.saml_settings.read()
    print(f"  enabled:                  {saml.enabled}")
    print(f"  debug:                    {saml.debug}")
    print(f"  provider_type:            {saml.provider_type}")
    print(f"  sso_endpoint_url:         {saml.sso_endpoint_url}")
    print(f"  slo_endpoint_url:         {saml.slo_endpoint_url}")
    print(f"  acs_consumer_url:         {saml.acs_consumer_url}")
    print(f"  metadata_url:             {saml.metadata_url}")
    print(f"  team_management_enabled:  {saml.team_management_enabled}")


def _write_saml_noop(client: TFEClient) -> None:
    # No-op write: refresh `debug` to its current value. Demonstrates the
    # update path without changing observable state.
    current = client.admin.saml_settings.read()
    refreshed = client.admin.saml_settings.update(
        AdminSAMLSettingsUpdateOptions(debug=current.debug or False)
    )
    print(f"  refreshed (debug={refreshed.debug})")


def _read_scim(client: TFEClient) -> None:
    banner("SCIM settings")
    scim = client.admin.scim_settings.read()
    print(f"  enabled:                       {scim.enabled}")
    print(f"  paused:                        {scim.paused}")
    print(f"  site_admin_group_scim_id:      {scim.site_admin_group_scim_id}")
    print(f"  site_admin_group_display_name: {scim.site_admin_group_display_name}")


def _write_scim_noop(client: TFEClient) -> None:
    # No-op write: refresh `paused` to its current value. Crucially we
    # DON'T pass site_admin_group_scim_id at all — that's what tells the
    # SDK to leave the server-side mapping alone (omit, not explicit null).
    current = client.admin.scim_settings.read()
    refreshed = client.admin.scim_settings.update(
        AdminSCIMSettingsUpdateOptions(paused=bool(current.paused))
    )
    print(f"  refreshed (paused={refreshed.paused})")


def _scim_token_round_trip(client: TFEClient) -> None:
    banner("SCIM token (mint + revoke)")
    # Mint a clearly-disposable token.
    minted = client.admin.scim_tokens.create(
        AdminSCIMTokenCreateOptions(description="pytfe-admin-example-disposable")
    )
    print(f"  minted: id={minted.id} description={minted.description!r}")
    print(f"  plaintext value (one-time): {minted.token!r}")

    # Confirm it shows up in list (without the plaintext value).
    seen = [t for t in client.admin.scim_tokens.list() if t.id == minted.id]
    if not seen:
        print("  WARNING: minted token did not appear in list response")
    else:
        listed = seen[0]
        print(
            f"  list confirms: id={listed.id} token={listed.token!r}  (None expected)"
        )

    # Read by id.
    read_back = client.admin.scim_tokens.read(minted.id)
    print(f"  read confirms: id={read_back.id} description={read_back.description!r}")

    # Revoke.
    client.admin.scim_tokens.delete(minted.id)
    print(f"  revoked: {minted.id}")


def main() -> int:
    client = TFEClient()
    apply_writes = os.environ.get("EXAMPLE_APPLY_WRITES", "").lower() in (
        "1",
        "true",
        "yes",
    )

    try:
        _read_saml(client)
        if apply_writes:
            print()
            print("[EXAMPLE_APPLY_WRITES=true] performing SAML no-op refresh")
            _write_saml_noop(client)

        _read_scim(client)
        if apply_writes:
            print()
            print("[EXAMPLE_APPLY_WRITES=true] performing SCIM no-op refresh")
            _write_scim_noop(client)

        banner("SCIM tokens")
        for tok in client.admin.scim_tokens.list():
            print(
                f"  {tok.id}  description={tok.description!r}  "
                f"created_at={tok.created_at}  last_used_at={tok.last_used_at}"
            )

        if apply_writes:
            print()
            print("[EXAMPLE_APPLY_WRITES=true] minting + revoking a throwaway token")
            _scim_token_round_trip(client)

        return 0
    except NotFound:
        print()
        print(
            "Got 404 from a /admin/* endpoint. These resources are TFE-only "
            "and are not available on HCP Terraform (SaaS) — check that "
            "TFE_ADDRESS points at a Terraform Enterprise instance and "
            "that TFE_TOKEN belongs to a site-admin user."
        )
        return 1
    except TFEError as exc:
        print(f"\nTFE error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
