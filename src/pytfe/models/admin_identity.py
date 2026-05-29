# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Models for Terraform Enterprise admin identity APIs.

This module covers three closely related TFE-only admin resources:

- SAML settings (``/api/v2/admin/saml-settings``)
- SCIM settings (``/api/v2/admin/scim-settings``)
- SCIM tokens (``/api/v2/admin/scim-tokens``)

These endpoints are TFE-only — they are not available on HCP Terraform
(SaaS). The SDK does not enforce that; the server returns 404 on HCP and
the SDK surfaces it as ``pytfe.errors.NotFound``.

Per the upstream API, several SAML attributes are write-only or sensitive
(``private-key`` in particular). The transport-level logger redacts these
keys before they ever reach the log; see ``pytfe._logging``.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# SAML
# ---------------------------------------------------------------------------


class SAMLProviderType(str, Enum):
    """Provider hint sent to TFE so it can apply provider-specific
    SAML quirks. ``UNKNOWN`` is the safe default for generic IdPs."""

    OKTA = "okta"
    ENTRA = "entra"
    SAML = "saml"
    UNKNOWN = "unknown"


class SAMLSignatureMethod(str, Enum):
    """Digest / signing algorithm for SP-signed SAML requests."""

    SHA1 = "SHA1"
    SHA256 = "SHA256"


class AdminSAMLSettings(BaseModel):
    """Snapshot of the organisation's SAML settings on TFE."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str | None = None

    # Lifecycle / debug flags.
    enabled: bool | None = None
    debug: bool | None = None

    # Identity provider configuration.
    idp_cert: str | None = Field(default=None, alias="idp-cert")
    old_idp_cert: str | None = Field(default=None, alias="old-idp-cert")
    slo_endpoint_url: str | None = Field(default=None, alias="slo-endpoint-url")
    sso_endpoint_url: str | None = Field(default=None, alias="sso-endpoint-url")

    # Service-provider configuration (read-back on TFE; written via update).
    acs_consumer_url: str | None = Field(default=None, alias="acs-consumer-url")
    metadata_url: str | None = Field(default=None, alias="metadata-url")
    certificate: str | None = None
    # ``private-key`` is sensitive; the API never returns it on read, but
    # we model it here so users can spot it on the type if they go looking.
    private_key: str | None = Field(default=None, alias="private-key")

    # Attribute mapping.
    attr_username: str | None = Field(default=None, alias="attr-username")
    attr_groups: str | None = Field(default=None, alias="attr-groups")
    attr_site_admin: str | None = Field(default=None, alias="attr-site-admin")
    site_admin_role: str | None = Field(default=None, alias="site-admin-role")

    # SP-signed request behaviour.
    authn_requests_signed: bool | None = Field(
        default=None, alias="authn-requests-signed"
    )
    want_assertions_signed: bool | None = Field(
        default=None, alias="want-assertions-signed"
    )
    signature_signing_method: SAMLSignatureMethod | None = Field(
        default=None, alias="signature-signing-method"
    )
    signature_digest_method: SAMLSignatureMethod | None = Field(
        default=None, alias="signature-digest-method"
    )

    # Team mapping + session lifetime.
    team_management_enabled: bool | None = Field(
        default=None, alias="team-management-enabled"
    )
    sso_api_token_session_timeout: int | None = Field(
        default=None, alias="sso-api-token-session-timeout"
    )

    # Provider hint.
    provider_type: SAMLProviderType | None = Field(default=None, alias="provider-type")


class AdminSAMLSettingsUpdateOptions(BaseModel):
    """Partial update options for SAML settings.

    Every field is optional; only fields the caller sets are emitted on
    the wire, and the server preserves the rest. Pass
    ``provider_type=SAMLProviderType.OKTA`` to switch the provider hint;
    pass ``private_key="..."`` to install a new SP signing key (sensitive,
    not returned on read).
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    enabled: bool | None = None
    debug: bool | None = None

    idp_cert: str | None = Field(default=None, alias="idp-cert")
    slo_endpoint_url: str | None = Field(default=None, alias="slo-endpoint-url")
    sso_endpoint_url: str | None = Field(default=None, alias="sso-endpoint-url")

    certificate: str | None = None
    private_key: str | None = Field(default=None, alias="private-key")

    attr_username: str | None = Field(default=None, alias="attr-username")
    attr_groups: str | None = Field(default=None, alias="attr-groups")
    attr_site_admin: str | None = Field(default=None, alias="attr-site-admin")
    site_admin_role: str | None = Field(default=None, alias="site-admin-role")

    authn_requests_signed: bool | None = Field(
        default=None, alias="authn-requests-signed"
    )
    want_assertions_signed: bool | None = Field(
        default=None, alias="want-assertions-signed"
    )
    signature_signing_method: SAMLSignatureMethod | None = Field(
        default=None, alias="signature-signing-method"
    )
    signature_digest_method: SAMLSignatureMethod | None = Field(
        default=None, alias="signature-digest-method"
    )

    team_management_enabled: bool | None = Field(
        default=None, alias="team-management-enabled"
    )
    sso_api_token_session_timeout: int | None = Field(
        default=None, alias="sso-api-token-session-timeout"
    )

    provider_type: SAMLProviderType | None = Field(default=None, alias="provider-type")


# ---------------------------------------------------------------------------
# SCIM settings
# ---------------------------------------------------------------------------


class AdminSCIMSettings(BaseModel):
    """Snapshot of the organisation's SCIM settings on TFE."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str | None = None
    enabled: bool | None = None
    paused: bool | None = None
    site_admin_group_scim_id: str | None = Field(
        default=None, alias="site-admin-group-scim-id"
    )
    site_admin_group_display_name: str | None = Field(
        default=None, alias="site-admin-group-display-name"
    )


class AdminSCIMSettingsUpdateOptions(BaseModel):
    """Partial update options for SCIM settings.

    ``site_admin_group_scim_id`` has special wire semantics:

    - Omit it (don't pass the kwarg) and the server keeps the current
      value.
    - Pass ``site_admin_group_scim_id=None`` explicitly and the wire
      payload contains ``"site-admin-group-scim-id": null``, which
      revokes the SCIM site-admin mapping.

    Pydantic's ``exclude_none=True`` cannot distinguish the two cases, so
    the resource layer calls :meth:`to_payload` which uses
    ``model_fields_set`` to tell them apart.
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    enabled: bool | None = None
    paused: bool | None = None
    site_admin_group_scim_id: str | None = Field(
        default=None, alias="site-admin-group-scim-id"
    )

    def to_payload(self) -> dict[str, Any]:
        """Build the JSON:API ``attributes`` dict honouring the
        omit-vs-explicit-null distinction documented above.
        """
        attrs: dict[str, Any] = {}
        set_fields = self.model_fields_set
        if "enabled" in set_fields and self.enabled is not None:
            attrs["enabled"] = self.enabled
        if "paused" in set_fields and self.paused is not None:
            attrs["paused"] = self.paused
        # site_admin_group_scim_id: None means "send JSON null". Only the
        # explicit-unset path drops the key entirely.
        if "site_admin_group_scim_id" in set_fields:
            attrs["site-admin-group-scim-id"] = self.site_admin_group_scim_id
        return attrs


# ---------------------------------------------------------------------------
# SCIM tokens
# ---------------------------------------------------------------------------


class AdminSCIMToken(BaseModel):
    """A SCIM provisioning token. ``token`` (the plaintext bearer value)
    is only populated on the response to :meth:`create`; ``list`` and
    :meth:`read` always return ``None`` for that field.
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str | None = None
    description: str | None = None
    token: str | None = None
    expired_at: datetime | None = Field(default=None, alias="expired-at")
    created_at: datetime | None = Field(default=None, alias="created-at")
    last_used_at: datetime | None = Field(default=None, alias="last-used-at")


class AdminSCIMTokenCreateOptions(BaseModel):
    """Options for minting a new SCIM token.

    ``description`` is required by this SDK (presence + non-empty); the
    upstream API marks it optional but a missing or empty description
    leaves the token un-identifiable in audit, so the SDK enforces it.
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    description: str = Field(
        ..., description="Human-readable description shown in audit logs."
    )
    expired_at: datetime | None = Field(default=None, alias="expired-at")


# ---------------------------------------------------------------------------
# SMTP settings
# ---------------------------------------------------------------------------


class SMTPAuthType(str, Enum):
    """Authentication mechanism for the SMTP relay."""

    NONE = "none"
    PLAIN = "plain"
    LOGIN = "login"


class AdminSMTPSettings(BaseModel):
    """Snapshot of the organisation's SMTP relay settings on TFE.

    ``password`` and ``test_email_address`` are write-only on the upstream
    API and are never returned by ``read()`` — modelled here as fields
    only on the update options below.
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str | None = None
    enabled: bool | None = None
    host: str | None = None
    port: int | None = None
    sender: str | None = None
    auth: SMTPAuthType | None = None
    username: str | None = None


class AdminSMTPSettingsUpdateOptions(BaseModel):
    """Partial update options for SMTP settings.

    Every field is optional. ``password`` is sensitive; the transport
    logger redacts it before debug output. ``test_email_address`` is a
    write-only signal — when set, TFE sends a verification email to that
    address as part of the PATCH; the field is not returned on read.
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    enabled: bool | None = None
    host: str | None = None
    port: int | None = None
    sender: str | None = None
    auth: SMTPAuthType | None = None
    username: str | None = None
    password: str | None = None
    test_email_address: str | None = Field(default=None, alias="test-email-address")
