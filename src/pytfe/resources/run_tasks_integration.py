"""Run Tasks Integration resource for python-tfe.

This module provides the callback functionality for external run task servers
to send results back to Terraform Cloud/Enterprise.
"""

from __future__ import annotations

from typing import Any

from ..errors import TFEError
from ..models.task_result import TaskResultStatus
from ..models.run_tasks_integration import (
    TaskResultTag,
    TaskResultOutcome,
    TaskResultCallbackOptions,
)
from ._base import _Service


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
