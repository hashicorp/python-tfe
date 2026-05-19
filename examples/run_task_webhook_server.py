# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Minimal FastAPI webhook server for Terraform Run Tasks.

This example receives a Run Task webhook, extracts the callback URL
and access token from the payload, and sends a callback result back
to Terraform using the SDK.

Setup:

1. Install dependencies:

       pip install fastapi uvicorn

2. Configure environment variables:

       export TFE_ADDRESS=https://app.terraform.io
       export TFE_TOKEN=<your-api-token>

3. Start the server from the repository root:

       uvicorn examples.run_task_webhook_server:app --reload --port 8000

4. Expose the server publicly with ngrok:

       ngrok http 8000

5. In Terraform Cloud / Enterprise:

   - Create a Run Task using the ngrok URL
   - Attach the Run Task to a workspace
   - Trigger a Terraform run

The webhook payload will include values like:

       {
         "task_result_callback_url": "...",
         "access_token": "..."
       }

This example prints the payload locally and sends a successful
callback response back to Terraform.
"""

from __future__ import annotations

import json

from fastapi import FastAPI, Request

from pytfe import TFEClient, TFEConfig
from pytfe.models.run_task_integration import (
    TaskResultCallbackRequestOptions,
    TaskResultStatus,
)

app = FastAPI()
client = TFEClient(TFEConfig.from_env())


@app.post("/")
async def receive_webhook(request: Request) -> dict[str, bool]:
    try:
        payload = await request.json()
    except Exception:
        # Terraform verification requests may not include a JSON payload.
        return {"ok": True}

    print("\n=== FULL PAYLOAD ===")
    print(json.dumps(payload, indent=2))

    callback_url = payload.get("task_result_callback_url")
    access_token = payload.get("access_token")

    print("\n=== EXTRACTED VALUES ===")
    print("callback_url:", callback_url)
    print("access_token:", access_token)

    if not callback_url or not access_token:
        # Verification requests do not include callback information.
        return {"ok": True}

    options = TaskResultCallbackRequestOptions(
        status=TaskResultStatus.passed,
        message="Webhook received and processed",
    )

    print(f"Sending callback to: {callback_url}")

    try:
        client.run_task_integrations.callback(
            callback_url=callback_url,
            access_token=access_token,
            options=options,
        )
        print("Run task callback sent successfully")
    except Exception as exc:
        print(f"Callback failed: {exc!r}")
        return {"ok": False}

    return {"ok": True}
