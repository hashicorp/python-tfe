"""
Terraform Cloud/Enterprise Workspace Run Task Management Example

This example demonstrates comprehensive workspace run task operations using the python-tfe SDK.
It provides a command-line interface for managing workspace run tasks with various operations
including attach/create, read, update, delete, and listing attached tasks.

Prerequisites:
    - Set TFE_TOKEN environment variable with your Terraform Cloud API token
    - Ensure you have access to the target organization and workspaces
    - Run tasks must exist in the organization before attaching to workspaces

Basic Usage:
    python examples/workspace_run_task.py --help

Core Operations:

1. List Workspace Run Tasks (default operation):
    python examples/workspace_run_task.py --workspace-id ws-abc123
    python examples/workspace_run_task.py --workspace-id ws-abc123 --page-size 20

2. Attach Run Task to Workspace (Create):
    python examples/workspace_run_task.py --workspace-id ws-abc123 --run-task-id task-def456 --create --enforcement-level mandatory --stages pre-plan post-plan

3. Read Workspace Run Task Details:
    python examples/workspace_run_task.py --workspace-id ws-abc123 --workspace-task-id wstask-xyz789

4. Update Workspace Run Task:
    python examples/workspace_run_task.py --workspace-id ws-abc123 --workspace-task-id wstask-xyz789 --update --enforcement-level advisory --stages pre-plan

5. Delete Workspace Run Task:
    python examples/workspace_run_task.py --workspace-id ws-abc123 --workspace-task-id wstask-xyz789 --delete
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
    WorkspaceRunTaskListOptions,
    WorkspaceRunTaskUpdateOptions,
)

# Ensure models are fully rebuilt to resolve forward references
WorkspaceRunTaskUpdateOptions.model_rebuild()
WorkspaceRunTaskCreateOptions.model_rebuild()


def _print_header(title: str) -> None:
    """Print a formatted header for operations."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Workspace Run Task demo for python-tfe SDK"
    )
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--workspace-id", required=True, help="Workspace ID")
    parser.add_argument(
        "--run-task-id", help="Run Task ID to attach (for create operation)"
    )
    parser.add_argument(
        "--workspace-task-id", help="Workspace Run Task ID for read/update/delete"
    )
    parser.add_argument(
        "--create", action="store_true", help="Create/attach a workspace run task"
    )
    parser.add_argument(
        "--update", action="store_true", help="Update a workspace run task"
    )
    parser.add_argument(
        "--delete", action="store_true", help="Delete a workspace run task"
    )
    parser.add_argument(
        "--enforcement-level",
        choices=["advisory", "mandatory"],
        help="Enforcement level for create/update",
    )
    parser.add_argument(
        "--stages",
        nargs="+",
        choices=["pre-plan", "post-plan", "pre-apply", "post-apply"],
        help="Stages to run the task in (for create/update)",
    )
    parser.add_argument(
        "--stage",
        choices=["pre-plan", "post-plan", "pre-apply", "post-apply"],
        help="Deprecated: Single stage to run the task in (use --stages instead)",
    )
    parser.add_argument("--page", type=int, default=1, help="Page number for listing")
    parser.add_argument(
        "--page-size", type=int, default=10, help="Page size for listing"
    )
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # Create a new workspace run task (attach run task to workspace)
    if args.create:
        if not args.run_task_id:
            print("Error: --run-task-id is required for creating a workspace run task")
            return

        if not args.enforcement_level:
            print("Error: --enforcement-level is required for creating")
            return

        _print_header("Creating Workspace Run Task")

        # Convert enforcement level string to enum
        enforcement_level = (
            TaskEnforcementLevel.MANDATORY
            if args.enforcement_level == "mandatory"
            else TaskEnforcementLevel.ADVISORY
        )

        # Convert stages to enum
        stages = None
        if args.stages:
            stages = []
            for stage_str in args.stages:
                if stage_str == "pre-plan":
                    stages.append(Stage.PRE_PLAN)
                elif stage_str == "post-plan":
                    stages.append(Stage.POST_PLAN)
                elif stage_str == "pre-apply":
                    stages.append(Stage.PRE_APPLY)
                elif stage_str == "post-apply":
                    stages.append(Stage.POST_APPLY)

        # Deprecated stage support
        stage = None
        if args.stage:
            if args.stage == "pre-plan":
                stage = Stage.PRE_PLAN
            elif args.stage == "post-plan":
                stage = Stage.POST_PLAN
            elif args.stage == "pre-apply":
                stage = Stage.PRE_APPLY
            elif args.stage == "post-apply":
                stage = Stage.POST_APPLY

        # Create RunTask object with just ID (minimal required)
        run_task = RunTask(
            id=args.run_task_id,
            name="",  # Name not needed for attachment
            url="",  # URL not needed for attachment
            category="task",
            enabled=True,
        )

        options = WorkspaceRunTaskCreateOptions(
            enforcement_level=enforcement_level,
            run_task=run_task,
            stages=stages,
            stage=stage,
        )

        try:
            workspace_task = client.workspace_run_tasks.create(
                args.workspace_id, options
            )
            print("✓ Successfully attached run task to workspace")
            print(f"  Workspace Task ID: {workspace_task.id}")
            print(f"  Enforcement Level: {workspace_task.enforcement_level.value}")
            print(f"  Stage: {workspace_task.stage.value}")
            if workspace_task.stages:
                print(f"  Stages: {[s.value for s in workspace_task.stages]}")
        except Exception as e:
            print(f"✗ Failed to create workspace run task: {e}")

    # Update an existing workspace run task
    elif args.update:
        if not args.workspace_task_id:
            print("Error: --workspace-task-id is required for updating")
            return

        _print_header("Updating Workspace Run Task")

        # Build update options
        enforcement_level = None
        if args.enforcement_level:
            enforcement_level = (
                TaskEnforcementLevel.MANDATORY
                if args.enforcement_level == "mandatory"
                else TaskEnforcementLevel.ADVISORY
            )

        # Update stages if provided
        stages = None
        if args.stages:
            stages = []
            for stage_str in args.stages:
                if stage_str == "pre-plan":
                    stages.append(Stage.PRE_PLAN)
                elif stage_str == "post-plan":
                    stages.append(Stage.POST_PLAN)
                elif stage_str == "pre-apply":
                    stages.append(Stage.PRE_APPLY)
                elif stage_str == "post-apply":
                    stages.append(Stage.POST_APPLY)

        options = WorkspaceRunTaskUpdateOptions(
            enforcement_level=enforcement_level, stages=stages
        )

        # Update stage if provided (deprecated)
        if args.stage:
            if args.stage == "pre-plan":
                options.stage = Stage.PRE_PLAN
            elif args.stage == "post-plan":
                options.stage = Stage.POST_PLAN
            elif args.stage == "pre-apply":
                options.stage = Stage.PRE_APPLY
            elif args.stage == "post-apply":
                options.stage = Stage.POST_APPLY

        try:
            workspace_task = client.workspace_run_tasks.update(
                args.workspace_id, args.workspace_task_id, options
            )
            print("✓ Successfully updated workspace run task")
            print(f"  Workspace Task ID: {workspace_task.id}")
            print(f"  Enforcement Level: {workspace_task.enforcement_level.value}")
            print(f"  Stage: {workspace_task.stage.value}")
            if workspace_task.stages:
                print(f"  Stages: {[s.value for s in workspace_task.stages]}")
        except Exception as e:
            print(f"✗ Failed to update workspace run task: {e}")

    # Delete a workspace run task
    elif args.delete:
        if not args.workspace_task_id:
            print("Error: --workspace-task-id is required for deleting")
            return

        _print_header("Deleting Workspace Run Task")

        try:
            client.workspace_run_tasks.delete(args.workspace_id, args.workspace_task_id)
            print(
                f"✓ Successfully deleted workspace run task: {args.workspace_task_id}"
            )
        except Exception as e:
            print(f"✗ Failed to delete workspace run task: {e}")

    # Read a specific workspace run task
    elif args.workspace_task_id:
        _print_header("Reading Workspace Run Task")

        try:
            workspace_task = client.workspace_run_tasks.read(
                args.workspace_id, args.workspace_task_id
            )
            print("✓ Workspace Run Task Details:")
            print(f"  ID: {workspace_task.id}")
            print(f"  Enforcement Level: {workspace_task.enforcement_level.value}")
            print(f"  Stage (deprecated): {workspace_task.stage.value}")
            if workspace_task.stages:
                print(f"  Stages: {[s.value for s in workspace_task.stages]}")
            if workspace_task.run_task:
                print(f"  Run Task ID: {workspace_task.run_task.id}")
            if workspace_task.workspace:
                print(f"  Workspace ID: {workspace_task.workspace.id}")
        except Exception as e:
            print(f"✗ Failed to read workspace run task: {e}")

    # List all workspace run tasks (default operation)
    else:
        _print_header(f"Listing Workspace Run Tasks for Workspace: {args.workspace_id}")

        options = WorkspaceRunTaskListOptions(
            page_number=args.page,
            page_size=args.page_size,
        )

        try:
            count = 0
            for workspace_task in client.workspace_run_tasks.list(
                args.workspace_id, options
            ):
                count += 1
                print(f"\n{count}. Workspace Run Task ID: {workspace_task.id}")
                print(f"   Enforcement Level: {workspace_task.enforcement_level.value}")
                print(f"   Stage: {workspace_task.stage.value}")
                if workspace_task.stages:
                    print(f"   Stages: {[s.value for s in workspace_task.stages]}")
                if workspace_task.run_task:
                    print(f"   Run Task ID: {workspace_task.run_task.id}")

            if count == 0:
                print("No workspace run tasks found for this workspace.")
            else:
                print(f"\n✓ Total workspace run tasks listed: {count}")
        except Exception as e:
            print(f"✗ Failed to list workspace run tasks: {e}")


if __name__ == "__main__":
    main()
