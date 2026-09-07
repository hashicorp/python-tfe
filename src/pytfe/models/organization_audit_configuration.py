# Copyright IBM Corp. 2025, 2026

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ._base import TFEModel
from .organization import Organization


class OrganizationAuditConfigAuditTrails(BaseModel):
    """Audit Trails configuration."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(..., description="Whether Audit Trails is enabled")


class OrganizationAuditConfigAuditStreaming(BaseModel):
    """HCP Audit Log Streaming configuration."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    enabled: bool = Field(..., description="Whether HCP Audit Log Streaming is enabled")
    organization_id: str | None = Field(None, alias="organization-id")
    use_default_organization: bool = Field(
        ...,
        alias="use-default-organization",
    )


class OrganizationAuditConfigPermissions(BaseModel):
    """Permissions for managing audit configuration."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    can_enable_hcp_audit_log_streaming: bool = Field(
        ...,
        alias="can-enable-hcp-audit-log-streaming",
    )
    can_set_hcp_audit_log_streaming_organization: bool = Field(
        ...,
        alias="can-set-hcp-audit-log-streaming-organization-id",
    )
    can_use_default_audit_log_streaming_organization: bool = Field(
        ...,
        alias="can-use-default-audit-log-streaming-organization",
    )


class OrganizationAuditConfigTimestamps(BaseModel):
    """Timestamp fields for organization audit configuration events."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    audit_trails_disabled_at: datetime | None = Field(
        None,
        alias="audit-trails-disabled-at",
    )
    audit_trails_enabled_at: datetime | None = Field(
        None,
        alias="audit-trails-enabled-at",
    )
    audit_trails_last_failure: datetime | None = Field(
        None,
        alias="audit-trails-last-failure",
    )
    audit_trails_last_success: datetime | None = Field(
        None,
        alias="audit-trails-last-success",
    )
    hcp_audit_log_streaming_disabled_at: datetime | None = Field(
        None,
        alias="hcp-audit-log-streaming-disabled-at",
    )
    hcp_audit_log_streaming_enabled_at: datetime | None = Field(
        None,
        alias="hcp-audit-log-streaming-enabled-at",
    )
    hcp_audit_log_streaming_last_failure: datetime | None = Field(
        None,
        alias="hcp-audit-log-streaming-last-failure",
    )
    hcp_audit_log_streaming_last_success: datetime | None = Field(
        None,
        alias="hcp-audit-log-streaming-last-success",
    )


class OrganizationAuditConfiguration(TFEModel):
    """Organization audit configuration resource."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str
    audit_trails: OrganizationAuditConfigAuditTrails | None = Field(
        None,
        alias="audit-trails",
    )
    hcp_audit_log_streaming: OrganizationAuditConfigAuditStreaming | None = Field(
        None,
        alias="hcp-audit-log-streaming",
    )
    permissions: OrganizationAuditConfigPermissions | None = None
    timestamps: OrganizationAuditConfigTimestamps | None = None
    updated_at: datetime | None = Field(None, alias="updated-at")
    organization: Organization | None = None


class OrganizationAuditConfigurationTest(BaseModel):
    """Result payload for sending a test audit event."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    request_id: str | None = Field(None, alias="request-id")


class OrganizationAuditConfigurationOptions(BaseModel):
    """Options for updating organization audit configuration."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    audit_trails: OrganizationAuditConfigAuditTrails | None = Field(
        None,
        alias="audit-trails",
    )
    hcp_audit_log_streaming: OrganizationAuditConfigAuditStreaming | None = Field(
        None,
        alias="hcp-audit-log-streaming",
    )
