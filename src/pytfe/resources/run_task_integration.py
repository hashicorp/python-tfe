# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from ..errors import InvalidAccessTokenError, InvalidCallbackURLError
from ..models.run_task_integration import TaskResultCallbackRequestOptions
from ._base import _Service


class RunTaskIntegrations(_Service):
    """Run Tasks Integration Callback API.

    See:
    https://developer.hashicorp.com/terraform/enterprise/api-docs/run-tasks/run-tasks-integration
    """

    def callback(
        self,
        callback_url: str,
        access_token: str,
        options: TaskResultCallbackRequestOptions,
    ) -> None:
        """Send a Run Task result back to the Terraform callback URL.

        The PATCH request must use the access token from the originating
        Run Task webhook (not the SDK client's API token).
        """
        if not callback_url or not callback_url.strip():
            raise InvalidCallbackURLError()
        if not access_token or not access_token.strip():
            raise InvalidAccessTokenError()

        self.t.request(
            "PATCH",
            callback_url,
            json_body=options.to_payload(),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/vnd.api+json",
            },
        )
