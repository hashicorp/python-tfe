# Copyright IBM Corp. 2025, 2026

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from .._jsonapi import attach_jsonapi
from ..errors import ERR_INVALID_ORG
from ..models.organization import Organization
from ..models.organization_audit_configuration import (
    OrganizationAuditConfiguration,
    OrganizationAuditConfigurationOptions,
    OrganizationAuditConfigurationTest,
)
from ..utils import valid_string_id
from ._base import _Service


class OrganizationAuditConfigurations(_Service):
    """Organization audit configuration service."""

    def read(self, organization: str) -> OrganizationAuditConfiguration:
        """Read an organization's audit configuration.

        Args:
            organization: The organization name (e.g. ``"my-org"``).

        Returns:
            The :class:`OrganizationAuditConfiguration`.

        Raises:
            ValueError: If ``organization`` is invalid, or if the response format
                is invalid.
            TFEError: If the API request fails.

        Example:
            >>> config = client.organization_audit_configurations.read("my-org")
            >>> print(config.audit_trails.enabled if config.audit_trails else None)
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        path = f"/api/v2/organizations/{quote(organization)}/audit-configuration"
        response = self.t.request("GET", path)
        payload = response.json() or {}
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ValueError("Invalid response format")

        return self._parse_audit_configuration(data)

    def test(self, organization: str) -> OrganizationAuditConfigurationTest:
        """Send a test audit event for an organization.

        Args:
            organization: The organization name (e.g. ``"my-org"``).

        Returns:
            The :class:`OrganizationAuditConfigurationTest`.

        Raises:
            ValueError: If ``organization`` is invalid, or if the response format
                is invalid.
            TFEError: If the API request fails.

        Example:
            >>> result = client.organization_audit_configurations.test("my-org")
            >>> print(result.request_id)
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        path = f"/api/v2/organizations/{quote(organization)}/audit-configuration/test"
        response = self.t.request("POST", path)
        payload = response.json() or {}
        if not isinstance(payload, dict):
            raise ValueError("Invalid response format")

        return OrganizationAuditConfigurationTest.model_validate(payload)

    def update(
        self,
        organization: str,
        options: OrganizationAuditConfigurationOptions,
    ) -> OrganizationAuditConfiguration:
        """Update an organization's audit configuration.

        Args:
            organization: The organization name (e.g. ``"my-org"``).
            options: The audit configuration settings, as a
                :class:`OrganizationAuditConfigurationOptions`.

        Returns:
            The updated :class:`OrganizationAuditConfiguration`.

        Raises:
            ValueError: If ``organization`` is invalid, or if the response format
                is invalid.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import OrganizationAuditConfigAuditTrails
            >>> from pytfe.models import OrganizationAuditConfigurationOptions
            >>> config = client.organization_audit_configurations.update(
            ...     "my-org",
            ...     OrganizationAuditConfigurationOptions(
            ...         audit_trails=OrganizationAuditConfigAuditTrails(enabled=True)
            ...     ),
            ... )
        """
        if not valid_string_id(organization):
            raise ValueError(ERR_INVALID_ORG)

        attrs = options.model_dump(by_alias=True, exclude_none=True)
        body: dict[str, Any] = {
            "data": {
                "type": "audit-configurations",
                "attributes": attrs,
            }
        }

        path = f"/api/v2/organizations/{quote(organization)}/audit-configuration"
        response = self.t.request("PATCH", path, json_body=body)
        payload = response.json() or {}
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ValueError("Invalid response format")

        return self._parse_audit_configuration(data)

    def _parse_audit_configuration(
        self, data: dict[str, Any]
    ) -> OrganizationAuditConfiguration:
        attrs = data.get("attributes", {})
        relationships = data.get("relationships", {})

        org = None
        org_data = relationships.get("organization", {}).get("data")
        if isinstance(org_data, dict):
            org = Organization(id=org_data.get("id"))

        return attach_jsonapi(
            OrganizationAuditConfiguration.model_validate(
                {
                    "id": data.get("id", ""),
                    "audit-trails": attrs.get("audit-trails"),
                    "hcp-audit-log-streaming": attrs.get("hcp-audit-log-streaming"),
                    "permissions": attrs.get("permissions"),
                    "timestamps": attrs.get("timestamps"),
                    "updated-at": attrs.get("updated-at"),
                    "organization": org,
                }
            ),
            data,
        )
