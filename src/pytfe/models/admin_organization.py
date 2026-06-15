# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AdminOrganizationListOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    query: str | None = Field(default=None, alias="q")
    page_number: int | None = Field(default=None, alias="page[number]")
    page_size: int | None = Field(default=None, alias="page[size]")


class AdminOrganization(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    id: str | None = None
    name: str | None = None
    email: str | None = None
    plan_expired: bool | None = Field(default=None, alias="plan-expired")
    plan_expires_at: str | None = Field(default=None, alias="plan-expires-at")
    plan_is_enterprise: bool | None = Field(default=None, alias="plan-is-enterprise")
    plan_is_trial: bool | None = Field(default=None, alias="plan-is-trial")
    plan_identifier: str | None = Field(default=None, alias="plan-identifier")
    fair_run_queuing_enabled: bool | None = Field(
        default=None, alias="fair-run-queuing-enabled"
    )
    owners_team_saml_role_id: str | None = Field(
        default=None, alias="owners-team-saml-role-id"
    )
    two_factor_conformant: bool | None = Field(
        default=None, alias="two-factor-conformant"
    )
    global_module_sharing: bool | None = Field(
        default=None, alias="global-module-sharing"
    )
    global_provider_sharing: bool | None = Field(
        default=None, alias="global-provider-sharing"
    )


class AdminOrganizationUpdateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    global_module_sharing: bool | None = Field(
        default=None, alias="global-module-sharing"
    )
    global_provider_sharing: bool | None = Field(
        default=None, alias="global-provider-sharing"
    )
    owners_team_saml_role_id: str | None = Field(
        default=None, alias="owners-team-saml-role-id"
    )
