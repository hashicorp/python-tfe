#!/usr/bin/env python3
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Example: HYOK OIDC configurations (AWS / Azure / GCP / Vault).

Demonstrates the create/read/update/delete lifecycle for an HCP Terraform
HYOK OIDC configuration record. Pick which provider to exercise via
``TFE_OIDC_PROVIDER`` (one of: ``aws``, ``azure``, ``gcp``, ``vault``).

These resources require HYOK / Premium entitlement on the organization.
If you see 404 from create, the org doesn't have HYOK enabled — this is
expected on most sandbox orgs.

This example does NOT provision the cloud-side trust resources (IAM role,
Azure app registration, GCP workload identity pool, Vault JWT auth method).
See docs/scenarios/oidc-dynamic-credentials.md for the full picture.

Environment variables:

    TFE_TOKEN              user, team, or org token (HYOK admin permission)
    TFE_ADDRESS            HCP Terraform / Terraform Enterprise URL
    TFE_ORG                organization with HYOK enabled
    TFE_OIDC_PROVIDER      aws | azure | gcp | vault  (default: aws)

    # AWS only:
    TFE_OIDC_AWS_ROLE_ARN  IAM role ARN HCP Terraform should assume

    # Azure only:
    TFE_OIDC_AZURE_CLIENT_ID
    TFE_OIDC_AZURE_SUBSCRIPTION_ID
    TFE_OIDC_AZURE_TENANT_ID

    # GCP only:
    TFE_OIDC_GCP_SERVICE_ACCOUNT_EMAIL
    TFE_OIDC_GCP_PROJECT_NUMBER
    TFE_OIDC_GCP_WORKLOAD_PROVIDER_NAME

    # Vault only:
    TFE_OIDC_VAULT_ADDRESS
    TFE_OIDC_VAULT_ROLE
    TFE_OIDC_VAULT_NAMESPACE       (optional)
    TFE_OIDC_VAULT_AUTH_PATH       (optional, defaults to "jwt" server-side)

The script creates, reads, updates, then deletes the configuration.
"""

from __future__ import annotations

import os
import sys

from pytfe.client import TFEClient
from pytfe.errors import NotFound, TFEError
from pytfe.models import (
    AWSOIDCConfigurationCreateOptions,
    AWSOIDCConfigurationUpdateOptions,
    AzureOIDCConfigurationCreateOptions,
    AzureOIDCConfigurationUpdateOptions,
    GCPOIDCConfigurationCreateOptions,
    GCPOIDCConfigurationUpdateOptions,
    VaultOIDCConfigurationCreateOptions,
    VaultOIDCConfigurationUpdateOptions,
)


def banner(s: str) -> None:
    print()
    print("=" * 64)
    print(s)
    print("=" * 64)


def _aws(client: TFEClient, org: str) -> None:
    banner("AWS OIDC configuration")
    role_arn = os.environ["TFE_OIDC_AWS_ROLE_ARN"]
    created = client.aws_oidc_configurations.create(
        org, AWSOIDCConfigurationCreateOptions(role_arn=role_arn)
    )
    print(f"  created: id={created.id} role_arn={created.role_arn}")

    read = client.aws_oidc_configurations.read(created.id)
    print(f"  read: id={read.id} role_arn={read.role_arn}")

    updated = client.aws_oidc_configurations.update(
        created.id,
        AWSOIDCConfigurationUpdateOptions(role_arn=role_arn),
    )
    print(f"  update (no-op): role_arn={updated.role_arn}")

    client.aws_oidc_configurations.delete(created.id)
    print(f"  deleted: {created.id}")


def _azure(client: TFEClient, org: str) -> None:
    banner("Azure OIDC configuration")
    created = client.azure_oidc_configurations.create(
        org,
        AzureOIDCConfigurationCreateOptions(
            client_id=os.environ["TFE_OIDC_AZURE_CLIENT_ID"],
            subscription_id=os.environ["TFE_OIDC_AZURE_SUBSCRIPTION_ID"],
            tenant_id=os.environ["TFE_OIDC_AZURE_TENANT_ID"],
        ),
    )
    print(f"  created: id={created.id} client_id={created.client_id}")

    read = client.azure_oidc_configurations.read(created.id)
    print(
        f"  read: id={read.id} subscription_id={read.subscription_id} tenant_id={read.tenant_id}"
    )

    # Partial update — change only client_id.
    updated = client.azure_oidc_configurations.update(
        created.id,
        AzureOIDCConfigurationUpdateOptions(
            client_id=os.environ["TFE_OIDC_AZURE_CLIENT_ID"]
        ),
    )
    print(f"  update (partial): client_id={updated.client_id}")

    client.azure_oidc_configurations.delete(created.id)
    print(f"  deleted: {created.id}")


def _gcp(client: TFEClient, org: str) -> None:
    banner("GCP OIDC configuration")
    created = client.gcp_oidc_configurations.create(
        org,
        GCPOIDCConfigurationCreateOptions(
            service_account_email=os.environ["TFE_OIDC_GCP_SERVICE_ACCOUNT_EMAIL"],
            project_number=os.environ["TFE_OIDC_GCP_PROJECT_NUMBER"],
            workload_provider_name=os.environ["TFE_OIDC_GCP_WORKLOAD_PROVIDER_NAME"],
        ),
    )
    print(f"  created: id={created.id} sa={created.service_account_email}")

    read = client.gcp_oidc_configurations.read(created.id)
    print(
        f"  read: project_number={read.project_number} workload_provider_name={read.workload_provider_name}"
    )

    updated = client.gcp_oidc_configurations.update(
        created.id,
        GCPOIDCConfigurationUpdateOptions(
            workload_provider_name=os.environ["TFE_OIDC_GCP_WORKLOAD_PROVIDER_NAME"]
        ),
    )
    print(
        f"  update (partial): workload_provider_name={updated.workload_provider_name}"
    )

    client.gcp_oidc_configurations.delete(created.id)
    print(f"  deleted: {created.id}")


def _vault(client: TFEClient, org: str) -> None:
    banner("Vault OIDC configuration")
    namespace = os.environ.get("TFE_OIDC_VAULT_NAMESPACE")
    auth_path = os.environ.get("TFE_OIDC_VAULT_AUTH_PATH")
    created = client.vault_oidc_configurations.create(
        org,
        VaultOIDCConfigurationCreateOptions(
            address=os.environ["TFE_OIDC_VAULT_ADDRESS"],
            role_name=os.environ["TFE_OIDC_VAULT_ROLE"],
            namespace=namespace,
            jwt_auth_path=auth_path,
        ),
    )
    print(
        f"  created: id={created.id} address={created.address} role={created.role_name}"
    )

    read = client.vault_oidc_configurations.read(created.id)
    print(f"  read: namespace={read.namespace} auth_path={read.jwt_auth_path}")

    updated = client.vault_oidc_configurations.update(
        created.id,
        VaultOIDCConfigurationUpdateOptions(namespace=namespace),
    )
    print(f"  update (partial): namespace={updated.namespace}")

    client.vault_oidc_configurations.delete(created.id)
    print(f"  deleted: {created.id}")


DISPATCH = {
    "aws": _aws,
    "azure": _azure,
    "gcp": _gcp,
    "vault": _vault,
}


def main() -> int:
    org = os.environ["TFE_ORG"]
    provider = os.environ.get("TFE_OIDC_PROVIDER", "aws").lower()

    if provider not in DISPATCH:
        print(
            f"unknown TFE_OIDC_PROVIDER='{provider}'; must be one of {list(DISPATCH)}"
        )
        return 2

    client = TFEClient()

    try:
        DISPATCH[provider](client, org)
        return 0
    except NotFound:
        print(
            "\nGot 404 from the OIDC endpoint. "
            "This usually means the organization does not have HYOK / Premium "
            "entitlement enabled — try a Premium org or skip these resources."
        )
        return 1
    except TFEError as exc:
        print(f"\nTFE error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
