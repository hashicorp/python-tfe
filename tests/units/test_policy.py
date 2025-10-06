"""Unit tests for the policy module."""

from unittest.mock import Mock, patch

import pytest

from tfe._http import HTTPTransport
from tfe.errors import (
    InvalidOrgError,
    InvalidPolicyIDError,
    RequiredNameError,
)
from tfe.models.policy import (
    EnforcementLevel,
    Policy,
    PolicyCreateOptions,
    PolicyList,
    PolicyUpdateOptions,
)
from tfe.models.policy_set import PolicyKind
from tfe.resources.policy import Policies


class TestPolicies:
    """Test the Policies service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def policies_service(self, mock_transport):
        """Create a Policies service with mocked transport."""
        return Policies(mock_transport)

    def test_list_policies_validations(self, policies_service):
        """Test list method with invalid organization."""

        # Test empty organization
        with pytest.raises(InvalidOrgError):
            policies_service.list("")

        # Test None organization
        with pytest.raises(InvalidOrgError):
            policies_service.list(None)

    def test_list_policies_success_without_options(
        self, policies_service, mock_transport
    ):
        """Test successful list operation without options."""

        mock_response_data = {
            "data": [
                {
                    "id": "pol-123",
                    "attributes": {
                        "name": "test-policy",
                        "kind": "sentinel",
                        "description": "Test policy description",
                        "enforcement-level": "advisory",
                        "policy-set-count": 1,
                        "updated-at": "2023-01-01T12:00:00Z",
                    },
                    "relationships": {
                        "organization": {
                            "data": {"id": "org-123", "type": "organizations"}
                        }
                    },
                }
            ],
            "meta": {
                "pagination": {
                    "current-page": 1,
                    "total-pages": 1,
                    "prev-page": None,
                    "next-page": None,
                    "total-count": 1,
                }
            },
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        result = policies_service.list("org-123")

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/organizations/org-123/policies", params=None
        )

        assert isinstance(result, PolicyList)
        assert len(result.items) == 1
        assert result.items[0].id == "pol-123"
        assert result.items[0].name == "test-policy"
        assert result.items[0].kind == PolicyKind.SENTINEL
        assert (
            result.items[0].enforcement_level == EnforcementLevel.ENFORCEMENT_ADVISORY
        )
        assert result.current_page == 1
        assert result.total_count == 1

    def test_create_policy_validations(self, policies_service):
        """Test create method validations."""

        # Test invalid organization
        options = PolicyCreateOptions(
            name="test-policy", enforcement_level=EnforcementLevel.ENFORCEMENT_ADVISORY
        )

        # Test validation method is called
        with patch.object(policies_service, "_valid_create_options") as mock_validate:
            mock_validate.return_value = RequiredNameError()

            with pytest.raises(RequiredNameError):
                policies_service.create("org-123", options)

    def test_create_policy_success(self, policies_service, mock_transport):
        """Test successful create operation."""

        mock_response_data = {
            "data": {
                "id": "pol-456",
                "attributes": {
                    "name": "new-policy",
                    "kind": "sentinel",
                    "enforcement-level": "hard-mandatory",
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        options = PolicyCreateOptions(
            name="new-policy",
            kind=PolicyKind.SENTINEL,
            enforcement_level=EnforcementLevel.ENFORCEMENT_HARD,
        )

        result = policies_service.create("org-123", options)

        mock_transport.request.assert_called_once_with(
            "POST",
            "/api/v2/organizations/org-123/policies",
            json_body={
                "data": {
                    "attributes": {
                        "name": "new-policy",
                        "kind": "sentinel",
                        "enforcement-level": "hard-mandatory",
                    },
                    "type": "policies",
                }
            },
        )

        assert isinstance(result, Policy)
        assert result.id == "pol-456"
        assert result.name == "new-policy"

    def test_read_policy_success(self, policies_service, mock_transport):
        """Test successful read operation."""

        mock_response_data = {
            "data": {
                "id": "pol-789",
                "attributes": {
                    "name": "existing-policy",
                    "kind": "opa",
                    "query": "terraform.main",
                    "enforcement-level": "advisory",
                },
                "relationships": {
                    "organization": {"data": {"id": "org-123", "type": "organizations"}}
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        result = policies_service.read("pol-789")

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/policies/pol-789"
        )

        assert isinstance(result, Policy)
        assert result.id == "pol-789"
        assert result.name == "existing-policy"
        assert result.kind == PolicyKind.OPA
        assert result.query == "terraform.main"

    def test_update_policy_success(self, policies_service, mock_transport):
        """Test successful update operation."""

        mock_response_data = {
            "data": {
                "id": "pol-789",
                "attributes": {
                    "name": "updated-policy",
                    "enforcement-level": "soft-mandatory",
                },
                "relationships": {
                    "organization": {"data": {"id": "org-123", "type": "organizations"}}
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        options = PolicyUpdateOptions(
            description="Updated description",
            enforcement_level=EnforcementLevel.ENFORCEMENT_SOFT,
        )

        result = policies_service.update("pol-789", options)

        mock_transport.request.assert_called_once_with(
            "PATCH",
            "/api/v2/policies/pol-789",
            json_body={
                "data": {
                    "type": "policies",
                    "attributes": {
                        "description": "Updated description",
                        "enforcement-level": "soft-mandatory",
                    },
                }
            },
        )

        assert isinstance(result, Policy)
        assert result.id == "pol-789"

    def test_delete_policy_validations(self, policies_service):
        """Test delete method with invalid policy ID."""

        with pytest.raises(InvalidPolicyIDError):
            policies_service.delete("")

    def test_delete_policy_success(self, policies_service, mock_transport):
        """Test successful delete operation."""

        policies_service.delete("pol-789")

        mock_transport.request.assert_called_once_with(
            "DELETE", "/api/v2/policies/pol-789"
        )

    def test_upload_policy_success_with_bytes(self, policies_service, mock_transport):
        """Test successful upload operation with bytes content."""

        policy_content = b"main = rule { true }"

        policies_service.upload("pol-789", policy_content)

        mock_transport.request.assert_called_once_with(
            "PUT",
            "/api/v2/policies/pol-789/upload",
            data=policy_content,
            headers={"Content-Type": "application/octet-stream"},
        )

    def test_download_policy_success(self, policies_service, mock_transport):
        """Test successful download operation."""

        policy_content = b"main = rule { true }"
        mock_response = Mock()
        mock_response.content = policy_content
        mock_transport.request.return_value = mock_response

        result = policies_service.download("pol-789")

        mock_transport.request.assert_called_once_with(
            "GET", "/api/v2/policies/pol-789/download"
        )

        assert result == policy_content

    def test_valid_create_options_success(self, policies_service):
        """Test _valid_create_options with valid options."""

        # Test valid Sentinel policy
        options = PolicyCreateOptions(
            name="test-policy",
            kind=PolicyKind.SENTINEL,
            enforcement_level=EnforcementLevel.ENFORCEMENT_HARD,
        )
        result = policies_service._valid_create_options(options)
        assert result is None

        # Test valid OPA policy
        options = PolicyCreateOptions(
            name="test-opa-policy",
            kind=PolicyKind.OPA,
            query="terraform.main",
            enforcement_level=EnforcementLevel.ENFORCEMENT_MANDATORY,
        )
        result = policies_service._valid_create_options(options)
        assert result is None
