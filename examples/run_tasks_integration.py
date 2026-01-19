"""
Terraform Cloud/Enterprise Run Tasks Integration Example

This example demonstrates how to use the python-tfe SDK to build a run task server
that receives task requests from TFC/TFE and sends results back via the callback API.

IMPORTANT: This example uses Flask as a simple HTTP server for demonstration purposes.
You can use any web framework (FastAPI, Django, etc.) or even the built-in http.server.
The key components are:
1. Receiving POST requests with run task payloads
2. Using TFEClient.run_tasks_integration.callback() to send results back

Prerequisites:
    - Install Flask (for this example only): pip install flask
    - Expose your server publicly using ngrok, cloudflare tunnel, or similar
    - Create a run task in TFC/TFE pointing to your public URL endpoint
    - Attach the run task to a workspace

Usage:
    python examples/run_tasks_integration.py

Then expose with ngrok:
    ngrok http 5000

API Documentation:
    https://developer.hashicorp.com/terraform/enterprise/api-docs/run-tasks/run-tasks-integration
"""

from __future__ import annotations

import os

try:
    from flask import Flask, request, jsonify
except ImportError:
    print("Error: Flask is required for this example")
    print("Install it with: pip install flask")
    exit(1)

from pytfe import TFEClient, TFEConfig
from pytfe.models import RunTaskRequest, RunTaskRequestCapabilities
from pytfe.resources.run_tasks_integration import (
    RunTasksIntegration,
    TaskResultCallbackOptions,
    TaskResultOutcome,
    TaskResultStatus,
    TaskResultTag,
)

app = Flask(__name__)

# Initialize TFE client for callback functionality
# Note: The callback uses the access_token from the run task request,
# NOT your regular TFE API token
config = TFEConfig()
client = TFEClient(config)


@app.route('/run-task', methods=['POST'])
def handle_run_task():
    """Handle incoming run task request from TFC/TFE."""
    try:
        # Parse the incoming request
        run_task_request = RunTaskRequest(**request.json)
        
        print(f"Received run task request:")
        print(f"  Organization: {run_task_request.organization_name}")
        print(f"  Workspace: {run_task_request.workspace_name}")
        print(f"  Run ID: {run_task_request.run_id}")
        print(f"  Stage: {run_task_request.stage}")
        print(f"  Enforcement Level: {run_task_request.task_result_enforcement_level}")
        
        # Extract the callback information
        callback_url = run_task_request.task_result_callback_url
        access_token = run_task_request.access_token
        
        # YOUR CUSTOM LOGIC HERE
        # This is where you would perform your actual run task checks
        # For example:
        # - Download and analyze the plan JSON
        # - Check for policy violations
        # - Validate resource configurations
        # - Run security scans
        # - Check cost estimates
        
        # Example: Simple check based on workspace name
        if "prod" in run_task_request.workspace_name.lower():
            # Production workspace - run strict checks
            result = perform_strict_checks(run_task_request)
        else:
            # Non-production - run basic checks
            result = perform_basic_checks(run_task_request)
        
        # Send the callback to TFC/TFE
        callback_options = TaskResultCallbackOptions(
            status=result["status"],
            message=result["message"],
            url=result.get("url"),
            outcomes=result.get("outcomes", []),
        )
        
        client.run_tasks_integration.callback(
            callback_url=callback_url,
            access_token=access_token,
            options=callback_options,
        )
        
        print(f"Successfully sent callback with status: {result['status']}")
        
        # Return 200 OK to TFC/TFE
        return jsonify({"status": "accepted"}), 200
        
    except Exception as e:
        print(f"Error processing run task: {e}")
        
        # Even if processing fails, try to send a failure callback
        try:
            if 'callback_url' in locals() and 'access_token' in locals():
                error_options = TaskResultCallbackOptions(
                    status=TaskResultStatus.FAILED,
                    message=f"Run task processing error: {str(e)}",
                )
                client.run_tasks_integration.callback(
                    callback_url=callback_url,
                    access_token=access_token,
                    options=error_options,
                )
        except Exception as callback_error:
            print(f"Failed to send error callback: {callback_error}")
        
        return jsonify({"error": str(e)}), 500


def perform_strict_checks(run_task_request: RunTaskRequest) -> dict:
    """Perform strict checks for production workspaces.
    
    This is a placeholder for your actual check logic.
    """
    # Example: Always pass for demo purposes
    # In real implementation, you would:
    # - Download the configuration or plan
    # - Analyze it for compliance/security
    # - Generate detailed outcomes
    
    outcomes = [
        TaskResultOutcome(
            outcome_id="SECURITY-001",
            description="Security check passed",
            body="All security requirements met for production deployment.",
            tags={
                "Category": [TaskResultTag(label="Security")],
                "Severity": [TaskResultTag(label="Info", level="info")],
            },
        ),
        TaskResultOutcome(
            outcome_id="COMPLIANCE-001",
            description="Compliance check passed",
            body="Configuration meets all compliance requirements.",
            tags={
                "Category": [TaskResultTag(label="Compliance")],
                "Severity": [TaskResultTag(label="Info", level="info")],
            },
        ),
    ]
    
    return {
        "status": TaskResultStatus.PASSED,
        "message": "All production checks passed",
        "url": "https://your-dashboard.example.com/results/123",
        "outcomes": outcomes,
    }


def perform_basic_checks(run_task_request: RunTaskRequest) -> dict:
    """Perform basic checks for non-production workspaces.
    
    This is a placeholder for your actual check logic.
    """
    # Example: Simple validation
    outcomes = [
        TaskResultOutcome(
            outcome_id="BASIC-001",
            description="Basic validation passed",
            body="Configuration syntax is valid.",
            tags={
                "Category": [TaskResultTag(label="Validation")],
            },
        ),
    ]
    
    return {
        "status": TaskResultStatus.PASSED,
        "message": "Basic checks completed successfully",
        "outcomes": outcomes,
    }


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


if __name__ == '__main__':
    print("Starting Run Task server on http://localhost:5000")
    print("Make sure to expose this with ngrok or similar for TFC/TFE to reach it")
    print("Example: ngrok http 5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
