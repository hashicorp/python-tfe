#!/usr/bin/env python3
"""
Workspace Run Task Operations Example

Demonstrates workspace run task operations:
1. create() - Attach a run task to a workspace
2. list() - List all workspace run tasks for a workspace
3. read() - Read a workspace run task by ID
4. update() - Update enforcement/stage settings
5. delete() - Delete a workspace run task

Prerequisites:
- Set TFE_TOKEN and TFE_ADDRESS environment variables
- Use valid workspace and run task IDs
"""

import argparse

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    RunTask,
    WorkspaceRunTaskCreateOptions,
    WorkspaceRunTaskUpdateOptions,
)


def _find_matching_workspace_run_task(items, run_task_id: str):
    for item in items:
        if item.run_task and item.run_task.id == run_task_id:
            return item

    if len(items) == 1:
        return items[0]

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Workspace run task operations demo for python-tfe SDK"
    )
    parser.add_argument(
        "--workspace-id",
        required=True,
        help="Workspace ID (example: ws-abc123)",
    )
    parser.add_argument(
        "--run-task-id",
        required=True,
        help="Run task ID (example: task-abc123)",
    )
    parser.add_argument(
        "--delete-existing",
        action="store_true",
        help="Allow delete() to remove a workspace run task that existed before this example ran",
    )
    args = parser.parse_args()

    client = TFEClient(TFEConfig.from_env())

    workspace_id = args.workspace_id
    run_task_id = args.run_task_id

    if workspace_id == "ws-xxxxxxxx" or run_task_id == "task-xxxxxxxx":
        print("Please provide real IDs for --workspace-id and --run-task-id")
        return

    print("=" * 80)
    print("WORKSPACE RUN TASK OPERATIONS")
    print("=" * 80)

    workspace_task = None
    created_in_run = False

    print("\n1. create()")
    try:
        create_options = WorkspaceRunTaskCreateOptions(
            enforcement_level="advisory",
            run_task=RunTask(id=run_task_id),
            stages=["post_plan"],
        )
        workspace_task = client.workspace_run_tasks.create(workspace_id, create_options)
        created_in_run = True
        print(f"Created workspace run task: {workspace_task.id}")
    except Exception as exc:
        print(f"Create result: {exc}")

    print("\n2. list()")
    items = []
    try:
        items = list(client.workspace_run_tasks.list(workspace_id))
        print(f"Found {len(items)} workspace run task(s)")
        for item in items:
            run_task = item.run_task.id if item.run_task else None
            print(
                f"- {item.id} run_task={run_task} enforcement={item.enforcement_level} stages={item.stages}"
            )

        if workspace_task is None:
            workspace_task = _find_matching_workspace_run_task(items, run_task_id)
            if workspace_task is not None:
                print(f"Using existing workspace run task: {workspace_task.id}")
    except Exception as exc:
        print(f"List failed: {exc}")

    print("\n3. read()")
    if workspace_task is None:
        print("Read skipped: no workspace run task ID available")
    else:
        try:
            workspace_task = client.workspace_run_tasks.read(
                workspace_id, workspace_task.id
            )
            print(
                f"Read workspace run task: {workspace_task.id} enforcement={workspace_task.enforcement_level} stages={workspace_task.stages}"
            )
        except Exception as exc:
            print(f"Read failed: {exc}")

    print("\n4. update()")
    if workspace_task is None:
        print("Update skipped: no workspace run task ID available")
    else:
        try:
            update_options = WorkspaceRunTaskUpdateOptions(
                # enforcement_level="mandatory",
                stages=["post_plan", "pre_plan"],
            )
            workspace_task = client.workspace_run_tasks.update(
                workspace_id, workspace_task.id, update_options
            )
            print(
                f"Updated workspace run task: {workspace_task.id} enforcement={workspace_task.enforcement_level} stages={workspace_task.stages}"
            )
        except Exception as exc:
            print(f"Update failed: {exc}")

    print("\n5. delete()")
    if workspace_task is None:
        print("Delete skipped: no workspace run task ID available")
    elif not created_in_run and not args.delete_existing:
        print(
            "Delete skipped: workspace run task existed before this example. "
            "Re-run with --delete-existing to delete it."
        )
    else:
        try:
            client.workspace_run_tasks.delete(workspace_id, workspace_task.id)
            print(f"Deleted workspace run task: {workspace_task.id}")
        except Exception as exc:
            print(f"Delete failed: {exc}")

    print("=" * 80)
    print("WORKSPACE RUN TASK OPERATIONS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
