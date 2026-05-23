"""Unit tests for organization audit configuration service."""

import os
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from pytfe._http import HTTPTransport
from pytfe.errors import ERR_INVALID_ORG
from pytfe.models.organization_audit_configuration import (
    OrganizationAuditConfigAuditStreaming,
    OrganizationAuditConfigAuditTrails,
    OrganizationAuditConfiguration,
    OrganizationAuditConfigurationOptions,
    OrganizationAuditConfigurationTest,
)
from pytfe.resources.organization_audit_configuration import (
    OrganizationAuditConfigurations,
)


class TestOrganizationAuditConfigurations:
    @pytest.fixture
    def mock_transport(self):
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def service(self, mock_transport):
        return OrganizationAuditConfigurations(mock_transport)

    def test_read_success(self, service):
        mock_response_data = {
            "data": {
                "id": "acfg-123",
                "attributes": {
                    "audit-trails": {"enabled": True},
                    "hcp-audit-log-streaming": {
                        "enabled": False,
                        "organization-id": "org-123",
                        "use-default-organization": True,
                    },
                    "updated-at": "2025-01-01T00:00:00Z",
                },
                "relationships": {
                    "organization": {"data": {"id": "org-123", "type": "organizations"}}
                },
            }
        }
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data

        with patch.object(service, "t") as mock_t:
            mock_t.request.return_value = mock_response
            result = service.read("test-org")

            assert isinstance(result, OrganizationAuditConfiguration)
            assert result.id == "acfg-123"
            assert result.audit_trails is not None
            assert result.audit_trails.enabled is True
            assert result.organization is not None
            assert result.organization.id == "org-123"

            call_args = mock_t.request.call_args
            assert call_args[0][0] == "GET"
            assert (
                call_args[0][1] == "/api/v2/organizations/test-org/audit-configuration"
            )

    def test_read_validation_errors(self, service):
        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            service.read("")

        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            service.read(None)

    def test_test_success(self, service):
        mock_response = Mock()
        mock_response.json.return_value = {"request-id": "req-123"}

        with patch.object(service, "t") as mock_t:
            mock_t.request.return_value = mock_response
            result = service.test("test-org")

            assert isinstance(result, OrganizationAuditConfigurationTest)
            assert result.request_id == "req-123"

            call_args = mock_t.request.call_args
            assert call_args[0][0] == "POST"
            assert (
                call_args[0][1]
                == "/api/v2/organizations/test-org/audit-configuration/test"
            )

    def test_test_validation_errors(self, service):
        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            service.test("")

        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            service.test(None)

    def test_update_success(self, service):
        mock_response_data = {
            "data": {
                "id": "acfg-123",
                "attributes": {
                    "audit-trails": {"enabled": True},
                    "hcp-audit-log-streaming": {
                        "enabled": True,
                        "organization-id": "org-123",
                        "use-default-organization": False,
                    },
                    "updated-at": "2025-01-01T00:00:00Z",
                },
                "relationships": {
                    "organization": {"data": {"id": "org-123", "type": "organizations"}}
                },
            }
        }
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data

        with patch.object(service, "t") as mock_t:
            mock_t.request.return_value = mock_response

            options = OrganizationAuditConfigurationOptions(
                audit_trails=OrganizationAuditConfigAuditTrails(enabled=True),
                hcp_audit_log_streaming=OrganizationAuditConfigAuditStreaming(
                    enabled=True,
                    organization_id="org-123",
                    use_default_organization=False,
                ),
            )

            result = service.update("test-org", options)
            assert isinstance(result, OrganizationAuditConfiguration)

            call_args = mock_t.request.call_args
            assert call_args[0][0] == "PATCH"
            assert (
                call_args[0][1] == "/api/v2/organizations/test-org/audit-configuration"
            )
            assert call_args[1]["json_body"]["data"]["type"] == "audit-configurations"
            attrs = call_args[1]["json_body"]["data"]["attributes"]
            assert attrs["audit-trails"]["enabled"] is True
            assert attrs["hcp-audit-log-streaming"]["organization-id"] == "org-123"

    def test_update_validation_errors(self, service):
        options = OrganizationAuditConfigurationOptions(
            audit_trails=OrganizationAuditConfigAuditTrails(enabled=False)
        )

        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            service.update("", options)

        with pytest.raises(ValueError, match=ERR_INVALID_ORG):
            service.update(None, options)
