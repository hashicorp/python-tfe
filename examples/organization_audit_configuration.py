#!/usr/bin/env python3
"""Organization audit configuration operations example.

Demonstrates:
1. read() - read organization audit configuration
2. test() - send a test audit event
3. update() - update organization audit configuration
"""

import os

from pytfe import TFEClient, TFEConfig
from pytfe.errors import TFEError
from pytfe.models.organization_audit_configuration import (
    OrganizationAuditConfigAuditTrails,
    OrganizationAuditConfigurationOptions,
)


def main() -> None:
    client = TFEClient(TFEConfig.from_env())

    organization_name = os.getenv("TFE_ORG", "example-org")

    try:
        print("[READ] Reading organization audit configuration")
        read_result = client.organization_audit_configurations.read(organization_name)
        print(f"[READ] id={read_result.id}, updated_at={read_result.updated_at}")
        if read_result.audit_trails is not None:
            print(f"[READ] audit_trails_enabled={read_result.audit_trails.enabled}")

        print("[TEST] Sending test audit event")
        test_result = client.organization_audit_configurations.test(organization_name)
        print(f"[TEST] request_id={test_result.request_id}")

        print("[UPDATE] Updating organization audit configuration")
        options = OrganizationAuditConfigurationOptions(
            audit_trails=OrganizationAuditConfigAuditTrails(enabled=True)
        )
        update_result = client.organization_audit_configurations.update(
            organization_name,
            options,
        )
        print(f"[UPDATE] id={update_result.id}, updated_at={update_result.updated_at}")

    except TFEError as exc:
        print(f"API error: {exc}")
        print("Check TFE_TOKEN, TFE_ADDRESS, and TFE_ORG.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
