# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""
Notification Configuration Models

This module provides models for working with Terraform Cloud/Enterprise notification configurations.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NotificationTriggerType(Enum):
    """Represents the different TFE notifications that can be sent as a run's progress transitions between different states."""

    # Run triggers
    CREATED = "run:created"
    PLANNING = "run:planning"
    NEEDS_ATTENTION = "run:needs_attention"
    APPLYING = "run:applying"
    COMPLETED = "run:completed"
    ERRORED = "run:errored"

    # Assessment triggers
    ASSESSMENT_DRIFTED = "assessment:drifted"
    ASSESSMENT_FAILED = "assessment:failed"
    ASSESSMENT_CHECK_FAILED = "assessment:check_failure"

    # Workspace triggers
    WORKSPACE_AUTO_DESTROY_REMINDER = "workspace:auto_destroy_reminder"
    WORKSPACE_AUTO_DESTROY_RUN_RESULTS = "workspace:auto_destroy_run_results"

    # Change request triggers
    CHANGE_REQUEST_CREATED = "change_request:created"


class NotificationDestinationType(Enum):
    """Represents the destination type of the notification configuration."""

    EMAIL = "email"
    GENERIC = "generic"
    SLACK = "slack"
    MICROSOFT_TEAMS = "microsoft-teams"


class DeliveryResponse:
    """Represents a notification configuration delivery response."""

    # Type annotations for instance attributes
    body: str
    code: str
    headers: dict[str, Any]
    sent_at: datetime | None
    successful: str
    url: str

    def __init__(self, data: dict[str, Any]):
        self.body = data.get("body", "")
        self.code = data.get("code", "")
        self.headers = data.get("headers", {})
        self.sent_at = self._parse_datetime(data.get("sent-at"))
        self.successful = data.get("successful", "")
        self.url = data.get("url", "")

    def _parse_datetime(self, date_str: str | None) -> datetime | None:
        """Parse ISO 8601 datetime string."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    def __repr__(self) -> str:
        return f"DeliveryResponse(url='{self.url}', code='{self.code}', successful='{self.successful}')"


class NotificationConfigurationSubscribableChoice:
    """Choice type struct that represents the possible values within a polymorphic relation."""

    # Type annotations for instance attributes
    team: Any | None
    workspace: Any | None

    def __init__(self, team: Any | None = None, workspace: Any | None = None):
        self.team = team
        self.workspace = workspace

    def __repr__(self) -> str:
        if self.team:
            return f"NotificationConfigurationSubscribableChoice(team={self.team})"
        elif self.workspace:
            return f"NotificationConfigurationSubscribableChoice(workspace={self.workspace})"
        return "NotificationConfigurationSubscribableChoice()"


class NotificationConfiguration:
    """Represents a Notification Configuration."""

    # Type annotations for instance attributes
    id: str | None
    created_at: datetime | None
    updated_at: datetime | None
    destination_type: str | None
    enabled: bool
    name: str
    token: str
    url: str
    triggers: list[NotificationTriggerType]
    delivery_responses: list[Any]
    email_addresses: list[str]
    email_users: list[Any]
    subscribable: Any
    subscribable_choice: Any | None

    def __init__(self, data: dict[str, Any]):
        self.id = data.get("id")
        self.created_at = self._parse_datetime(data.get("created-at"))
        self.updated_at = self._parse_datetime(data.get("updated-at"))

        # Core attributes
        self.destination_type = data.get("destination-type")
        self.enabled = data.get("enabled", False)
        self.name = data.get("name", "")
        self.token = data.get("token", "")
        self.url = data.get("url", "")

        # Triggers - convert from strings to enum values
        self.triggers = self._parse_triggers(data.get("triggers", []))

        # Delivery responses
        delivery_responses_data = data.get("delivery-responses", [])
        self.delivery_responses = [
            DeliveryResponse(dr) for dr in delivery_responses_data
        ]

        # Email configuration
        self.email_addresses = data.get("email-addresses", [])
        self.email_users = data.get("email-users", [])

        # Relationships - using polymorphic relation pattern
        self.subscribable = data.get(
            "subscribable"
        )  # Deprecated but maintained for compatibility
        self.subscribable_choice = self._parse_subscribable_choice(
            data.get("subscribable-choice")
        )

    def _parse_datetime(self, date_str: str | None) -> datetime | None:
        """Parse ISO 8601 datetime string."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    def _parse_triggers(self, triggers: list[str]) -> list[NotificationTriggerType]:
        """Parse trigger strings to enum values."""
        parsed_triggers = []
        for trigger in triggers:
            try:
                parsed_triggers.append(NotificationTriggerType(trigger))
            except ValueError:
                # If trigger is not in enum, keep as string for backwards compatibility
                pass
        return parsed_triggers

    def _parse_subscribable_choice(
        self, choice_data: dict[str, Any] | None
    ) -> NotificationConfigurationSubscribableChoice | None:
        """Parse subscribable choice data."""
        if not choice_data:
            return None

        team = choice_data.get("team")
        workspace = choice_data.get("workspace")
        return NotificationConfigurationSubscribableChoice(
            team=team, workspace=workspace
        )

    def __repr__(self) -> str:
        return f"NotificationConfiguration(id='{self.id}', name='{self.name}', enabled={self.enabled})"


def _serialize_triggers(
    triggers: list[NotificationTriggerType | str],
) -> list[str]:
    """Serialize trigger enums or raw strings to their wire value."""
    return [t.value if isinstance(t, NotificationTriggerType) else t for t in triggers]


def _validate_triggers(
    triggers: list[NotificationTriggerType | str],
) -> list[str]:
    """Collect errors for any non-enum, non-known-string trigger entries."""
    errors: list[str] = []
    for trigger in triggers:
        if isinstance(trigger, NotificationTriggerType):
            continue
        try:
            NotificationTriggerType(trigger)
        except ValueError:
            errors.append(f"Invalid trigger type: {trigger}")
    return errors


class NotificationConfigurationListOptions(BaseModel):
    """Represents the options for listing notification configurations."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    page_size: int | None = Field(default=None, alias="page[size]")
    subscribable_choice: NotificationConfigurationSubscribableChoice | None = Field(
        default=None, exclude=True
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        return self.model_dump(by_alias=True, exclude_none=True)


class NotificationConfigurationCreateOptions(BaseModel):
    """Represents the options for creating a new notification configuration."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    destination_type: NotificationDestinationType
    enabled: bool
    name: str
    token: str | None = None
    triggers: list[NotificationTriggerType | str] = Field(default_factory=list)
    url: str | None = None
    email_addresses: list[str] = Field(default_factory=list)
    email_users: list[Any] = Field(default_factory=list)
    subscribable_choice: NotificationConfigurationSubscribableChoice | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        data: dict[str, Any] = {
            "type": "notification-configurations",
            "attributes": {
                "destination-type": self.destination_type.value,
                "enabled": self.enabled,
                "name": self.name,
            },
        }

        if self.token is not None:
            data["attributes"]["token"] = self.token

        if self.triggers:
            data["attributes"]["triggers"] = _serialize_triggers(self.triggers)

        if self.url is not None:
            data["attributes"]["url"] = self.url

        if self.email_addresses:
            data["attributes"]["email-addresses"] = self.email_addresses

        if self.email_users:
            data["relationships"] = {
                "users": {
                    "data": [
                        {
                            "type": "users",
                            "id": user.id if hasattr(user, "id") else str(user),
                        }
                        for user in self.email_users
                    ]
                }
            }

        return data

    def validate(self) -> list[str]:  # type: ignore[override]
        """Validate the create options and return any errors."""
        errors: list[str] = []

        if not self.name or not self.name.strip():
            errors.append("Name is required")

        if self.destination_type in (
            NotificationDestinationType.GENERIC,
            NotificationDestinationType.SLACK,
            NotificationDestinationType.MICROSOFT_TEAMS,
        ):
            if not self.url:
                errors.append("URL is required for this destination type")

        errors.extend(_validate_triggers(self.triggers))

        return errors


class NotificationConfigurationUpdateOptions(BaseModel):
    """Represents the options for updating an existing notification configuration."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    enabled: bool | None = None
    name: str | None = None
    token: str | None = None
    triggers: list[NotificationTriggerType | str] | None = None
    url: str | None = None
    email_addresses: list[str] | None = None
    email_users: list[Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API requests."""
        data: dict[str, Any] = {"type": "notification-configurations", "attributes": {}}

        if self.enabled is not None:
            data["attributes"]["enabled"] = self.enabled

        if self.name is not None:
            data["attributes"]["name"] = self.name

        if self.token is not None:
            data["attributes"]["token"] = self.token

        if self.triggers is not None:
            data["attributes"]["triggers"] = _serialize_triggers(self.triggers)

        if self.url is not None:
            data["attributes"]["url"] = self.url

        if self.email_addresses is not None:
            data["attributes"]["email-addresses"] = self.email_addresses

        if self.email_users is not None:
            data["relationships"] = {
                "users": {
                    "data": [
                        {
                            "type": "users",
                            "id": user.id if hasattr(user, "id") else str(user),
                        }
                        for user in self.email_users
                    ]
                }
            }

        return data

    def validate(self) -> list[str]:  # type: ignore[override]
        """Validate the update options and return any errors."""
        errors: list[str] = []

        if self.name is not None and (not self.name or not self.name.strip()):
            errors.append("Name cannot be empty")

        if self.triggers is not None:
            errors.extend(_validate_triggers(self.triggers))

        return errors


class NotificationConfigurationList:
    """Represents a list of notification configurations with pagination."""

    # Type annotations for instance attributes
    items: list[NotificationConfiguration]
    current_page: int
    page_size: int
    prev_page: int | None
    next_page: int | None
    total_pages: int
    total_count: int

    def __init__(self, data: dict[str, Any]):
        self.items = [
            NotificationConfiguration(item.get("attributes", {}))
            for item in data.get("data", [])
        ]

        # Pagination metadata
        meta = data.get("meta", {})
        pagination = meta.get("pagination", {})

        self.current_page = pagination.get("current-page", 0)
        self.page_size = pagination.get("page-size", 20)
        self.prev_page = pagination.get("prev-page")
        self.next_page = pagination.get("next-page")
        self.total_pages = pagination.get("total-pages", 0)
        self.total_count = pagination.get("total-count", 0)

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Any:
        return iter(self.items)

    def __getitem__(self, index: int) -> NotificationConfiguration:
        return self.items[index]

    def __repr__(self) -> str:
        return f"NotificationConfigurationList(count={len(self.items)}, page={self.current_page}, total={self.total_count})"
