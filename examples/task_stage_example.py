"""
Example usage of TaskStages API

This demonstrates how to:
- Read a task stage
- List task stages for a run
- Override a task stage
"""

from pytfe.client import TFEClient

# Initialize client (make sure your auth/env is configured)
client = TFEClient()

# ---------------------------
# Read a task stage
# ---------------------------
# Fetch a single task stage by ID
# Replace "ts-123" with a real task stage ID
stage = client.task_stages.read("ts-abc123xyz")
print(stage)


# ---------------------------
# List task stages for a run
# ---------------------------
# Fetch all task stages for a run
# Replace "run-123" with a real run ID
# for stage in client.task_stages.list("run-123"):
#     print(stage)


# ---------------------------
# Override a task stage
# ---------------------------
# Override a task stage (if allowed)
# Replace "ts-123" with a real task stage ID
# client.task_stages.override("ts-123", comment="Approved")