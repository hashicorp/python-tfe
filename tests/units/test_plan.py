# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the plan module."""

from unittest.mock import Mock, patch

import pytest

from pytfe.errors import InvalidPlanIDError
from pytfe.resources.plan import Plans


class TestPlans:
    @pytest.fixture
    def plans_service(self):
        """Create a Plans service for testing."""
        mock_transport = Mock()
        return Plans(mock_transport)

    def test_plans_service_init(self, plans_service):
        """Test Plans service initialization."""
        assert plans_service.t is not None

    def test_read_plan_validation_errors(self, plans_service):
        """Test read method with invalid plan ID."""

        # Test empty plan ID
        with pytest.raises(InvalidPlanIDError):
            plans_service.read("")

        # Test None plan ID
        with pytest.raises(InvalidPlanIDError):
            plans_service.read(None)

    def test_read_plan_success(self, plans_service):
        """Test successful read operation."""

        mock_response_data = {
            "data": {
                "id": "plan-123",
                "attributes": {
                    "has-changes": True,
                    "generated-configuration": False,
                    "log-read-url": "https://example.com/logs/plan-123",
                    "resource-additions": 3,
                    "resource-changes": 1,
                    "resource-destructions": 0,
                    "resource-imports": 0,
                    "status": "finished",
                    "status-timestamps": {
                        "canceled-at": "2023-01-01T00:00:00Z",
                        "errored-at": "2023-01-01T00:00:00Z",
                        "finished-at": "2023-01-01T10:00:00Z",
                        "force-canceled-at": "2023-01-01T00:00:00Z",
                        "queued-at": "2023-01-01T09:00:00Z",
                        "started-at": "2023-01-01T09:30:00Z",
                    },
                    "exports": [],
                },
            }
        }

        with patch.object(plans_service, "t") as mock_transport:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_transport.request.return_value = mock_response

            result = plans_service.read("plan-123")

            # Verify request was made correctly
            mock_transport.request.assert_called_once_with(
                "GET", "/api/v2/plans/plan-123"
            )

            # Verify plan object
            assert result.id == "plan-123"
            assert result.has_changes is True
            assert result.generated_configuration is False
            assert result.log_read_url == "https://example.com/logs/plan-123"
            assert result.resource_additions == 3
            assert result.resource_changes == 1
            assert result.resource_destructions == 0
            assert result.resource_imports == 0
            assert result.status.value == "finished"

    def test_logs_success(self, plans_service):
        """Test successful logs operation."""

        # Mock the read method to return a plan with log URL
        mock_plan = Mock()
        mock_plan.log_read_url = "https://example.com/logs/plan-123"

        with patch.object(plans_service, "read", return_value=mock_plan):
            result = plans_service.logs("plan-123")

            # Verify read was called first
            plans_service.read.assert_called_once_with("plan-123")

            # The current implementation returns empty string as placeholder
            assert result == ""

    def test_read_json_output_success(self, plans_service):
        """Test successful read_json_output operation (200 response)."""

        mock_json_data = {
            "format_version": "1.1",
            "terraform_version": "1.5.0",
            "planned_values": {"root_module": {"resources": []}},
            "resource_changes": [
                {
                    "address": "resource.example",
                    "mode": "managed",
                    "type": "resource",
                    "name": "example",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {"name": "example"},
                    },
                }
            ],
        }

        with patch.object(plans_service, "t") as mock_transport:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_json_data
            mock_transport.request.return_value = mock_response

            result = plans_service.read_json_output("plan-123")

            mock_transport.request.assert_called_once_with(
                "GET", "/api/v2/plans/plan-123/json-output", allow_redirects=False
            )

            assert result == mock_json_data
            assert result["format_version"] == "1.1"
            assert result["terraform_version"] == "1.5.0"
            assert len(result["resource_changes"]) == 1
            assert result["resource_changes"][0]["change"]["actions"] == ["create"]

    def test_read_json_output_follows_redirect_without_auth(self, plans_service):
        """The 307 redirect target must be fetched with include_auth=False."""
        mock_json_data = {"format_version": "1.1"}

        with patch.object(plans_service, "t") as mock_transport:
            redirect_resp = Mock()
            redirect_resp.status_code = 307
            redirect_resp.headers = {
                "Location": "https://archivist.example/blob?sig=abc"
            }
            blob_resp = Mock()
            blob_resp.status_code = 200
            blob_resp.json.return_value = mock_json_data
            mock_transport.request.side_effect = [redirect_resp, blob_resp]

            result = plans_service.read_json_output("plan-123")

            assert result == mock_json_data
            assert mock_transport.request.call_count == 2
            first_call = mock_transport.request.call_args_list[0]
            second_call = mock_transport.request.call_args_list[1]
            assert first_call.args == ("GET", "/api/v2/plans/plan-123/json-output")
            assert first_call.kwargs == {"allow_redirects": False}
            assert second_call.args == (
                "GET",
                "https://archivist.example/blob?sig=abc",
            )
            assert second_call.kwargs == {"include_auth": False}
