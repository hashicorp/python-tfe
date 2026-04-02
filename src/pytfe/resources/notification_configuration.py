# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""
Notification Configuration Resources

This module provides CRUD operations for Terraform Cloud/Enterprise notification configurations.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import (
    InvalidOrgError,
    ValidationError,
)
from ..models.notification_configuration import (
    NotificationConfiguration,
    NotificationConfigurationCreateOptions,
    NotificationConfigurationListOptions,
    NotificationConfigurationUpdateOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class NotificationConfigurations(_Service):
    """Notification Configuration API for Terraform Enterprise."""

    def list(
        self,
        subscribable_id: str,
        options: NotificationConfigurationListOptions | None = None,
    ) -> Iterator[NotificationConfiguration]:
        """List all notification configurations associated with a workspace or team."""
        if not valid_string_id(subscribable_id):
            raise InvalidOrgError("Invalid subscribable ID")

        # Determine URL based on subscribable choice
        if options and options.subscribable_choice and options.subscribable_choice.team:
            path = f"/api/v2/teams/{subscribable_id}/notification-configurations"
        else:
            path = f"/api/v2/workspaces/{subscribable_id}/notification-configurations"

        params = options.to_dict() if options else None

        for d in self._list(path, params=params):
            yield self._parse_notification_configuration(d)

    def create(
        self, subscribable_id: str, options: NotificationConfigurationCreateOptions
    ) -> NotificationConfiguration:
        """Create a new notification configuration."""
        if not valid_string_id(subscribable_id):
            raise InvalidOrgError("Invalid subscribable ID provided")

        # Validate options
        validation_errors = options.validate()
        if validation_errors:
            raise ValidationError(
                f"Notification configuration validation failed: {', '.join(validation_errors)}"
            )

        # Determine URL based on subscribable choice
        if options.subscribable_choice and options.subscribable_choice.team:
            url = f"/api/v2/teams/{subscribable_id}/notification-configurations"
        else:
            url = f"/api/v2/workspaces/{subscribable_id}/notification-configurations"

        payload = {"data": options.to_dict()}

        try:
            r = self.t.request("POST", url, json_body=payload)
            jd = r.json()

            if "data" in jd:
                return self._parse_notification_configuration(jd["data"])

            raise ValidationError("Invalid response format from API")
        except Exception as e:
            # Enhance error messages for common scenarios
            error_msg = str(e).lower()
            if "verification failed" in error_msg and "404" in error_msg:
                raise ValidationError(
                    "Webhook URL verification failed - check that the URL is reachable and accepts POST requests"
                ) from e
            elif "not found" in error_msg:
                if "team" in url:
                    raise InvalidOrgError(
                        f"Team '{subscribable_id}' not found or teams not available in your plan"
                    ) from e
                else:
                    raise InvalidOrgError(
                        f"Workspace '{subscribable_id}' not found"
                    ) from e
            else:
                raise

    def read(self, notification_config_id: str) -> NotificationConfiguration:
        """Read a notification configuration by its ID."""
        if not valid_string_id(notification_config_id):
            raise InvalidOrgError("Invalid notification configuration ID provided")

        url = f"/api/v2/notification-configurations/{notification_config_id}"

        try:
            r = self.t.request("GET", url)
            jd = r.json()

            if "data" in jd:
                return self._parse_notification_configuration(jd["data"])

            raise ValidationError("Invalid response format from API")
        except Exception as e:
            error_msg = str(e).lower()
            if "not found" in error_msg:
                raise InvalidOrgError(
                    f"Notification configuration '{notification_config_id}' not found"
                ) from e
            else:
                raise

    def update(
        self,
        notification_config_id: str,
        options: NotificationConfigurationUpdateOptions,
    ) -> NotificationConfiguration:
        """Update an existing notification configuration."""
        if not valid_string_id(notification_config_id):
            raise InvalidOrgError("Invalid notification configuration ID")

        # Validate options
        validation_errors = options.validate()
        if validation_errors:
            raise ValidationError(f"Invalid options: {', '.join(validation_errors)}")

        url = f"/api/v2/notification-configurations/{notification_config_id}"

        payload = {"data": options.to_dict()}
        payload["data"]["id"] = notification_config_id

        r = self.t.request("PATCH", url, json_body=payload)
        jd = r.json()

        if "data" in jd:
            return self._parse_notification_configuration(jd["data"])

        raise ValidationError("Invalid response format from API")

    def delete(self, notification_config_id: str) -> None:
        """Delete a notification configuration by its ID."""
        if not valid_string_id(notification_config_id):
            raise InvalidOrgError("Invalid notification configuration ID")

        url = f"/api/v2/notification-configurations/{notification_config_id}"
        self.t.request("DELETE", url)

    def verify(self, notification_config_id: str) -> NotificationConfiguration:
        """Verify a notification configuration by delivering a verification payload."""
        if not valid_string_id(notification_config_id):
            raise InvalidOrgError("Invalid notification configuration ID provided")

        url = f"/api/v2/notification-configurations/{notification_config_id}/actions/verify"

        try:
            r = self.t.request("POST", url, json_body={})
            jd = r.json()

            if "data" in jd:
                return self._parse_notification_configuration(jd["data"])

            raise ValidationError("Invalid response format from API")
        except Exception as e:
            error_msg = str(e).lower()
            if "verification failed" in error_msg and "404" in error_msg:
                raise ValidationError(
                    "Webhook verification failed: URL returned 404. Check that your webhook URL is correct and accessible."
                ) from e
            elif "not found" in error_msg:
                raise InvalidOrgError(
                    f"Notification configuration '{notification_config_id}' not found"
                ) from e
            else:
                raise

    def _parse_notification_configuration(
        self, data: dict[str, Any]
    ) -> NotificationConfiguration:
        """Parse notification configuration data from API response."""
        attributes = data.get("attributes", {})
        attributes["id"] = data.get("id")

        # Handle relationships
        relationships = data.get("relationships", {})
        if "subscribable" in relationships:
            subscribable_data = relationships["subscribable"].get("data", {})
            attributes["subscribable-choice"] = subscribable_data

        if "users" in relationships:
            users_data = relationships["users"].get("data", [])
            attributes["email-users"] = users_data

        return NotificationConfiguration(attributes)
