# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""
Notification Configuration Models

This module provides models for working with Terraform Cloud/Enterprise notification configurations.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ._base import TFEModel


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


class DeliveryResponse(BaseModel):
    """Represents a notification configuration delivery response."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    body: str | None = None
    code: str | None = None
    headers: dict[str, Any] | None = Field(default_factory=dict)
    sent_at: datetime | None = Field(default=None, alias="sent-at")
    successful: str | None = None
    url: str | None = None

    def __init__(self, data: dict[str, Any] | None = None, /, **kwargs: Any) -> None:
        if data is not None:
            super().__init__(**{**data, **kwargs})
        else:
            super().__init__(**kwargs)


class NotificationConfigurationSubscribableChoice(BaseModel):
    """Choice type struct that represents the possible values within a polymorphic relation."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    team: Any | None = None
    workspace: Any | None = None


class NotificationConfiguration(TFEModel):
    """Represents a Notification Configuration."""

    model_config = ConfigDict(
        populate_by_name=True, arbitrary_types_allowed=True, extra="allow"
    )

    id: str | None = None
    created_at: datetime | None = Field(default=None, alias="created-at")
    updated_at: datetime | None = Field(default=None, alias="updated-at")
    destination_type: str | None = Field(default=None, alias="destination-type")
    enabled: bool = False
    name: str | None = None
    token: str | None = None
    url: str | None = None
    triggers: list[NotificationTriggerType] = Field(default_factory=list)
    delivery_responses: list[DeliveryResponse] = Field(
        default_factory=list, alias="delivery-responses"
    )
    email_addresses: list[str] = Field(default_factory=list, alias="email-addresses")
    email_users: list[Any] = Field(default_factory=list, alias="email-users")
    subscribable: Any = None
    subscribable_choice: NotificationConfigurationSubscribableChoice | None = Field(
        default=None, alias="subscribable-choice"
    )

    @field_validator(
        "delivery_responses",
        "email_addresses",
        "email_users",
        mode="before",
    )
    @classmethod
    def _none_to_empty_list(cls, value: Any) -> Any:
        return [] if value is None else value

    @field_validator("triggers", mode="before")
    @classmethod
    def _coerce_triggers(cls, value: Any) -> list[NotificationTriggerType]:
        if not value:
            return []
        parsed: list[NotificationTriggerType] = []
        for trigger in value:
            if isinstance(trigger, NotificationTriggerType):
                parsed.append(trigger)
                continue
            try:
                parsed.append(NotificationTriggerType(trigger))
            except (ValueError, TypeError):
                # Silently drop unknown triggers for backwards compatibility
                pass
        return parsed

    def __init__(self, data: dict[str, Any] | None = None, /, **kwargs: Any) -> None:
        if data is not None:
            super().__init__(**{**data, **kwargs})
        else:
            super().__init__(**kwargs)


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


class NotificationConfigurationList(BaseModel):
    """Represents a list of notification configurations with pagination."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    items: list[NotificationConfiguration] = Field(default_factory=list)
    current_page: int = 0
    page_size: int = 20
    prev_page: int | None = None
    next_page: int | None = None
    total_pages: int = 0
    total_count: int = 0

    def __init__(self, data: dict[str, Any] | None = None, /, **kwargs: Any) -> None:
        if data is None:
            super().__init__(**kwargs)
            return

        items_data = [item.get("attributes", {}) for item in data.get("data") or []]
        pagination = (data.get("meta") or {}).get("pagination") or {}
        parsed: dict[str, Any] = {
            "items": items_data,
            "current_page": pagination.get("current-page", 0),
            "page_size": pagination.get("page-size", 20),
            "prev_page": pagination.get("prev-page"),
            "next_page": pagination.get("next-page"),
            "total_pages": pagination.get("total-pages", 0),
            "total_count": pagination.get("total-count", 0),
        }
        parsed.update(kwargs)
        super().__init__(**parsed)

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Iterator[NotificationConfiguration]:  # type: ignore[override]
        return iter(self.items)

    def __getitem__(self, index: int) -> NotificationConfiguration:
        return self.items[index]
