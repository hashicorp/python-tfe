"""Unit tests for the policy_set_parameter module."""

from unittest.mock import Mock, patch

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import (
    InvalidCategoryError,
    InvalidParamIDError,
    InvalidPolicySetIDError,
    RequiredKeyError,
)
from pytfe.models import (
    CategoryType,
    PolicySetParameter,
    PolicySetParameterCreateOptions,
    PolicySetParameterListOptions,
    PolicySetParameterUpdateOptions,
)
from pytfe.resources.policy_set_parameter import PolicySetParameters


class TestPolicySetParameters:
    """Test the PolicySetParameters service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def policy_set_parameters_service(self, mock_transport):
        """Create a PolicySetParameters service with mocked transport."""
        return PolicySetParameters(mock_transport)

    def test_list_parameters_validations(self, policy_set_parameters_service):
        """Test list method with invalid policy set ID."""

        # Test empty policy set ID
        with pytest.raises(InvalidPolicySetIDError):
            list(policy_set_parameters_service.list(""))

        # Test None policy set ID
        with pytest.raises(InvalidPolicySetIDError):
            list(policy_set_parameters_service.list(None))

    def test_list_parameters_success_without_options(
        self, policy_set_parameters_service
    ):
        """Test successful list operation without options."""

        mock_data = [
            {
                "id": "var-123",
                "attributes": {
                    "key": "test_param",
                    "value": "test_value",
                    "category": "policy-set",
                    "sensitive": False,
                },
                "relationships": {
                    "configurable": {
                        "data": {"id": "polset-123", "type": "policy-sets"}
                    }
                },
            }
        ]

        with patch.object(policy_set_parameters_service, "_list") as mock_list:
            mock_list.return_value = iter(mock_data)

            result = list(policy_set_parameters_service.list("polset-123"))

            mock_list.assert_called_once_with(
                "/api/v2/policy-sets/polset-123/parameters", params={}
            )

            assert len(result) == 1
            assert result[0].id == "var-123"
            assert result[0].key == "test_param"
            assert result[0].value == "test_value"
            assert result[0].category == CategoryType.POLICY_SET
            assert result[0].sensitive is False

    def test_list_parameters_with_options(self, policy_set_parameters_service):
        """Test successful list operation with pagination options."""

        mock_data = []

        with patch.object(policy_set_parameters_service, "_list") as mock_list:
            mock_list.return_value = iter(mock_data)

            options = PolicySetParameterListOptions(page_size=10)
            result = list(policy_set_parameters_service.list("polset-123", options))

            mock_list.assert_called_once_with(
                "/api/v2/policy-sets/polset-123/parameters",
                params={"page[size]": 10},
            )

            assert len(result) == 0

    def test_list_parameters_returns_iterator(self, policy_set_parameters_service):
        """Test that list method returns an iterator."""

        with patch.object(policy_set_parameters_service, "_list") as mock_list:
            mock_list.return_value = iter([])

            result = policy_set_parameters_service.list("polset-123")

            # Verify it's an iterator
            assert hasattr(result, "__iter__")
            assert hasattr(result, "__next__")

    def test_create_parameter_validations(self, policy_set_parameters_service):
        """Test create method validations."""

        # Test invalid policy set ID
        options = PolicySetParameterCreateOptions(key="test")
        with pytest.raises(InvalidPolicySetIDError):
            policy_set_parameters_service.create("", options)

        # Test missing key
        options = PolicySetParameterCreateOptions(key="")
        with pytest.raises(RequiredKeyError):
            policy_set_parameters_service.create("polset-123", options)

        # Test invalid category (not policy-set)
        options = PolicySetParameterCreateOptions(
            key="test", category=CategoryType.TERRAFORM
        )
        with pytest.raises(InvalidCategoryError):
            policy_set_parameters_service.create("polset-123", options)

    def test_create_parameter_success(
        self, policy_set_parameters_service, mock_transport
    ):
        """Test successful create operation."""

        mock_response_data = {
            "data": {
                "id": "var-456",
                "attributes": {
                    "key": "new_param",
                    "value": "new_value",
                    "category": "policy-set",
                    "sensitive": False,
                },
                "relationships": {
                    "configurable": {
                        "data": {"id": "polset-123", "type": "policy-sets"}
                    }
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        options = PolicySetParameterCreateOptions(
            key="new_param", value="new_value", sensitive=False
        )

        result = policy_set_parameters_service.create("polset-123", options)

        mock_transport.request.assert_called_once_with(
            "POST",
            path="api/v2/policy-sets/polset-123/parameters",
            json_body={
                "data": {
                    "type": "vars",
                    "attributes": {
                        "key": "new_param",
                        "value": "new_value",
                        "category": "policy-set",
                        "sensitive": False,
                    },
                }
            },
        )

        assert isinstance(result, PolicySetParameter)
        assert result.id == "var-456"
        assert result.key == "new_param"
        assert result.value == "new_value"

    def test_create_sensitive_parameter(
        self, policy_set_parameters_service, mock_transport
    ):
        """Test creating a sensitive parameter."""

        mock_response_data = {
            "data": {
                "id": "var-789",
                "attributes": {
                    "key": "secret_param",
                    "value": None,
                    "category": "policy-set",
                    "sensitive": True,
                },
                "relationships": {
                    "configurable": {
                        "data": {"id": "polset-123", "type": "policy-sets"}
                    }
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        options = PolicySetParameterCreateOptions(
            key="secret_param", value="secret_value", sensitive=True
        )

        result = policy_set_parameters_service.create("polset-123", options)

        assert isinstance(result, PolicySetParameter)
        assert result.id == "var-789"
        assert result.key == "secret_param"
        assert result.value is None  # Sensitive values are not returned
        assert result.sensitive is True

    def test_read_parameter_validations(self, policy_set_parameters_service):
        """Test read method validations."""

        # Test invalid policy set ID
        with pytest.raises(InvalidPolicySetIDError):
            policy_set_parameters_service.read("", "var-123")

        # Test invalid parameter ID
        with pytest.raises(InvalidParamIDError):
            policy_set_parameters_service.read("polset-123", "")

    def test_read_parameter_success(
        self, policy_set_parameters_service, mock_transport
    ):
        """Test successful read operation."""

        mock_response_data = {
            "data": {
                "id": "var-789",
                "attributes": {
                    "key": "existing_param",
                    "value": "existing_value",
                    "category": "policy-set",
                    "sensitive": False,
                },
                "relationships": {
                    "configurable": {
                        "data": {"id": "polset-123", "type": "policy-sets"}
                    }
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        result = policy_set_parameters_service.read("polset-123", "var-789")

        mock_transport.request.assert_called_once_with(
            "GET", path="api/v2/policy-sets/polset-123/parameters/var-789"
        )

        assert isinstance(result, PolicySetParameter)
        assert result.id == "var-789"
        assert result.key == "existing_param"
        assert result.value == "existing_value"

    def test_update_parameter_validations(self, policy_set_parameters_service):
        """Test update method validations."""

        options = PolicySetParameterUpdateOptions(value="updated")

        # Test invalid policy set ID
        with pytest.raises(InvalidPolicySetIDError):
            policy_set_parameters_service.update("", "var-123", options)

        # Test invalid parameter ID
        with pytest.raises(InvalidParamIDError):
            policy_set_parameters_service.update("polset-123", "", options)

    def test_update_parameter_success(
        self, policy_set_parameters_service, mock_transport
    ):
        """Test successful update operation."""

        mock_response_data = {
            "data": {
                "id": "var-789",
                "attributes": {
                    "key": "updated_param",
                    "value": "updated_value",
                    "category": "policy-set",
                    "sensitive": False,
                },
                "relationships": {
                    "configurable": {
                        "data": {"id": "polset-123", "type": "policy-sets"}
                    }
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        options = PolicySetParameterUpdateOptions(
            key="updated_param", value="updated_value"
        )

        result = policy_set_parameters_service.update("polset-123", "var-789", options)

        mock_transport.request.assert_called_once_with(
            "PATCH",
            path="api/v2/policy-sets/polset-123/parameters/var-789",
            json_body={
                "data": {
                    "type": "vars",
                    "id": "var-789",
                    "attributes": {"key": "updated_param", "value": "updated_value"},
                }
            },
        )

        assert isinstance(result, PolicySetParameter)
        assert result.id == "var-789"
        assert result.key == "updated_param"
        assert result.value == "updated_value"

    def test_update_parameter_to_sensitive(
        self, policy_set_parameters_service, mock_transport
    ):
        """Test updating a parameter to make it sensitive."""

        mock_response_data = {
            "data": {
                "id": "var-789",
                "attributes": {
                    "key": "param",
                    "value": None,
                    "category": "policy-set",
                    "sensitive": True,
                },
                "relationships": {
                    "configurable": {
                        "data": {"id": "polset-123", "type": "policy-sets"}
                    }
                },
            }
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        options = PolicySetParameterUpdateOptions(sensitive=True)

        result = policy_set_parameters_service.update("polset-123", "var-789", options)

        assert isinstance(result, PolicySetParameter)
        assert result.sensitive is True
        assert result.value is None

    def test_delete_parameter_validations(self, policy_set_parameters_service):
        """Test delete method validations."""

        # Test invalid policy set ID
        with pytest.raises(InvalidPolicySetIDError):
            policy_set_parameters_service.delete("", "var-123")

        # Test invalid parameter ID
        with pytest.raises(InvalidParamIDError):
            policy_set_parameters_service.delete("polset-123", "")

    def test_delete_parameter_success(
        self, policy_set_parameters_service, mock_transport
    ):
        """Test successful delete operation."""

        result = policy_set_parameters_service.delete("polset-123", "var-789")

        mock_transport.request.assert_called_once_with(
            "DELETE", path="api/v2/policy-sets/polset-123/parameters/var-789"
        )

        assert result is None
