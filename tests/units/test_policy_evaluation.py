"""Unit tests for the policy evaluation module."""

from unittest.mock import Mock

import pytest

from pytfe._http import HTTPTransport
from pytfe.errors import InvalidTaskStageIDError
from pytfe.models.policy_evaluation import (
    PolicyEvaluation,
    PolicyEvaluationListOptions,
    PolicyEvaluationStatus,
)
from pytfe.resources.policy_evaluation import PolicyEvaluations


class TestPolicyEvaluations:
    """Test the PolicyEvaluations service class."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock HTTPTransport."""
        return Mock(spec=HTTPTransport)

    @pytest.fixture
    def policy_evaluations_service(self, mock_transport):
        """Create a PolicyEvaluations service with mocked transport."""
        return PolicyEvaluations(mock_transport)

    def test_list_validations(self, policy_evaluations_service):
        """Test list method with invalid task stage ID."""

        # Test empty task stage ID
        with pytest.raises(InvalidTaskStageIDError):
            list(policy_evaluations_service.list(""))

        # Test None task stage ID
        with pytest.raises(InvalidTaskStageIDError):
            list(policy_evaluations_service.list(None))

    def test_list_success_with_options(
        self, policy_evaluations_service, mock_transport
    ):
        """Test successful iteration with custom pagination options."""

        mock_response_data = {
            "data": [
                {
                    "id": "poleval-456",
                    "type": "policy-evaluations",
                    "attributes": {
                        "status": "failed",
                        "policy-kind": "opa",
                        "status-timestamp": {
                            "passed-at": None,
                            "failed-at": "2023-01-02T12:00:00Z",
                            "running-at": "2023-01-02T11:59:00Z",
                            "canceled-at": None,
                            "errored-at": None,
                        },
                        "result-count": {
                            "advisory-failed": 2,
                            "mandatory-failed": 1,
                            "passed": 3,
                            "errored": 0,
                        },
                        "created-at": "2023-01-02T11:58:00Z",
                        "updated-at": "2023-01-02T12:00:00Z",
                    },
                    "relationships": {
                        "policy-attachable": {
                            "data": {"id": "ts-456", "type": "task-stages"}
                        }
                    },
                }
            ]
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        options = PolicyEvaluationListOptions(page_size=5)
        result = list(policy_evaluations_service.list("ts-456", options=options))

        # Verify the request was made with correct parameters
        assert mock_transport.request.call_count == 1
        call_args = mock_transport.request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "api/v2/task-stages/ts-456/policy-evaluations"

        # Verify custom options were passed and merged with _list defaults
        params = call_args[1]["params"]
        assert params["page[size]"] == 5  # Custom value from options

        # Verify the result
        assert len(result) == 1
        assert isinstance(result[0], PolicyEvaluation)
        assert result[0].id == "poleval-456"
        assert result[0].status == PolicyEvaluationStatus.POLICYEVALUATIONFAILED
        assert result[0].result_count.advisory_failed == 2
        assert result[0].result_count.mandatory_failed == 1

    def test_list_empty_result(self, policy_evaluations_service, mock_transport):
        """Test iteration with no results."""

        mock_response_data = {"data": []}

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        result = list(policy_evaluations_service.list("ts-empty"))

        # Verify the request was made
        assert mock_transport.request.call_count == 1

        # Verify iterator yields no items
        assert len(result) == 0
        assert result == []

    def test_list_with_different_statuses(
        self, policy_evaluations_service, mock_transport
    ):
        """Test list operation returns evaluations with different statuses."""

        mock_response_data = {
            "data": [
                {
                    "id": "poleval-pending",
                    "type": "policy-evaluations",
                    "attributes": {
                        "status": "pending",
                        "policy-kind": "opa",
                        "status-timestamp": {},
                        "result-count": {
                            "advisory-failed": 0,
                            "mandatory-failed": 0,
                            "passed": 0,
                            "errored": 0,
                        },
                        "created-at": "2023-01-01T11:58:00Z",
                        "updated-at": "2023-01-01T11:58:00Z",
                    },
                    "relationships": {
                        "policy-attachable": {
                            "data": {"id": "ts-multi", "type": "task-stages"}
                        }
                    },
                },
                {
                    "id": "poleval-running",
                    "type": "policy-evaluations",
                    "attributes": {
                        "status": "running",
                        "policy-kind": "opa",
                        "status-timestamp": {"running-at": "2023-01-01T11:59:00Z"},
                        "result-count": {
                            "advisory-failed": 0,
                            "mandatory-failed": 0,
                            "passed": 0,
                            "errored": 0,
                        },
                        "created-at": "2023-01-01T11:58:00Z",
                        "updated-at": "2023-01-01T11:59:00Z",
                    },
                    "relationships": {
                        "policy-attachable": {
                            "data": {"id": "ts-multi", "type": "task-stages"}
                        }
                    },
                },
                {
                    "id": "poleval-errored",
                    "type": "policy-evaluations",
                    "attributes": {
                        "status": "errored",
                        "policy-kind": "opa",
                        "status-timestamp": {"errored-at": "2023-01-01T12:00:00Z"},
                        "result-count": {
                            "advisory-failed": 0,
                            "mandatory-failed": 0,
                            "passed": 0,
                            "errored": 1,
                        },
                        "created-at": "2023-01-01T11:58:00Z",
                        "updated-at": "2023-01-01T12:00:00Z",
                    },
                    "relationships": {
                        "policy-attachable": {
                            "data": {"id": "ts-multi", "type": "task-stages"}
                        }
                    },
                },
            ]
        }

        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_transport.request.return_value = mock_response

        result = list(policy_evaluations_service.list("ts-multi"))

        # Verify the iterator yields all items with correct statuses
        assert len(result) == 3
        assert result[0].status == PolicyEvaluationStatus.POLICYEVALUATIONPENDING
        assert result[1].status == PolicyEvaluationStatus.POLICYEVALUATIONRUNNING
        assert result[2].status == PolicyEvaluationStatus.POLICYEVALUATIONERRORED

        # Verify all are PolicyEvaluation instances
        assert all(isinstance(item, PolicyEvaluation) for item in result)
