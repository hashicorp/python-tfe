#!/usr/bin/env python
"""
Run Tasks Integration Example - Real TFC/TFE Testing

This example shows how to create a webhook server that integrates with
Terraform Cloud/Enterprise run tasks to validate runs and send results back.

STEP-BY-STEP TESTING WITH REAL TFC/TFE:

1. START THE SERVER:
   python examples/run_tasks_integration.py --port 8888

2. MAKE IT ACCESSIBLE (choose one):

   Option A - Using ngrok (for local testing):
   - Install: https://ngrok.com/download
   - Run: ngrok http 8888
   - Copy the public URL (e.g., https://abc123.ngrok.io)

   Option B - Deploy to cloud (recommended for production):

   AWS EC2:
   - Launch EC2 instance (t2.micro sufficient for testing)
   - Upload this file: scp run_tasks_integration.py ec2-user@YOUR-IP:~/
   - SSH in: ssh ec2-user@YOUR-IP
   - Install Python 3.11+: sudo dnf install python3.11 python3.11-pip
   - Install dependencies: python3.11 -m pip install --user pytfe
   - Run server: python3.11 run_tasks_integration.py --port 8888
   - Configure security group: Allow port 8888 from 0.0.0.0/0
   - Use public IP: http://YOUR-EC2-IP:8888

   Heroku (easiest):
   - Create Procfile: web: python run_tasks_integration.py --port $PORT
   - Create requirements.txt: pytfe>=0.1.0
   - Deploy: git push heroku main
   - Use Heroku URL: https://your-app.herokuapp.com

   Google Cloud Run:
   - Create Dockerfile: FROM python:3.11 / RUN pip install pytfe / COPY . . / CMD ["python", "run_tasks_integration.py", "--port", "8080"]
   - Deploy: gcloud run deploy --source .
   - Use Cloud Run URL: https://your-service-hash.run.app

   DigitalOcean Droplet:
   - Create Ubuntu droplet
   - Upload file and install Python/pytfe
   - Run with: python3 run_tasks_integration.py --port 8888
   - Use droplet IP: http://YOUR-DROPLET-IP:8888

   Benefits of cloud deployment:
   - Permanent URL (no ngrok reconnections)
   - Better reliability and uptime
   - Can handle production workloads
   - SSL/HTTPS support available
   - Scalable if needed

3. CREATE RUN TASK IN TFC/TFE:
   - Go to: https://app.terraform.io/app/YOUR_ORG/settings/tasks
   - Click "Create run task"
   - Name: "python-tfe-test"
   - URL: Your public URL from step 2
   - Save and wait for verification (check mark)

4. ATTACH TO WORKSPACE:
   - Go to workspace settings → Run Tasks
   - Click "Add run task"
   - Select "python-tfe-test"
   - Enforcement: Advisory (for testing)
   - Stage: Pre-plan
   - Save

5. TRIGGER A RUN:
   - Go to your workspace
   - Click "Actions" → "Start new run"
   - Watch this terminal for webhook activity!
   - Check TFC/TFE UI for run task results

CUSTOMIZE VALIDATION LOGIC:
Edit the section around line 80 to add your custom checks:
- Cost validation
- Security scanning (Checkov, tfsec)
- Policy enforcement
- Custom approval workflows

API Documentation:
    https://developer.hashicorp.com/terraform/enterprise/api-docs/run-tasks/run-tasks-integration
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from pytfe import TFEClient
from pytfe.models import RunTaskRequest
from pytfe.models import (
    TaskResultCallbackOptions,
    TaskResultOutcome,
    TaskResultTag,
)


class RunTaskHandler(BaseHTTPRequestHandler):
    """HTTP handler for run task callbacks from TFC/TFE."""

    def do_POST(self):
        """Handle POST request from TFC/TFE run task webhook."""
        # Read the request body
        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length)

        try:
            # Parse the incoming run task request
            payload = json.loads(body)
            print("\n" + "=" * 60)
            print("Received Run Task Request")
            print("=" * 60)

            # Parse into RunTaskRequest model
            request = RunTaskRequest.model_validate(payload)

            print(f"Run ID: {request.run_id}")
            print(f"Organization: {request.organization_name}")
            print(f"Workspace: {request.workspace_name}")
            print(f"Workspace ID: {request.workspace_id}")
            print(f"Stage: {request.stage}")
            print(f"Callback URL: {request.task_result_callback_url}")
            print(f"Is Speculative: {request.is_speculative}")

            # Handle verification requests (test webhooks from TFC/TFE)
            if (
                request.organization_name == "test-org"
                or request.workspace_name == "test-workspace"
            ):
                print("\n[OK] Verification request detected - responding with 200 OK")
                print("=" * 60 + "\n")
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode())
                return

            # ===============================================================
            # CUSTOMIZE YOUR VALIDATION LOGIC HERE
            # ===============================================================
            # This is where you add your custom checks and validation.
            # Examples:
            #
            # 1. Cost Control:
            #    if estimated_cost > 1000:
            #        result_status = "failed"
            #        result_message = f"Cost ${estimated_cost} exceeds limit"
            #
            # 2. Security Scanning:
            #    scan_results = run_checkov(request.configuration_version_download_url)
            #    if scan_results.failed:
            #        result_status = "failed"
            #        result_message = "Security scan failed"
            #
            # 3. Policy Enforcement:
            #    if not workspace_has_required_tags(request.workspace_name):
            #        result_status = "failed"
            #        result_message = "Workspace missing required tags"
            #
            # 4. Custom Approval:
            #    if request.workspace_name.startswith("prod-"):
            #        result_status = "failed"
            #        result_message = "Production changes require manual approval"

            # For this example, we'll just pass the task
            result_status = "passed"
            result_message = "All checks passed successfully"

            # Create detailed outcomes (optional but recommended)
            outcomes = [
                TaskResultOutcome(
                    outcome_id="check-1",
                    description="Configuration validation passed",
                    body="All Terraform configurations are valid and follow best practices.",
                    url="https://example.com/results/check-1",
                    tags={
                        "Status": [TaskResultTag(label="Passed", level="info")],
                        "Category": [TaskResultTag(label="Validation")],
                    },
                )
            ]

            # Create callback options
            callback_options = TaskResultCallbackOptions(
                status=result_status,
                message=result_message,
                url="https://example.com/full-results",
                outcomes=outcomes,
            )

            # Initialize client and send callback
            print("\nInitializing TFEClient...")
            print(f"Access token from webhook: {request.access_token[:10]}***")
            client = TFEClient()
            print("Client initialized successfully")

            print(f"Sending callback to: {request.task_result_callback_url[:50]}...")
            client.run_tasks_integration.callback(
                callback_url=request.task_result_callback_url,
                access_token=request.access_token,
                options=callback_options,
            )

            print(f"\n[SUCCESS] Callback sent successfully: {result_status}")
            print("=" * 60 + "\n")

            # Respond to TFC/TFE
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "received"}).encode())

        except Exception as e:
            print(f"Error processing request: {e}")
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_message(self, format, *args):
        """Suppress default HTTP logging."""
        pass


def run_server(port=8080):
    """Start the run task callback server."""
    server_address = ("", port)
    httpd = HTTPServer(server_address, RunTaskHandler)

    print("=" * 60)
    print("Run Tasks Integration Callback Server")
    print("=" * 60)
    print(f"Listening on http://localhost:{port}")
    print("\nFor local testing:")
    print("  1. Use ngrok or similar tool to expose this server:")
    print(f"     ngrok http {port}")
    print("  2. Configure your run task in TFC/TFE with the ngrok URL")
    print("  3. Trigger a run in your workspace")
    print("\nWaiting for requests from TFC/TFE...")
    print("=" * 60 + "\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        httpd.shutdown()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run Tasks Integration callback server"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080)",
    )
    args = parser.parse_args()

    run_server(port=args.port)
