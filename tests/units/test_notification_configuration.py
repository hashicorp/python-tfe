# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""
Unit tests for Notification Configuration API.

Tests all CRUD operations: List, Create, Read, Update, Delete, and Verify.
"""

from unittest.mock import Mock

import pytest

from pytfe.errors import InvalidOrgError, ValidationError
from pytfe.models.notification_configuration import (
    DeliveryResponse,
    NotificationConfiguration,
    NotificationConfigurationCreateOptions,
    NotificationConfigurationList,
    NotificationConfigurationListOptions,
    NotificationConfigurationSubscribableChoice,
    NotificationConfigurationUpdateOptions,
    NotificationDestinationType,
    NotificationTriggerType,
)
from pytfe.resources.notification_configuration import NotificationConfigurations


class TestNotificationConfigurations:
    """Test suite for notification configuration operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_transport = Mock()
        self.notifications = NotificationConfigurations(self.mock_transport)

        # Sample notification configuration data
        self.sample_nc_data = {
            "id": "nc-123456789",
            "attributes": {
                "created-at": "2023-01-01T10:00:00Z",
                "updated-at": "2023-01-01T10:00:00Z",
                "destination-type": "generic",
                "enabled": True,
                "name": "Test Notification",
                "token": "test-token",
                "url": "https://example.com/webhook",
                "triggers": ["run:created", "run:completed"],
                "email-addresses": [],
                "delivery-responses": [],
            },
            "relationships": {
                "subscribable": {"data": {"type": "workspaces", "id": "ws-123456789"}},
                "users": {"data": []},
            },
        }

    def test_list_workspace_notifications(self):
        """Test listing notification configurations for a workspace."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [self.sample_nc_data],
            "meta": {
                "pagination": {
                    "current-page": 1,
                    "page-size": 20,
                    "prev-page": None,
                    "next-page": None,
                    "total-pages": 1,
                    "total-count": 1,
                }
            },
        }
        self.mock_transport.request.return_value = mock_response

        # Test list operation
        workspace_id = "ws-123456789"
        result_iter = self.notifications.list(workspace_id)
        items = list(result_iter)

        # Verify API call (occurs when iterator is consumed)
        self.mock_transport.request.assert_called_once()
        call_args = self.mock_transport.request.call_args
        assert call_args[0][0] == "GET"
        assert (
            call_args[0][1]
            == f"/api/v2/workspaces/{workspace_id}/notification-configurations"
        )
        params = call_args[1].get("params")
        assert isinstance(params, dict)
        assert "page[number]" in params and "page[size]" in params
        assert params["page[number]"] == 1
        assert params["page[size]"] == 100

        # Verify result
        assert len(items) == 1
        assert isinstance(items[0], NotificationConfiguration)
        assert items[0].id == "nc-123456789"
        assert items[0].name == "Test Notification"

    def test_list_team_notifications(self):
        """Test listing notification configurations for a team."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [self.sample_nc_data],
            "meta": {
                "pagination": {"current-page": 1, "page-size": 20, "total-count": 1}
            },
        }
        self.mock_transport.request.return_value = mock_response

        # Test list operation with team
        team_id = "team-123456789"
        team_choice = NotificationConfigurationSubscribableChoice(team={"id": team_id})
        options = NotificationConfigurationListOptions(subscribable_choice=team_choice)

        result_iter = self.notifications.list(team_id, options)
        items = list(result_iter)

        # Verify API call (occurs when iterator is consumed)
        self.mock_transport.request.assert_called_once()
        call_args = self.mock_transport.request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == f"/api/v2/teams/{team_id}/notification-configurations"
        params = call_args[1].get("params")
        assert isinstance(params, dict)
        assert "page[number]" in params and "page[size]" in params
        assert params["page[number]"] == 1
        assert params["page[size]"] == 100

        # Verify result
        assert len(items) == 1
        assert isinstance(items[0], NotificationConfiguration)

    def test_list_with_pagination(self):
        """Test listing with pagination options."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [],
            "meta": {
                "pagination": {"current-page": 2, "page-size": 50, "total-count": 0}
            },
        }
        self.mock_transport.request.return_value = mock_response

        # Test with pagination
        workspace_id = "ws-123456789"
        options = NotificationConfigurationListOptions(page_size=50)

        result_iter = self.notifications.list(workspace_id, options)
        _ = list(result_iter)

        # page_size from options is respected by _list(); page[number] is controlled by _list()
        self.mock_transport.request.assert_called_once()
        call_args = self.mock_transport.request.call_args
        assert call_args[0][0] == "GET"
        assert (
            call_args[0][1]
            == f"/api/v2/workspaces/{workspace_id}/notification-configurations"
        )
        params = call_args[1].get("params")
        assert isinstance(params, dict)
        assert "page[number]" in params and "page[size]" in params
        assert params["page[number]"] == 1
        assert params["page[size]"] == 50

    def test_list_invalid_id(self):
        """Test list with invalid subscribable ID."""
        with pytest.raises(InvalidOrgError):
            list(self.notifications.list(""))

    def test_create_workspace_notification(self):
        """Test creating a notification configuration for a workspace."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {"data": self.sample_nc_data}
        self.mock_transport.request.return_value = mock_response

        # Create options
        options = NotificationConfigurationCreateOptions(
            destination_type=NotificationDestinationType.GENERIC,
            enabled=True,
            name="Test Notification",
            token="test-token",
            url="https://example.com/webhook",
            triggers=[
                NotificationTriggerType.CREATED,
                NotificationTriggerType.COMPLETED,
            ],
        )

        # Test create operation
        workspace_id = "ws-123456789"
        result = self.notifications.create(workspace_id, options)

        # Verify API call
        call_args = self.mock_transport.request.call_args
        assert call_args[0][0] == "POST"
        assert (
            call_args[0][1]
            == f"/api/v2/workspaces/{workspace_id}/notification-configurations"
        )

        payload = call_args[1]["json_body"]
        assert payload["data"]["type"] == "notification-configurations"
        assert payload["data"]["attributes"]["name"] == "Test Notification"
        assert payload["data"]["attributes"]["destination-type"] == "generic"

        # Verify result
        assert isinstance(result, NotificationConfiguration)
        assert result.id == "nc-123456789"
        assert result.name == "Test Notification"

    def test_create_team_notification(self):
        """Test creating a notification configuration for a team."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {"data": self.sample_nc_data}
        self.mock_transport.request.return_value = mock_response

        # Create options with team choice
        team_choice = NotificationConfigurationSubscribableChoice(
            team={"id": "team-123456789"}
        )
        options = NotificationConfigurationCreateOptions(
            destination_type=NotificationDestinationType.SLACK,
            enabled=False,
            name="Team Slack Notification",
            url="https://hooks.slack.com/webhook",
            triggers=[NotificationTriggerType.CHANGE_REQUEST_CREATED],
            subscribable_choice=team_choice,
        )

        # Test create operation
        team_id = "team-123456789"
        self.notifications.create(team_id, options)

        # Verify API call uses teams endpoint
        call_args = self.mock_transport.request.call_args
        assert call_args[0][1] == f"/api/v2/teams/{team_id}/notification-configurations"

    def test_create_email_notification(self):
        """Test creating an email notification configuration."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {"data": self.sample_nc_data}
        self.mock_transport.request.return_value = mock_response

        # Create email notification options
        options = NotificationConfigurationCreateOptions(
            destination_type=NotificationDestinationType.EMAIL,
            enabled=True,
            name="Email Notification",
            email_addresses=["admin@example.com"],
            triggers=[NotificationTriggerType.ERRORED],
        )

        # Test create operation
        workspace_id = "ws-123456789"
        self.notifications.create(workspace_id, options)

        # Verify API call
        call_args = self.mock_transport.request.call_args
        payload = call_args[1]["json_body"]
        assert payload["data"]["attributes"]["destination-type"] == "email"
        assert payload["data"]["attributes"]["email-addresses"] == ["admin@example.com"]

    def test_create_validation_errors(self):
        """Test create with validation errors."""
        # Test missing required fields
        options = NotificationConfigurationCreateOptions(
            destination_type=NotificationDestinationType.GENERIC,
            enabled=True,
            name="",  # Empty name should fail validation
            url="https://example.com",
        )

        with pytest.raises(ValidationError) as exc_info:
            self.notifications.create("ws-123456789", options)

        assert "Name is required" in str(exc_info.value)

    def test_create_url_validation(self):
        """Test create with URL validation for certain destination types."""
        # Test missing URL for generic destination
        options = NotificationConfigurationCreateOptions(
            destination_type=NotificationDestinationType.GENERIC,
            enabled=True,
            name="Test Notification",
            # Missing URL
        )

        with pytest.raises(ValidationError) as exc_info:
            self.notifications.create("ws-123456789", options)

        assert "URL is required" in str(exc_info.value)

    def test_create_invalid_id(self):
        """Test create with invalid workspace ID."""
        options = NotificationConfigurationCreateOptions(
            destination_type=NotificationDestinationType.GENERIC,
            enabled=True,
            name="Test Notification",
            url="https://example.com",
        )

        with pytest.raises(InvalidOrgError):
            self.notifications.create("", options)

    def test_read_notification_configuration(self):
        """Test reading a notification configuration by ID."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {"data": self.sample_nc_data}
        self.mock_transport.request.return_value = mock_response

        # Test read operation
        nc_id = "nc-123456789"
        result = self.notifications.read(nc_id)

        # Verify API call
        self.mock_transport.request.assert_called_once_with(
            "GET", f"/api/v2/notification-configurations/{nc_id}"
        )

        # Verify result
        assert isinstance(result, NotificationConfiguration)
        assert result.id == "nc-123456789"
        assert result.name == "Test Notification"
        assert result.enabled is True

    def test_read_invalid_id(self):
        """Test read with invalid notification configuration ID."""
        with pytest.raises(InvalidOrgError):
            self.notifications.read("")

    def test_update_notification_configuration(self):
        """Test updating a notification configuration."""
        # Mock API response
        updated_data = self.sample_nc_data.copy()
        updated_data["attributes"]["name"] = "Updated Notification"
        updated_data["attributes"]["enabled"] = False

        mock_response = Mock()
        mock_response.json.return_value = {"data": updated_data}
        self.mock_transport.request.return_value = mock_response

        # Update options
        options = NotificationConfigurationUpdateOptions(
            name="Updated Notification", enabled=False
        )

        # Test update operation
        nc_id = "nc-123456789"
        result = self.notifications.update(nc_id, options)

        # Verify API call
        call_args = self.mock_transport.request.call_args
        assert call_args[0][0] == "PATCH"
        assert call_args[0][1] == f"/api/v2/notification-configurations/{nc_id}"

        payload = call_args[1]["json_body"]
        assert payload["data"]["id"] == nc_id
        assert payload["data"]["attributes"]["name"] == "Updated Notification"
        assert payload["data"]["attributes"]["enabled"] is False

        # Verify result
        assert isinstance(result, NotificationConfiguration)
        assert result.name == "Updated Notification"
        assert result.enabled is False

    def test_update_triggers(self):
        """Test updating notification triggers."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {"data": self.sample_nc_data}
        self.mock_transport.request.return_value = mock_response

        # Update triggers
        options = NotificationConfigurationUpdateOptions(
            triggers=[
                NotificationTriggerType.PLANNING,
                NotificationTriggerType.APPLYING,
                NotificationTriggerType.ERRORED,
            ]
        )

        # Test update operation
        nc_id = "nc-123456789"
        self.notifications.update(nc_id, options)

        # Verify API call includes triggers
        call_args = self.mock_transport.request.call_args
        payload = call_args[1]["json_body"]
        expected_triggers = ["run:planning", "run:applying", "run:errored"]
        assert payload["data"]["attributes"]["triggers"] == expected_triggers

    def test_update_validation_errors(self):
        """Test update with validation errors."""
        # Test empty name
        options = NotificationConfigurationUpdateOptions(name="")

        with pytest.raises(ValidationError) as exc_info:
            self.notifications.update("nc-123456789", options)

        assert "Name cannot be empty" in str(exc_info.value)

    def test_update_invalid_id(self):
        """Test update with invalid notification configuration ID."""
        options = NotificationConfigurationUpdateOptions(name="New Name")

        with pytest.raises(InvalidOrgError):
            self.notifications.update("", options)

    def test_delete_notification_configuration(self):
        """Test deleting a notification configuration."""
        # Mock API response (DELETE returns no content)
        mock_response = Mock()
        self.mock_transport.request.return_value = mock_response

        # Test delete operation
        nc_id = "nc-123456789"
        self.notifications.delete(nc_id)

        # Verify API call
        self.mock_transport.request.assert_called_once_with(
            "DELETE", f"/api/v2/notification-configurations/{nc_id}"
        )

    def test_delete_invalid_id(self):
        """Test delete with invalid notification configuration ID."""
        with pytest.raises(InvalidOrgError):
            self.notifications.delete("")

    def test_verify_notification_configuration(self):
        """Test verifying a notification configuration."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {"data": self.sample_nc_data}
        self.mock_transport.request.return_value = mock_response

        # Test verify operation
        nc_id = "nc-123456789"
        result = self.notifications.verify(nc_id)

        # Verify API call
        self.mock_transport.request.assert_called_once_with(
            "POST",
            f"/api/v2/notification-configurations/{nc_id}/actions/verify",
            json_body={},
        )

        # Verify result
        assert isinstance(result, NotificationConfiguration)
        assert result.id == "nc-123456789"

    def test_verify_invalid_id(self):
        """Test verify with invalid notification configuration ID."""
        with pytest.raises(InvalidOrgError):
            self.notifications.verify("")


class TestNotificationConfigurationModels:
    """Test suite for notification configuration models."""

    def test_notification_configuration_parsing(self):
        """Test parsing notification configuration from API data."""
        data = {
            "id": "nc-123456789",
            "created-at": "2023-01-01T10:00:00Z",
            "updated-at": "2023-01-01T10:00:00Z",
            "destination-type": "slack",
            "enabled": True,
            "name": "Slack Notification",
            "token": "token-123",
            "url": "https://hooks.slack.com/webhook",
            "triggers": ["run:created", "run:errored"],
            "email-addresses": [],
            "delivery-responses": [
                {
                    "body": "OK",
                    "code": "200",
                    "headers": {},
                    "sent-at": "2023-01-01T10:00:00Z",
                    "successful": "true",
                    "url": "https://hooks.slack.com/webhook",
                }
            ],
        }

        nc = NotificationConfiguration(data)

        assert nc.id == "nc-123456789"
        assert nc.name == "Slack Notification"
        assert nc.enabled is True
        assert nc.destination_type == "slack"
        assert len(nc.triggers) == 2
        assert NotificationTriggerType.CREATED in nc.triggers
        assert NotificationTriggerType.ERRORED in nc.triggers
        assert len(nc.delivery_responses) == 1
        assert nc.delivery_responses[0].code == "200"

    def test_delivery_response_parsing(self):
        """Test parsing delivery response data."""
        data = {
            "body": "Success",
            "code": "200",
            "headers": {"Content-Type": ["application/json"]},
            "sent-at": "2023-01-01T10:00:00Z",
            "successful": "true",
            "url": "https://example.com/webhook",
        }

        dr = DeliveryResponse(data)

        assert dr.body == "Success"
        assert dr.code == "200"
        assert dr.headers == {"Content-Type": ["application/json"]}
        assert dr.successful == "true"
        assert dr.url == "https://example.com/webhook"
        assert dr.sent_at is not None

    def test_create_options_validation(self):
        """Test validation of create options."""
        # Valid options
        options = NotificationConfigurationCreateOptions(
            destination_type=NotificationDestinationType.GENERIC,
            enabled=True,
            name="Test Notification",
            url="https://example.com",
        )
        errors = options.validate()
        assert len(errors) == 0

        # Invalid options - missing name
        options = NotificationConfigurationCreateOptions(
            destination_type=NotificationDestinationType.GENERIC,
            enabled=True,
            name="",
            url="https://example.com",
        )
        errors = options.validate()
        assert "Name is required" in errors

        # Invalid options - missing URL for generic destination
        options = NotificationConfigurationCreateOptions(
            destination_type=NotificationDestinationType.GENERIC,
            enabled=True,
            name="Test Notification",
        )
        errors = options.validate()
        assert "URL is required for this destination type" in errors

    def test_update_options_validation(self):
        """Test validation of update options."""
        # Valid options
        options = NotificationConfigurationUpdateOptions(
            name="Updated Name", enabled=False
        )
        errors = options.validate()
        assert len(errors) == 0

        # Invalid options - empty name
        options = NotificationConfigurationUpdateOptions(name="")
        errors = options.validate()
        assert "Name cannot be empty" in errors

    def test_trigger_type_enum(self):
        """Test notification trigger type enum values."""
        assert NotificationTriggerType.CREATED.value == "run:created"
        assert NotificationTriggerType.PLANNING.value == "run:planning"
        assert NotificationTriggerType.NEEDS_ATTENTION.value == "run:needs_attention"
        assert NotificationTriggerType.APPLYING.value == "run:applying"
        assert NotificationTriggerType.COMPLETED.value == "run:completed"
        assert NotificationTriggerType.ERRORED.value == "run:errored"
        assert NotificationTriggerType.ASSESSMENT_DRIFTED.value == "assessment:drifted"
        assert NotificationTriggerType.ASSESSMENT_FAILED.value == "assessment:failed"
        assert (
            NotificationTriggerType.ASSESSMENT_CHECK_FAILED.value
            == "assessment:check_failure"
        )
        assert (
            NotificationTriggerType.WORKSPACE_AUTO_DESTROY_REMINDER.value
            == "workspace:auto_destroy_reminder"
        )
        assert (
            NotificationTriggerType.WORKSPACE_AUTO_DESTROY_RUN_RESULTS.value
            == "workspace:auto_destroy_run_results"
        )
        assert (
            NotificationTriggerType.CHANGE_REQUEST_CREATED.value
            == "change_request:created"
        )

    def test_destination_type_enum(self):
        """Test notification destination type enum values."""
        assert NotificationDestinationType.EMAIL.value == "email"
        assert NotificationDestinationType.GENERIC.value == "generic"
        assert NotificationDestinationType.SLACK.value == "slack"
        assert NotificationDestinationType.MICROSOFT_TEAMS.value == "microsoft-teams"

    def test_subscribable_choice(self):
        """Test notification configuration subscribable choice."""
        # Test workspace choice
        workspace_choice = NotificationConfigurationSubscribableChoice(
            workspace={"id": "ws-123456789"}
        )
        assert workspace_choice.workspace == {"id": "ws-123456789"}
        assert workspace_choice.team is None

        # Test team choice
        team_choice = NotificationConfigurationSubscribableChoice(
            team={"id": "team-123456789"}
        )
        assert team_choice.team == {"id": "team-123456789"}
        assert team_choice.workspace is None

    def test_notification_configuration_list(self):
        """Test notification configuration list parsing."""
        data = {
            "data": [
                {"attributes": {"id": "nc-1", "name": "NC 1"}},
                {"attributes": {"id": "nc-2", "name": "NC 2"}},
            ],
            "meta": {
                "pagination": {
                    "current-page": 1,
                    "page-size": 20,
                    "total-pages": 1,
                    "total-count": 2,
                }
            },
        }

        nc_list = NotificationConfigurationList(data)

        assert len(nc_list.items) == 2
        assert nc_list.current_page == 1
        assert nc_list.total_count == 2
        assert nc_list.items[0].name == "NC 1"
        assert nc_list.items[1].name == "NC 2"

    def test_list_options_to_dict(self):
        """Test list options conversion to dictionary."""
        options = NotificationConfigurationListOptions(page_size=50)
        result = options.to_dict()

        assert result == {"page[size]": 50}

    def test_create_options_to_dict(self):
        """Test create options conversion to dictionary."""
        options = NotificationConfigurationCreateOptions(
            destination_type=NotificationDestinationType.SLACK,
            enabled=True,
            name="Slack Notification",
            url="https://hooks.slack.com/webhook",
            triggers=[NotificationTriggerType.CREATED, NotificationTriggerType.ERRORED],
        )
        result = options.to_dict()

        assert result["type"] == "notification-configurations"
        assert result["attributes"]["destination-type"] == "slack"
        assert result["attributes"]["enabled"] is True
        assert result["attributes"]["name"] == "Slack Notification"
        assert result["attributes"]["url"] == "https://hooks.slack.com/webhook"
        assert result["attributes"]["triggers"] == ["run:created", "run:errored"]

    def test_update_options_to_dict(self):
        """Test update options conversion to dictionary."""
        options = NotificationConfigurationUpdateOptions(
            name="Updated Name",
            enabled=False,
            triggers=[NotificationTriggerType.COMPLETED],
        )
        result = options.to_dict()

        assert result["type"] == "notification-configurations"
        assert result["attributes"]["name"] == "Updated Name"
        assert result["attributes"]["enabled"] is False
        assert result["attributes"]["triggers"] == ["run:completed"]
