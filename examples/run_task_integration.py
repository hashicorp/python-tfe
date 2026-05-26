# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Example Run Task callback integration.

This example sends a callback result back to Terraform after a Run Task
webhook is received.

Required environment variables:

- TFE_ADDRESS
    Terraform address (for example: https://app.terraform.io)

- TFE_TOKEN
    Your Terraform API token used to initialize the SDK client.

- TFE_CALLBACK_URL
    The task_result_callback_url received in the Run Task webhook payload.

- TFE_CALLBACK_TOKEN
    The access_token received in the same webhook payload.
    This token is used for the callback request and is different from
    your regular Terraform API token.

Local testing flow:

1. Start the webhook server:

       uvicorn examples.run_task_webhook_server:app --reload --port 8000

2. Expose the server publicly:

       ngrok http 8000

3. Create a Run Task in Terraform Cloud / Enterprise using the ngrok URL.

4. Attach the Run Task to a workspace and trigger a run.

5. The webhook payload will include values similar to:

       {
         "task_result_callback_url": "https://app.terraform.io/...",
         "access_token": "v1.xxxxx..."
       }

6. Export those values locally and run this example script,
   or call client.run_task_integrations.callback(...) directly
   inside your webhook handler.

Example:

    export TFE_ADDRESS=https://app.terraform.io
    export TFE_TOKEN=<your-api-token>
    export TFE_CALLBACK_URL=<from-webhook-payload>
    export TFE_CALLBACK_TOKEN=<from-webhook-payload>

    python examples/run_task_integration.py
"""

from __future__ import annotations

import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    TaskResultCallbackRequestOptions,
    TaskResultCallbackStatus,
    TaskResultOutcome,
    TaskResultTag,
)


def main() -> None:
    callback_url = os.getenv("TFE_CALLBACK_URL")
    access_token = os.getenv("TFE_CALLBACK_TOKEN")

    if not callback_url or not access_token:
        print("Missing TFE_CALLBACK_URL or TFE_CALLBACK_TOKEN")
        return

    # TFE_ADDRESS and TFE_TOKEN are loaded from the environment.
    # The callback request itself uses the short-lived webhook token.
    client = TFEClient(TFEConfig.from_env())

    outcome = TaskResultOutcome(
        description="Example outcome",
        body="All checks passed successfully",
        tags={"severity": [TaskResultTag(label="low", level="info")]},
    )

    # Example status values:
    #
    # - passed: marks the run task as successful
    # - failed: fails the run task
    # - running: reports progress before sending a final result
    #
    # Example: send an in-progress update
    #
    # options = TaskResultCallbackRequestOptions(
    #     status=TaskResultStatus.running,
    #     message="Security scan in progress",
    # )
    #
    # Example: report a failure
    #
    # options = TaskResultCallbackRequestOptions(
    #     status=TaskResultStatus.failed,
    #     message="Found critical vulnerabilities",
    # )

    options = TaskResultCallbackRequestOptions(
        status=TaskResultCallbackStatus.passed,
        message="Run task completed successfully",
        url="https://example.com/results",
        outcomes=[outcome],
    )

    print(f"Sending callback to: {callback_url}")

    client.run_task_integrations.callback(
        callback_url=callback_url,
        access_token=access_token,
        options=options,
    )

    print("Run task callback sent successfully")


if __name__ == "__main__":
    main()
