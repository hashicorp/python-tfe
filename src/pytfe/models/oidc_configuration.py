# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Models for HCP Terraform HYOK OIDC configurations.

Four provider types share the same wire endpoint
(``/organizations/{org}/oidc-configurations`` for create,
``/oidc-configurations/{id}`` for read/update/delete) and are polymorphically
dispatched by the JSON:API ``data.type`` string:

- ``aws-oidc-configurations``
- ``azure-oidc-configurations``
- ``gcp-oidc-configurations``
- ``vault-oidc-configurations``

These models manage the HCP Terraform *configuration record* only — they
don't provision the cloud-side IAM/service-principal/workload-identity
resources. Use the cloud provider's own SDK/IaC for that. See
``docs/scenarios/oidc-dynamic-credentials.md`` for how this fits with
workspace dynamic provider credentials.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .organization import Organization


def _non_empty_role_arn(value: str) -> str:
    """AWS role ARNs must be non-empty strings.

    go-tfe's ``AWSOIDCConfigurationUpdateOptions.valid()`` rejects empty
    role ARNs locally with ``ErrRequiredRoleARN``. We mirror that for both
    create and update so callers get a clear pydantic error at construction
    time instead of an opaque server-side 422 (or worse, an accepted but
    malformed config record).
    """
    if not value or not value.strip():
        raise ValueError("role_arn must be a non-empty string")
    return value


# ---------------------------------------------------------------------------
# AWS
# ---------------------------------------------------------------------------


class AWSOIDCConfiguration(BaseModel):
    """An AWS OIDC configuration record on HCP Terraform."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str | None = None
    role_arn: str | None = Field(default=None, alias="role-arn")

    # Relationships
    organization: Organization | None = None


class AWSOIDCConfigurationCreateOptions(BaseModel):
    """Options for creating an AWS OIDC configuration."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    role_arn: str = Field(
        ...,
        alias="role-arn",
        description="ARN of the IAM role HCP Terraform will assume",
    )

    _validate_role_arn = field_validator("role_arn")(_non_empty_role_arn)


class AWSOIDCConfigurationUpdateOptions(BaseModel):
    """Options for updating an AWS OIDC configuration.

    Unlike Azure/GCP/Vault — whose update options are fully partial —
    ``role_arn`` is REQUIRED here. The AWS resource has exactly one
    updatable attribute, so an update with no fields is meaningless;
    go-tfe's ``AWSOIDCConfigurationUpdateOptions.valid()`` rejects the
    empty case locally with ``ErrRequiredRoleARN`` and we mirror that
    behaviour.
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    role_arn: str = Field(..., alias="role-arn")

    _validate_role_arn = field_validator("role_arn")(_non_empty_role_arn)


# ---------------------------------------------------------------------------
# Azure
# ---------------------------------------------------------------------------


class AzureOIDCConfiguration(BaseModel):
    """An Azure OIDC configuration record on HCP Terraform."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str | None = None
    client_id: str | None = Field(default=None, alias="client-id")
    subscription_id: str | None = Field(default=None, alias="subscription-id")
    tenant_id: str | None = Field(default=None, alias="tenant-id")

    organization: Organization | None = None


class AzureOIDCConfigurationCreateOptions(BaseModel):
    """Options for creating an Azure OIDC configuration."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    client_id: str = Field(..., alias="client-id")
    subscription_id: str = Field(..., alias="subscription-id")
    tenant_id: str = Field(..., alias="tenant-id")


class AzureOIDCConfigurationUpdateOptions(BaseModel):
    """Options for updating an Azure OIDC configuration."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    client_id: str | None = Field(default=None, alias="client-id")
    subscription_id: str | None = Field(default=None, alias="subscription-id")
    tenant_id: str | None = Field(default=None, alias="tenant-id")


# ---------------------------------------------------------------------------
# GCP
# ---------------------------------------------------------------------------


class GCPOIDCConfiguration(BaseModel):
    """A GCP OIDC configuration record on HCP Terraform."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str | None = None
    service_account_email: str | None = Field(
        default=None, alias="service-account-email"
    )
    project_number: str | None = Field(default=None, alias="project-number")
    workload_provider_name: str | None = Field(
        default=None, alias="workload-provider-name"
    )

    organization: Organization | None = None


class GCPOIDCConfigurationCreateOptions(BaseModel):
    """Options for creating a GCP OIDC configuration."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    service_account_email: str = Field(..., alias="service-account-email")
    project_number: str = Field(..., alias="project-number")
    workload_provider_name: str = Field(..., alias="workload-provider-name")


class GCPOIDCConfigurationUpdateOptions(BaseModel):
    """Options for updating a GCP OIDC configuration."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    service_account_email: str | None = Field(
        default=None, alias="service-account-email"
    )
    project_number: str | None = Field(default=None, alias="project-number")
    workload_provider_name: str | None = Field(
        default=None, alias="workload-provider-name"
    )


# ---------------------------------------------------------------------------
# Vault
# ---------------------------------------------------------------------------


class VaultOIDCConfiguration(BaseModel):
    """A Vault OIDC configuration record on HCP Terraform.

    Field-name mappings:
    - ``role_name``         <-> wire ``role``
    - ``jwt_auth_path``     <-> wire ``auth-path``
    - ``tls_ca_certificate`` <-> wire ``encoded-cacert``
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str | None = None
    address: str | None = None
    role_name: str | None = Field(default=None, alias="role")
    namespace: str | None = None
    jwt_auth_path: str | None = Field(default=None, alias="auth-path")
    tls_ca_certificate: str | None = Field(default=None, alias="encoded-cacert")

    organization: Organization | None = None


class VaultOIDCConfigurationCreateOptions(BaseModel):
    """Options for creating a Vault OIDC configuration."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    address: str = Field(
        ..., description="Vault address (e.g. https://vault.example.com)"
    )
    role_name: str = Field(..., alias="role")
    namespace: str | None = None
    jwt_auth_path: str | None = Field(default=None, alias="auth-path")
    tls_ca_certificate: str | None = Field(default=None, alias="encoded-cacert")


class VaultOIDCConfigurationUpdateOptions(BaseModel):
    """Options for updating a Vault OIDC configuration."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    address: str | None = None
    role_name: str | None = Field(default=None, alias="role")
    namespace: str | None = None
    jwt_auth_path: str | None = Field(default=None, alias="auth-path")
    tls_ca_certificate: str | None = Field(default=None, alias="encoded-cacert")


__all__ = [
    "AWSOIDCConfiguration",
    "AWSOIDCConfigurationCreateOptions",
    "AWSOIDCConfigurationUpdateOptions",
    "AzureOIDCConfiguration",
    "AzureOIDCConfigurationCreateOptions",
    "AzureOIDCConfigurationUpdateOptions",
    "GCPOIDCConfiguration",
    "GCPOIDCConfigurationCreateOptions",
    "GCPOIDCConfigurationUpdateOptions",
    "VaultOIDCConfiguration",
    "VaultOIDCConfigurationCreateOptions",
    "VaultOIDCConfigurationUpdateOptions",
]
