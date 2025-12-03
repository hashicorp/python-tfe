"""
Terraform Cloud/Enterprise Workspace Run Tasks Management Example

This comprehensive example demonstrates workspace run task operations using the python-tfe SDK,
providing a complete command-line interface for managing workspace run tasks with advanced
operations including list, get, create, update, and delete operations.

Prerequisites:
    - Set TFE_TOKEN environment variable with your Terraform Cloud API token
    - Ensure you have access to the target organization and workspace
    - Have a run task created in your organization

Quick Start:
    python examples/workspace_run_tasks.py --help

Core Operations:

1. List Workspace Run Tasks:
    python examples/workspace_run_tasks.py --org my-org --workspace "my-workspace"
    python examples/workspace_run_tasks.py --org my-org --workspace "my-workspace" --page-size 20
    python examples/workspace_run_tasks.py --org my-org --workspace "my-workspace" --include task

2. Get Workspace Run Task:
    python examples/workspace_run_tasks.py --org my-org --workspace "my-workspace" --task-id "wsrt-abc123xyz"

3. Create Workspace Run Task:
    python examples/workspace_run_tasks.py --org my-org --workspace "my-workspace" --create --run-task-id "task-abc123xyz"

4. Update Workspace Run Task:
    python examples/workspace_run_tasks.py --org my-org --workspace "my-workspace" --task-id "wsrt-abc123xyz" --update

5. Delete Workspace Run Task:
    python examples/workspace_run_tasks.py --org my-org --workspace "my-workspace" --task-id "wsrt-abc123xyz" --delete

6. Comprehensive Testing:
    python examples/workspace_run_tasks.py --org my-org --workspace "my-workspace" --all-tests
"""

from __future__ import annotations

import argparse
import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    RunTask,
    Stage,
    TaskEnforcementLevel,
    WorkspaceRunTaskCreateOptions,
    WorkspaceRunTaskIncludeOpt,
    WorkspaceRunTaskListOptions,
    WorkspaceRunTaskReadOptions,
    WorkspaceRunTaskUpdateOptions,
)


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _print_workspace_run_task(task, title: str = "Workspace Run Task Details"):
    """Print workspace run task details in a formatted way."""
    print(f"\n{title}")
    print("-" * 40)
    print(f"ID: {task.id}")
    print(f"Type: {task.type}")
    print(f"Stage: {task.stage}")
    print(f"Enforcement Level: {task.enforcement_level}")

    if hasattr(task, "created_at") and task.created_at:
        print(f"Created At: {task.created_at}")
    if hasattr(task, "updated_at") and task.updated_at:
        print(f"Updated At: {task.updated_at}")


def list_workspace_run_tasks(client: TFEClient, args):
    """List workspace run tasks with various filters."""
    _print_header(f"Listing Workspace Run Tasks for Workspace: {args.workspace}")

    # Build list options
    options = WorkspaceRunTaskListOptions()

    if args.page_size:
        options.page_size = args.page_size
    if args.page:
        options.page_number = args.page
    if args.include:
        include_opts = []
        for inc in args.include.split(","):
            inc = inc.strip()
            if inc == "task":
                include_opts.append(WorkspaceRunTaskIncludeOpt.RUN_TASK)
        if include_opts:
            options.include = include_opts

    # Get workspace ID from workspace name
    try:
        workspace = client.workspaces.read(args.workspace, organization=args.org)
        workspace_id = workspace.id

        task_count = 0
        for task in client.workspace_run_tasks.list(workspace_id, options=options):
            task_count += 1
            _print_workspace_run_task(task, f"Workspace Run Task #{task_count}")

        if task_count == 0:
            print("No workspace run tasks found.")
        else:
            print(f"\nTotal workspace run tasks: {task_count}")

    except Exception as e:
        print(f"Error listing workspace run tasks: {e}")


def get_workspace_run_task(client: TFEClient, args):
    """Get a specific workspace run task."""
    _print_header(f"Getting Workspace Run Task: {args.task_id}")

    try:
        # Get workspace ID from workspace name
        workspace = client.workspaces.read(args.workspace, organization=args.org)
        workspace_id = workspace.id

        # Build read options
        options = WorkspaceRunTaskReadOptions()
        if args.include:
            include_opts = []
            for inc in args.include.split(","):
                inc = inc.strip()
                if inc == "task":
                    include_opts.append(WorkspaceRunTaskIncludeOpt.RUN_TASK)
            if include_opts:
                options.include = include_opts

        task = client.workspace_run_tasks.get(
            workspace_id, args.task_id, options=options
        )
        _print_workspace_run_task(task)

    except Exception as e:
        print(f"Error getting workspace run task: {e}")


def create_workspace_run_task(client: TFEClient, args):
    """Create a new workspace run task."""
    _print_header("Creating Workspace Run Task")

    try:
        # Get workspace ID from workspace name
        workspace = client.workspaces.read(args.workspace, organization=args.org)
        workspace_id = workspace.id

        # Build create options
        enforcement_level = TaskEnforcementLevel.ADVISORY  # Default
        if args.enforcement_level:
            if args.enforcement_level.lower() == "advisory":
                enforcement_level = TaskEnforcementLevel.ADVISORY
            elif args.enforcement_level.lower() == "mandatory":
                enforcement_level = TaskEnforcementLevel.MANDATORY

        stage = None
        if args.stage:
            if args.stage.lower() == "pre_plan":
                stage = Stage.PRE_PLAN
            elif args.stage.lower() == "post_plan":
                stage = Stage.POST_PLAN
            elif args.stage.lower() == "pre_apply":
                stage = Stage.PRE_APPLY
            elif args.stage.lower() == "post_apply":
                stage = Stage.POST_APPLY

        options = WorkspaceRunTaskCreateOptions(
            enforcement_level=enforcement_level,
            stage=stage,
            run_task=RunTask(id=args.run_task_id),
        )

        task = client.workspace_run_tasks.create(workspace_id, options)
        _print_workspace_run_task(task, "Created Workspace Run Task")

    except Exception as e:
        print(f"Error creating workspace run task: {e}")


def update_workspace_run_task(client: TFEClient, args):
    """Update a workspace run task."""
    _print_header(f"Updating Workspace Run Task: {args.task_id}")

    try:
        # Get workspace ID from workspace name
        workspace = client.workspaces.read(args.workspace, organization=args.org)
        workspace_id = workspace.id

        # Build update options
        options = WorkspaceRunTaskUpdateOptions()

        # Set optional fields based on args
        if args.enforcement_level:
            if args.enforcement_level.lower() == "advisory":
                options.enforcement_level = TaskEnforcementLevel.ADVISORY
            elif args.enforcement_level.lower() == "mandatory":
                options.enforcement_level = TaskEnforcementLevel.MANDATORY

        if args.stage:
            if args.stage.lower() == "pre_plan":
                options.stage = Stage.PRE_PLAN
            elif args.stage.lower() == "post_plan":
                options.stage = Stage.POST_PLAN
            elif args.stage.lower() == "pre_apply":
                options.stage = Stage.PRE_APPLY
            elif args.stage.lower() == "post_apply":
                options.stage = Stage.POST_APPLY

        task = client.workspace_run_tasks.update(workspace_id, args.task_id, options)
        _print_workspace_run_task(task, "Updated Workspace Run Task")

    except Exception as e:
        print(f"Error updating workspace run task: {e}")


def delete_workspace_run_task(client: TFEClient, args):
    """Delete a workspace run task."""
    _print_header(f"Deleting Workspace Run Task: {args.task_id}")

    try:
        # Get workspace ID from workspace name
        workspace = client.workspaces.read(args.workspace, organization=args.org)
        workspace_id = workspace.id

        client.workspace_run_tasks.delete(workspace_id, args.task_id)
        print("Workspace run task deleted successfully.")

    except Exception as e:
        print(f"Error deleting workspace run task: {e}")


def run_all_tests(client: TFEClient, args):
    """Run comprehensive tests of all workspace run task operations."""
    _print_header("Running All Workspace Run Task Tests")

    if not args.run_task_id:
        print("Error: --run-task-id is required for comprehensive testing")
        return

    test_workspace_id = None
    test_task_id = None

    try:
        # Get workspace ID
        workspace = client.workspaces.read(args.workspace, organization=args.org)
        test_workspace_id = workspace.id

        print("\n1. Testing LIST operation...")
        task_count = 0
        for task in client.workspace_run_tasks.list(test_workspace_id):
            task_count += 1
            if task_count <= 3:  # Show first 3
                _print_workspace_run_task(task, f"Task #{task_count}")
        print(f"Found {task_count} existing workspace run tasks")

        print("\n2. Testing CREATE operation...")
        create_options = WorkspaceRunTaskCreateOptions(
            run_task=RunTask(id=args.run_task_id),
            enforcement_level=TaskEnforcementLevel.ADVISORY,
            stage=Stage.POST_PLAN,
        )
        created_task = client.workspace_run_tasks.create(
            test_workspace_id, create_options
        )
        test_task_id = created_task.id
        _print_workspace_run_task(created_task, "Created Test Task")

        print("\n3. Testing GET operation...")
        retrieved_task = client.workspace_run_tasks.get(test_workspace_id, test_task_id)
        _print_workspace_run_task(retrieved_task, "Retrieved Task")

        print("\n4. Testing UPDATE operation...")
        update_options = WorkspaceRunTaskUpdateOptions(
            enforcement_level=TaskEnforcementLevel.MANDATORY
        )
        updated_task = client.workspace_run_tasks.update(
            test_workspace_id, test_task_id, update_options
        )
        _print_workspace_run_task(updated_task, "Updated Task")

        print("\n5. Testing DELETE operation...")
        client.workspace_run_tasks.delete(test_workspace_id, test_task_id)
        print("Test task deleted successfully")

        print("\nAll tests completed successfully!")

    except Exception as e:
        print(f"Test failed: {e}")
        # Cleanup on failure
        if test_workspace_id and test_task_id:
            try:
                client.workspace_run_tasks.delete(test_workspace_id, test_task_id)
                print("Cleaned up test task")
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="Workspace Run Tasks demo for python-tfe SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Connection settings
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))

    # Required arguments
    parser.add_argument("--org", required=True, help="Organization name")
    parser.add_argument("--workspace", required=True, help="Workspace name")

    # Identification arguments
    parser.add_argument(
        "--task-id", help="Workspace run task ID for get/update/delete operations"
    )
    parser.add_argument("--run-task-id", help="Run task ID for create operations")

    # Operations
    parser.add_argument(
        "--create", action="store_true", help="Create a new workspace run task"
    )
    parser.add_argument(
        "--update", action="store_true", help="Update a workspace run task"
    )
    parser.add_argument(
        "--delete", action="store_true", help="Delete a workspace run task"
    )
    parser.add_argument(
        "--all-tests", action="store_true", help="Run all operation tests"
    )

    # Listing options
    parser.add_argument("--page", type=int, default=1, help="Page number for listing")
    parser.add_argument("--page-size", type=int, help="Page size for listing")
    parser.add_argument("--include", help="Include options (task)")

    # Task configuration options
    parser.add_argument(
        "--enforcement-level",
        choices=["advisory", "mandatory"],
        help="Enforcement level for the task",
    )
    parser.add_argument(
        "--stage",
        choices=["pre_plan", "post_plan", "pre_apply", "post_apply"],
        help="Stage when the task should run",
    )

    args = parser.parse_args()

    # Validate token
    if not args.token:
        print("Error: TFE_TOKEN environment variable or --token argument is required")
        return 1

    # Create client
    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    try:
        # Determine operation
        if args.all_tests:
            run_all_tests(client, args)
        elif args.create:
            if not args.run_task_id:
                print("Error: --run-task-id is required for create operation")
                return 1
            create_workspace_run_task(client, args)
        elif args.update:
            if not args.task_id:
                print("Error: --task-id is required for update operation")
                return 1
            update_workspace_run_task(client, args)
        elif args.delete:
            if not args.task_id:
                print("Error: --task-id is required for delete operation")
                return 1
            delete_workspace_run_task(client, args)
        elif args.task_id:
            get_workspace_run_task(client, args)
        else:
            list_workspace_run_tasks(client, args)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
