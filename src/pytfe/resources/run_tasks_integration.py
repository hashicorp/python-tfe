"""Run Tasks Integration resource for python-tfe.

This module provides the callback functionality for external run task servers
to send results back to Terraform Cloud/Enterprise.
"""

from __future__ import annotations

from typing import Any

from ..errors import TFEError
from ._base import _Service


class TaskResultStatus:
    """Task result status enum."""
    
    PASSED = "passed"
    FAILED = "failed"
    RUNNING = "running"


class TaskResultTag:
    """Tag to enrich outcomes display in TFC/TFE."""
    
    def __init__(self, label: str, level: str | None = None):
        self.label = label
        self.level = level
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {"label": self.label}
        if self.level:
            result["level"] = self.level
        return result


class TaskResultOutcome:
    """Detailed run task outcome for improved visibility in TFC/TFE UI.
    
    API Documentation:
        https://developer.hashicorp.com/terraform/enterprise/api-docs/run-tasks/run-tasks-integration#outcomes-payload-body
    """
    
    def __init__(
        self,
        outcome_id: str | None = None,
        description: str | None = None,
        body: str | None = None,
        url: str | None = None,
        tags: dict[str, list[TaskResultTag]] | None = None,
    ):
        self.outcome_id = outcome_id
        self.description = description
        self.body = body
        self.url = url
        self.tags = tags or {}
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {"type": "task-result-outcomes", "attributes": {}}
        
        if self.outcome_id:
            result["attributes"]["outcome-id"] = self.outcome_id
        if self.description:
            result["attributes"]["description"] = self.description
        if self.body:
            result["attributes"]["body"] = self.body
        if self.url:
            result["attributes"]["url"] = self.url
        if self.tags:
            result["attributes"]["tags"] = {
                key: [tag.to_dict() for tag in tags]
                for key, tags in self.tags.items()
            }
        
        return result


class TaskResultCallbackOptions:
    """Options for sending task result callback to TFC/TFE.
    
    API Documentation:
        https://developer.hashicorp.com/terraform/enterprise/api-docs/run-tasks/run-tasks-integration#request-body-1
    """
    
    def __init__(
        self,
        status: str,
        message: str | None = None,
        url: str | None = None,
        outcomes: list[TaskResultOutcome] | None = None,
    ):
        """Initialize callback options.
        
        Args:
            status: Task result status (passed, failed, running)
            message: Optional message about the task result
            url: Optional URL to view detailed results
            outcomes: Optional list of detailed outcomes
        """
        self.status = status
        self.message = message
        self.url = url
        self.outcomes = outcomes or []
    
    def validate(self) -> None:
        """Validate the callback options."""
        valid_statuses = [TaskResultStatus.PASSED, TaskResultStatus.FAILED, TaskResultStatus.RUNNING]
        if self.status not in valid_statuses:
            raise TFEError(
                f"Invalid task result status: {self.status}. "
                f"Must be one of: {', '.join(valid_statuses)}"
            )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON:API format."""
        data: dict[str, Any] = {
            "type": "task-results",
            "attributes": {
                "status": self.status,
            },
        }
        
        if self.message:
            data["attributes"]["message"] = self.message
        if self.url:
            data["attributes"]["url"] = self.url
        
        if self.outcomes:
            data["relationships"] = {
                "outcomes": {
                    "data": [outcome.to_dict() for outcome in self.outcomes]
                }
            }
        
        return {"data": data}


class RunTasksIntegration(_Service):
    """Run Tasks Integration API for sending callbacks to TFC/TFE.
    
    This service is used by external run task servers to send task results
    back to Terraform Cloud/Enterprise.
    
    API Documentation:
        https://developer.hashicorp.com/terraform/enterprise/api-docs/run-tasks/run-tasks-integration
    """
    
    def callback(
        self,
        callback_url: str,
        access_token: str,
        options: TaskResultCallbackOptions,
    ) -> None:
        """Send task result callback to TFC/TFE.
        
        Args:
            callback_url: The callback URL from the run task request
            access_token: The access token from the run task request
            options: Task result callback options
            
        Raises:
            TFEError: If callback_url or access_token is invalid
            TFEError: If options validation fails
        """
        if not callback_url or not callback_url.strip():
            raise TFEError("callback_url cannot be empty")
        
        if not access_token or not access_token.strip():
            raise TFEError("access_token cannot be empty")
        
        options.validate()
        
        # Create custom headers with the access token from the request
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/vnd.api+json",
        }
        
        # Send PATCH request to callback URL
        self.t.request(
            "PATCH",
            callback_url,
            json_body=options.to_dict(),
            headers=headers,
        )
