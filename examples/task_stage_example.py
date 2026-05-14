"""
Example usage of TaskStages API

Demonstrates:
- Read a task stage
- List task stages for a run
- Override a task stage
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pytfe import TFEClient, TFEConfig


def main():
    client = TFEClient(TFEConfig.from_env())

    # Read from environment variables (NO hardcoding)
    task_stage_id = os.getenv("TFE_TASK_STAGE_ID")
    run_id = os.getenv("TFE_RUN_ID")

    if not task_stage_id or not run_id:
        print("Please set TFE_TASK_STAGE_ID and TFE_RUN_ID")
        return

    print("=== TaskStages Example ===")

    # READ
    print("\nReading task stage...")
    try:
        stage = client.task_stages.read(task_stage_id)
        print(f"ID: {stage.id}, Status: {stage.status}")
    except Exception as e:
        print(f"Read failed: {e}")

    # LIST
    print("\nListing task stages...")
    try:
        stages = list(client.task_stages.list(run_id))
        for s in stages:
            print(f"{s.id} - {s.status}")
    except Exception as e:
        print(f"List failed: {e}")

    # OVERRIDE
    print("\nOverriding task stage...")
    try:
        client.task_stages.override(task_stage_id, comment="Approved")
        print("Override successful")
    except Exception as e:
        print(f"Override failed: {e}")


if __name__ == "__main__":
    main()
