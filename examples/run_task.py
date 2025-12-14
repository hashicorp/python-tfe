"""
Terraform Cloud/Enterprise Run Task Management Example

This example demonstrates comprehensive run task operations using the python-tfe SDK.
It provides a command-line interface for managing TFE run tasks with various operations
including create, read, update, delete, and advanced listing capabilities.

Prerequisites:
    - Set TFE_TOKEN environment variable with your Terraform Cloud API token
    - Ensure you have access to the target organization

Basic Usage:
    python examples/run_task.py --help

Core Operations:

1. List Run Tasks (default operation):
    python examples/run_task.py --org my-org
    python examples/run_task.py --org my-org --page-size 20
    python examples/run_task.py --org my-org --page 2 --page-size 10

2. Create New Run Task:
    python examples/run_task.py --org my-org --create

3. Read Run Task Details:
    python examples/run_task.py --org my-org --task-id "rt-abc123xyz"
    python examples/run_task.py --org my-org --task-id "rt-abc123xyz" --include-workspace-tasks

4. Update Run Task Settings:
    python examples/run_task.py --org my-org --task-id "rt-abc123xyz" --update

5. Delete Run Task:
    python examples/run_task.py --org my-org --task-id "rt-abc123xyz" --delete
"""

from __future__ import annotations

import argparse
import os
import time
from datetime import datetime

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    RunTaskCreateOptions,
    RunTaskIncludeOptions,
    RunTaskListOptions,
    RunTaskReadOptions,
    RunTaskUpdateOptions,
)


def _print_header(title: str) -> None:
    """Print a formatted header for operations."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Run Task demo for python-tfe SDK")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--org", required=True, help="Organization name")
    parser.add_argument(
        "--task-id", help="Run Task ID for read/update/delete operations"
    )
    parser.add_argument("--create", action="store_true", help="Create a new run task")
    parser.add_argument(
        "--update", action="store_true", help="Update run task settings"
    )
    parser.add_argument("--delete", action="store_true", help="Delete the run task")
    parser.add_argument(
        "--include-workspace-tasks",
        action="store_true",
        help="Include workspace task relationships in read operations",
    )
    parser.add_argument("--page", type=int, default=1, help="Page number for listing")
    parser.add_argument(
        "--page-size", type=int, default=10, help="Page size for listing"
    )
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # 1) List run tasks in the organization
    _print_header("Listing run tasks")
    try:
        # Create options for listing run tasks with pagination
        options = RunTaskListOptions(
            page_number=args.page,
            page_size=args.page_size,
            include=[
                RunTaskIncludeOptions.RUN_TASK_WORKSPACE_TASKS,
                RunTaskIncludeOptions.RUN_TASK_WORKSPACE,
            ],
        )

        print(
            f"Fetching run tasks from organization '{args.org}' (page {args.page}, size {args.page_size})..."
        )
        # Get run tasks and convert to list safely
        run_task_gen = client.run_tasks.list(args.org, options)
        run_task_list = []
        count = 0
        for task in run_task_gen:
            run_task_list.append(task)
            count += 1
            if count >= args.page_size * 2:  # Safety limit based on page size
                break

        print(f"Found {len(run_task_list)} run tasks")
        print()

        if not run_task_list:
            print("No run tasks found in this organization.")
        else:
            for i, task in enumerate(run_task_list, 1):
                print(f"{i:2d}. {task.name}")
                print(f"ID: {task.id}")
                print(f"URL: {task.url}")
                print(f"Category: {task.category}")
                print(f"Enabled: {task.enabled}")
                if task.description:
                    print(f"Description: {task.description}")
                print()
    except Exception as e:
        print(f"Error listing run tasks: {e}")
        return

    # 2) Create a new run task if requested
    if args.create:
        _print_header("Creating a new run task")
        try:
            timestamp = int(time.time())
            task_name = f"demo-run-task-{timestamp}"

            create_options = RunTaskCreateOptions(
                name=task_name,
                url="https://httpbin.org/post",
                category="task",
                description=f"Demo run task created at {datetime.now()}",
                enabled=True,
                hmac_key=f"demo-secret-key-{timestamp}",
            )

            print(f"Creating run task '{task_name}' in organization '{args.org}'...")
            run_task = client.run_tasks.create(args.org, create_options)
            print("Successfully created run task!")
            print(f"Name: {run_task.name}")
            print(f"ID: {run_task.id}")
            print(f"URL: {run_task.url}")
            print(f"Category: {run_task.category}")
            print(f"Enabled: {run_task.enabled}")
            print(f"Description: {run_task.description}")
            print(f"HMAC Key: {'[CONFIGURED]' if run_task.hmac_key else 'None'}")
            print()

            args.task_id = run_task.id  # Use the created task for other operations
        except Exception as e:
            print(f"Error creating run task: {e}")
            return

    # 3) Read run task details if task ID is provided
    if args.task_id:
        _print_header(f"Reading run task: {args.task_id}")
        try:
            if args.include_workspace_tasks:
                read_options = RunTaskReadOptions(
                    include=[RunTaskIncludeOptions.RUN_TASK_WORKSPACE_TASKS]
                )
                run_task = client.run_tasks.read_with_options(
                    args.task_id, read_options
                )
                print("Reading run task with workspace task relationships...")
            else:
                run_task = client.run_tasks.read(args.task_id)
                print("Reading run task details...")

            print("Successfully read run task!")
            print(f"Name: {run_task.name}")
            print(f"ID: {run_task.id}")
            print(f"URL: {run_task.url}")
            print(f"Category: {run_task.category}")
            print(f"Enabled: {run_task.enabled}")
            print(f"Description: {run_task.description or 'None'}")
            print(f"HMAC Key: {'[SET]' if run_task.hmac_key else 'None'}")

            if run_task.organization:
                print(f"Organization: {run_task.organization.id}")

            if run_task.workspace_run_tasks:
                print(f"Workspace Run Tasks: {len(run_task.workspace_run_tasks)} items")

            print()
        except Exception as e:
            print(f"Error reading run task: {e}")
            return

    # 4) Update run task if requested
    if args.update and args.task_id:
        _print_header(f"Updating run task: {args.task_id}")
        try:
            update_options = RunTaskUpdateOptions(
                name=f"updated-task-{int(time.time())}",
                description=f"Updated run task at {datetime.now()}",
                url="https://httpbin.org/anything",
                enabled=True,
            )
            print(f"Updating run task '{args.task_id}'...")
            updated_task = client.run_tasks.update(args.task_id, update_options)
            print("Successfully updated run task!")
            print(f"Name: {updated_task.name}")
            print(f"Description: {updated_task.description}")
            print(f"URL: {updated_task.url}")
            print(f"Enabled: {updated_task.enabled}")
            print()
        except Exception as e:
            print(f"Error updating run task: {e}")
            return

    # 5) Delete run task if requested (should be last operation)
    if args.delete and args.task_id:
        _print_header(f"Deleting run task: {args.task_id}")
        try:
            print(f"Deleting run task '{args.task_id}'...")
            client.run_tasks.delete(args.task_id)
            print(f"Successfully deleted run task: {args.task_id}")
            print()
        except Exception as e:
            print(f"Error deleting run task: {e}")
            return


if __name__ == "__main__":
    main()
