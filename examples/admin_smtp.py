#!/usr/bin/env python3
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Reference example: TFE admin SMTP settings.

TFE-only. Running this against HCP Terraform (SaaS) returns 404 on every
call. The script defaults to a read-only operation; setting
``EXAMPLE_APPLY_WRITES=true`` will do a no-op refresh that re-PATCHes
the current values, and setting ``EXAMPLE_SEND_TEST_EMAIL=true`` plus
``EXAMPLE_TEST_EMAIL_ADDRESS=ops@example.com`` will trigger TFE to send
a verification email to that address as a side effect of the update.

Environment:

    TFE_TOKEN     site-admin token
    TFE_ADDRESS   TFE base URL

    Optional:
    EXAMPLE_APPLY_WRITES         "true" / "false"  (default: "false")
    EXAMPLE_SEND_TEST_EMAIL      "true" / "false"  (default: "false")
    EXAMPLE_TEST_EMAIL_ADDRESS   email address for test send
"""

from __future__ import annotations

import os
import sys

from pytfe import TFEClient
from pytfe.errors import NotFound, TFEError
from pytfe.models import AdminSMTPSettingsUpdateOptions


def main() -> int:
    client = TFEClient()
    apply_writes = os.environ.get("EXAMPLE_APPLY_WRITES", "").lower() in (
        "1",
        "true",
        "yes",
    )
    send_test = os.environ.get("EXAMPLE_SEND_TEST_EMAIL", "").lower() in (
        "1",
        "true",
        "yes",
    )
    test_address = os.environ.get("EXAMPLE_TEST_EMAIL_ADDRESS")

    try:
        print("=== SMTP settings ===")
        smtp = client.admin.smtp_settings.read()
        print(f"  enabled:  {smtp.enabled}")
        print(f"  host:     {smtp.host}")
        print(f"  port:     {smtp.port}")
        print(f"  sender:   {smtp.sender}")
        print(f"  auth:     {smtp.auth}")
        print(f"  username: {smtp.username}")

        if not apply_writes:
            print(
                "\nSet EXAMPLE_APPLY_WRITES=true to refresh the values "
                "(no observable change)."
            )
            return 0

        # Refresh the host to its current value — demonstrates the
        # update path with no observable effect.
        print("\n[EXAMPLE_APPLY_WRITES=true] refreshing host to its current value")
        options = AdminSMTPSettingsUpdateOptions(host=smtp.host)
        if send_test and test_address:
            print(f"[EXAMPLE_SEND_TEST_EMAIL=true] also requesting test email to {test_address}")
            options = AdminSMTPSettingsUpdateOptions(
                host=smtp.host, test_email_address=test_address
            )
        refreshed = client.admin.smtp_settings.update(options)
        print(f"  refreshed host: {refreshed.host}")
        return 0

    except NotFound:
        print(
            "\nGot 404 from /api/v2/admin/smtp-settings. SMTP admin is "
            "TFE-only and is not available on HCP Terraform (SaaS) — "
            "check that TFE_ADDRESS points at a Terraform Enterprise "
            "instance and that TFE_TOKEN belongs to a site-admin user."
        )
        return 1
    except TFEError as exc:
        print(f"\nTFE error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
