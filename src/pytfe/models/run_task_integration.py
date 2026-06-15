# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..errors import InvalidTaskResultsCallbackStatusError


class TaskResultCallbackStatus(str, Enum):
    """Statuses accepted by the Run Task callback endpoint."""

    passed = "passed"
    failed = "failed"
    running = "running"


class TaskResultTag(BaseModel):
    """Tag attached to a Run Task outcome to enrich the result display in the UI."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    label: str = Field(..., alias="label")
    level: str | None = Field(None, alias="level")

    def _to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"label": self.label}
        if self.level is not None:
            payload["level"] = self.level
        return payload


class TaskResultOutcome(BaseModel):
    """Detailed Run Task outcome."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    outcome_id: str | None = Field(None, alias="outcome-id")
    description: str | None = Field(None, alias="description")
    body: str | None = Field(None, alias="body")
    url: str | None = Field(None, alias="url")
    tags: dict[str, list[TaskResultTag]] | None = Field(None, alias="tags")

    def _to_payload(self) -> dict[str, Any]:
        attributes: dict[str, Any] = {}
        if self.outcome_id is not None:
            attributes["outcome-id"] = self.outcome_id
        if self.description is not None:
            attributes["description"] = self.description
        if self.body is not None:
            attributes["body"] = self.body
        if self.url is not None:
            attributes["url"] = self.url
        if self.tags is not None:
            attributes["tags"] = {
                key: [tag._to_payload() for tag in tags]
                for key, tags in self.tags.items()
            }
        return {"type": "task-result-outcomes", "attributes": attributes}


class TaskResultCallbackRequestOptions(BaseModel):
    """Payload options for sending a Run Task callback result."""

    model_config = ConfigDict(populate_by_name=True)

    status: TaskResultCallbackStatus = Field(..., alias="status")
    message: str | None = Field(None, alias="message")
    url: str | None = Field(None, alias="url")
    outcomes: list[TaskResultOutcome] | None = Field(None, alias="outcomes")

    def _validate(self) -> None:
        """Validate callback status."""
        if not isinstance(self.status, TaskResultCallbackStatus):
            raise InvalidTaskResultsCallbackStatusError()

    def to_payload(self) -> dict[str, Any]:
        """Return the JSON:API payload for the callback PATCH request."""
        self._validate()

        attributes: dict[str, Any] = {"status": self.status.value}
        if self.message is not None:
            attributes["message"] = self.message
        if self.url is not None:
            attributes["url"] = self.url

        payload: dict[str, Any] = {
            "data": {
                "type": "task-results",
                "attributes": attributes,
            }
        }

        if self.outcomes:
            payload["data"]["relationships"] = {
                "outcomes": {
                    "data": [outcome._to_payload() for outcome in self.outcomes]
                }
            }

        return payload
