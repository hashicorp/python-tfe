# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Models for HYOK (Hold Your Own Key) configurations.

A HYOK configuration ties together an OIDC configuration (how HCP Terraform
authenticates to your KMS), an agent pool, and a key-encryption-key id, so HCP
Terraform can encrypt workspace state/plan data with a key you control.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..errors import (
    InvalidAgentPoolIDError,
    InvalidOIDCConfigurationIDError,
    RequiredKEKIDError,
    RequiredNameError,
)
from ..utils import valid_string, valid_string_id
from ._base import TFEModel


class HYOKConfigurationStatus(str, Enum):
    """Lifecycle status of a HYOK configuration."""

    UNTESTED = "untested"
    AVAILABLE = "available"
    TESTING = "testing"
    TEST_FAILED = "test_failed"
    ACTIVE = "active"
    REVOKING = "revoking"
    REVOKED = "revoked"
    ERRORED = "errored"


class OIDCConfigurationType(str, Enum):
    """JSON:API type of the OIDC configuration a HYOK config authenticates with."""

    AWS = "aws-oidc-configurations"
    AZURE = "azure-oidc-configurations"
    GCP = "gcp-oidc-configurations"
    VAULT = "vault-oidc-configurations"


class HYOKKMSOptions(BaseModel):
    """Optional KMS-specific options for a HYOK configuration."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    key_region: str | None = None
    key_location: str | None = None
    key_ring_id: str | None = None


class HYOKConfiguration(TFEModel):
    """A Hold Your Own Key configuration."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    name: str | None = None
    kek_id: str | None = Field(default=None, alias="kek-id")
    kms_options: HYOKKMSOptions | None = Field(default=None, alias="kms-options")
    primary: bool | None = None
    status: HYOKConfigurationStatus | None = None
    error: str | None = None
    # Flat relationship references (the raw block is on `.relationships`).
    organization_id: str | None = Field(default=None, alias="organization-id")
    agent_pool_id: str | None = Field(default=None, alias="agent-pool-id")
    oidc_configuration_id: str | None = Field(
        default=None, alias="oidc-configuration-id"
    )
    oidc_configuration_type: str | None = Field(
        default=None, alias="oidc-configuration-type"
    )


class HYOKConfigurationCreateOptions(BaseModel):
    """Options for creating a HYOK configuration."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="forbid"
    )

    name: str = Field(..., description="Label for the HYOK configuration.")
    kek_id: str = Field(
        ..., alias="kek-id", description="Name/id of your key in the KMS."
    )
    agent_pool_id: str = Field(..., description="ID of the agent pool to use.")
    oidc_configuration_id: str = Field(
        ..., description="ID of the OIDC configuration to authenticate with."
    )
    oidc_configuration_type: OIDCConfigurationType = Field(
        ..., description="The OIDC configuration's JSON:API type (cloud)."
    )
    primary: bool | None = Field(
        default=None, description="Whether this is the primary HYOK configuration."
    )
    kms_options: HYOKKMSOptions | None = Field(default=None, alias="kms-options")

    @model_validator(mode="after")
    def valid(self) -> HYOKConfigurationCreateOptions:
        if not valid_string(self.name):
            raise RequiredNameError()
        if not valid_string(self.kek_id):
            raise RequiredKEKIDError()
        if not valid_string_id(self.agent_pool_id):
            raise InvalidAgentPoolIDError()
        if not valid_string_id(self.oidc_configuration_id):
            raise InvalidOIDCConfigurationIDError()
        return self


class HYOKConfigurationListOptions(BaseModel):
    """Options for listing HYOK configurations in an organization."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="forbid"
    )

    page_number: int | None = Field(default=None, alias="page[number]")
    page_size: int | None = Field(default=None, alias="page[size]")
