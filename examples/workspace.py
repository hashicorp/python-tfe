# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""
Terraform Cloud/Enterprise Workspace Management Example

Prerequisites:
    - Set TFE_TOKEN environment variable with your Terraform Cloud API token
    - Ensure you have access to the target organization

Quick Start:
    python examples/workspace.py --help

Core Operations:

1. List Workspaces:
    python examples/workspace.py --org my-org
    python examples/workspace.py --org my-org --page-size 20 --page 2
    python examples/workspace.py --org my-org --search "demo" --tags "env:prod"
    python examples/workspace.py --org my-org --wildcard-name "test-*"

2. Create Workspace:
    python examples/workspace.py --org my-org --create

3. Read Operations:
    python examples/workspace.py --org my-org --workspace "my-workspace" --read
    python examples/workspace.py --org my-org --workspace-id "ws-abc123xyz" --read

4. Update Operations:
    python examples/workspace.py --org my-org --workspace "my-workspace" --update
    python examples/workspace.py --org my-org --workspace-id "ws-abc123xyz" --update

5. Lock Management:
    python examples/workspace.py --org my-org --workspace-id "ws-abc123xyz" --lock
    python examples/workspace.py --org my-org --workspace-id "ws-abc123xyz" --unlock
    python examples/workspace.py --org my-org --workspace-id "ws-abc123xyz" --force-unlock
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    ExecutionMode,
    Tag,
    WorkspaceAddTagsOptions,
    WorkspaceAssignSSHKeyOptions,
    WorkspaceCreateOptions,
    WorkspaceIncludeOpt,
    WorkspaceListOptions,
    WorkspaceListRemoteStateConsumersOptions,
    WorkspaceLockOptions,
    WorkspaceReadOptions,
    WorkspaceRemoveTagsOptions,
    WorkspaceTagListOptions,
    WorkspaceUpdateOptions,
)


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Workspace demo for python-tfe SDK")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--org", required=True, help="Organization name")
    parser.add_argument("--workspace", help="Workspace name to read/update/delete")
    parser.add_argument("--workspace-id", help="Workspace ID for ID-based operations")

    # Core CRUD Operations
    parser.add_argument(
        "--list", action="store_true", help="List workspaces in the organization"
    )
    parser.add_argument("--create", action="store_true", help="Create a new workspace")
    parser.add_argument("--delete", action="store_true", help="Delete the workspace")
    parser.add_argument(
        "--safe-delete",
        action="store_true",
        help="Safely delete the workspace, passed along with --delete",
    )
    parser.add_argument(
        "--update", action="store_true", help="Update workspace settings"
    )

    # Lock Management
    parser.add_argument("--lock", action="store_true", help="Lock the workspace")
    parser.add_argument("--unlock", action="store_true", help="Unlock the workspace")
    parser.add_argument(
        "--force-unlock", action="store_true", help="Force unlock the workspace"
    )

    # VCS Operations
    parser.add_argument(
        "--remove-vcs", action="store_true", help="Remove VCS connection"
    )

    parser.add_argument("--read", action="store_true", help="Read workspace details")
    parser.add_argument(
        "--tag-ops", action="store_true", help="Test tag management operations"
    )
    parser.add_argument(
        "--ssh-keys", action="store_true", help="Test SSH key operations"
    )
    parser.add_argument(
        "--remote-state", action="store_true", help="Test remote state operations"
    )
    parser.add_argument(
        "--retention", action="store_true", help="Test data retention policies"
    )
    parser.add_argument(
        "--readme", action="store_true", help="Test readme functionality"
    )

    # Listing and Filtering
    parser.add_argument(
        "--page-size", type=int, default=10, help="Page size for listing"
    )
    parser.add_argument("--search", help="Search workspaces by partial name")
    parser.add_argument("--tags", help="Filter by tags (comma-separated)")
    parser.add_argument(
        "--exclude-tags", help="Exclude workspaces with these tags (comma-separated)"
    )
    parser.add_argument("--wildcard-name", help="Filter by wildcard name matching")
    parser.add_argument("--project-id", help="Filter by project ID")
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # 1) List workspaces in the organization
    if args.list:
        _print_header("Listing workspaces")
        try:
            # Create options for listing workspaces with pagination and filters
            options = WorkspaceListOptions(
                page_size=args.page_size,
                search=args.search,
                tags=args.tags,
                exclude_tags=args.exclude_tags,
                wildcard_name=args.wildcard_name,
                project_id=args.project_id,
            )
            print(
                f"Fetching workspaces from organization '{args.org}', size {args.page_size})..."
            )

            # Get workspaces and convert to list safely
            workspace_gen = client.workspaces.list(args.org, options)
            workspace_list = []
            count = 0
            for ws in workspace_gen:
                workspace_list.append(ws)
                count += 1
                if count >= args.page_size * 2:  # Safety limit based on page size
                    break

            print(f"Found {len(workspace_list)} workspaces")
            print()

            if not workspace_list:
                print("No workspaces found in this organization.")
            else:
                for i, ws in enumerate(workspace_list, 1):
                    print(f"{i:2d}. {ws.name}")
                    print(f"ID: {ws.id}")
                    print(f"Execution Mode: {ws.execution_mode}")
                    print(f"Auto Apply: {ws.auto_apply}")
                    print()
        except Exception as e:
            print(f"Error listing workspaces: {e}")
            return

    # 2) Create a new workspace if requested
    if args.create:
        _print_header("Creating a new workspace")
        try:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            workspace_name = f"demo-workspace-{timestamp}"

            create_options = WorkspaceCreateOptions(
                name=workspace_name,
                description=f"Demo workspace created at {datetime.now()}",
                auto_apply=False,
                execution_mode=ExecutionMode.REMOTE,
                terraform_version="1.5.0",
                working_directory="terraform/",
                file_triggers_enabled=True,
                queue_all_runs=False,
                speculative_enabled=True,
                trigger_prefixes=["modules/", "shared/"],
            )

            print(
                f"Creating workspace '{workspace_name}' in organization '{args.org}'..."
            )
            workspace = client.workspaces.create(args.org, create_options)
            print("Successfully created workspace!")
            print(f"Name: {workspace.name}")
            print(f"ID: {workspace.id}")
            print(f"Description: {workspace.description}")
            print(f"Execution Mode: {workspace.execution_mode}")
            print(f"Auto Apply: {workspace.auto_apply}")
            print(f"Terraform Version: {workspace.terraform_version}")
            print()

            args.workspace = (
                workspace.name
            )  # Use the created workspace for other operations
            args.workspace_id = workspace.id
        except Exception as e:
            print(f"Error creating workspace: {e}")
            return

    # 3a) Read workspace details by name
    if args.read and args.workspace:
        _print_header("Read workspace by name")

        # Test read_with_options (enhanced read)
        try:
            print("Testing read_with_options()...")
            read_options = WorkspaceReadOptions(
                include=[WorkspaceIncludeOpt.CURRENT_RUN, WorkspaceIncludeOpt.OUTPUTS]
            )
            workspace = client.workspaces.read_with_options(
                args.workspace, read_options, organization=args.org
            )
            print(f"read_with_options: {workspace.name}")
            print(f"ID: {workspace.id}")
            print(f"Description: {workspace.description}")
            print(f"Execution Mode: {workspace.execution_mode}")
            print(f"Auto Apply: {workspace.auto_apply}")
            print(f"Locked: {workspace.locked}")
            print(f"Terraform Version: {workspace.terraform_version}")
            print(f"Working Directory: {workspace.working_directory}")

            # Set workspace_id for further operations
            if not args.workspace_id:
                args.workspace_id = workspace.id
        except Exception as e:
            print(f"read_with_options error: {e}")

    # 3b) Read workspace by ID
    if args.read and args.workspace_id:
        _print_header("Read workspace by ID")
        try:
            print("Testing read_by_id_with_options()...")
            options = WorkspaceReadOptions(include=[WorkspaceIncludeOpt.ORGANIZATION])
            workspace = client.workspaces.read_by_id_with_options(
                args.workspace_id, options
            )
            print(
                f"read_by_id_with_options: {workspace.name} with organization included"
            )
        except Exception as e:
            print(f"read_by_id_with_options error: {e}")

    # 4a) Update workspace by name
    if args.update and args.workspace:
        _print_header("Update workspace by name")

        # Test standard update method
        try:
            print("Testing update() by name...")
            update_options = WorkspaceUpdateOptions(
                name=args.workspace,  # Name is required
                description=f"Updated workspace at {datetime.now()}",
                auto_apply=True,
                terraform_version="1.6.0",
            )
            updated_workspace = client.workspaces.update(
                args.workspace, update_options, organization=args.org
            )
            print("update: Successfully updated workspace!")
            print(f"Name: {updated_workspace.name}")
            print(f"Description: {updated_workspace.description}")
            print(f"Auto Apply: {updated_workspace.auto_apply}")
            print(f"Terraform Version: {updated_workspace.terraform_version}")
            print()
        except Exception as e:
            print(f"update error: {e}")

    # 4b) Update workspace by ID
    if args.update and args.workspace_id and not args.workspace:
        try:
            print("Testing update_by_id()...")
            # Get current workspace to preserve the name
            current_workspace = client.workspaces.read_by_id(args.workspace_id)
            update_options = WorkspaceUpdateOptions(
                name=current_workspace.name,  # Required field
                description=f"Updated via ID at {datetime.now()}",
            )
            updated_workspace = client.workspaces.update_by_id(
                args.workspace_id, update_options
            )
            print(
                f"update_by_id: Updated description to '{updated_workspace.description}'"
            )
        except Exception as e:
            print(f"update_by_id error: {e}")

    # 5) Lock workspace if requested
    if args.lock and args.workspace_id:
        _print_header(f"Locking workspace: {args.workspace_id}")
        lock_options = WorkspaceLockOptions(reason="Demo lock via python-tfe SDK")

        locked_workspace = client.workspaces.lock(args.workspace_id, lock_options)
        print(f"Locked workspace: {locked_workspace.name}")
        print(f"Lock reason: {locked_workspace.locked_by}")

    # 6) Unlock workspace if requested
    if args.unlock and args.workspace_id:
        _print_header(f"Unlocking workspace: {args.workspace_id}")

        unlocked_workspace = client.workspaces.unlock(args.workspace_id)
        print(f"Unlocked workspace: {unlocked_workspace.name}")

    # 7) Remove VCS connection if requested
    if args.remove_vcs and args.workspace:
        _print_header(f"Removing VCS connection from workspace: {args.workspace}")
        try:
            print(
                f"Removing VCS connection from workspace '{args.workspace}' in organization '{args.org}'..."
            )
            workspace = client.workspaces.remove_vcs_connection(
                args.workspace, organization=args.org
            )
            print("Successfully removed VCS connection from workspace!")
            print(f"Workspace: {workspace.name}")
            print()
        except Exception as e:
            print(f"Error removing VCS connection: {e}")

    # 8) Demonstrate tag operations
    if args.tag_ops and args.workspace_id:
        _print_header("Tag operations")

        # List existing tags
        tag_options = WorkspaceTagListOptions(page_size=20)
        try:
            tags = list(client.workspaces.list_tags(args.workspace_id, tag_options))
            print(f"Current tags: {[tag.name for tag in tags]}")
        except Exception as e:
            print(f"Error listing tags: {e}")

        # Add some demo tags
        try:
            add_tag_options = WorkspaceAddTagsOptions(
                tags=[Tag(name="demo"), Tag(name="python-tfe")]
            )
            client.workspaces.add_tags(args.workspace_id, add_tag_options)
            print("Added demo tags: demo, python-tfe")
        except Exception as e:
            print(f"Error adding tags: {e}")

        # Test remove_tags
        try:
            print("Testing remove_tags()...")
            remove_options = WorkspaceRemoveTagsOptions(tags=[Tag(name="demo")])
            client.workspaces.remove_tags(args.workspace_id, remove_options)
            print("remove_tags: Removed 'demo' tag")
        except Exception as e:
            print(f"remove_tags: {e}")

        # Test list_tag_bindings
        try:
            print("Testing list_tag_bindings()...")
            bindings = list(client.workspaces.list_tag_bindings(args.workspace_id))
            print(f"list_tag_bindings: Found {len(bindings)} tag bindings")
        except Exception as e:
            print(f"list_tag_bindings error: {e}")

        # Test list_effective_tag_bindings
        try:
            print("Testing list_effective_tag_bindings()...")
            effective_bindings = list(
                client.workspaces.list_effective_tag_bindings(args.workspace_id)
            )
            print(
                f"list_effective_tag_bindings: Found {len(effective_bindings)} effective bindings"
            )
        except Exception as e:
            print(f"list_effective_tag_bindings error: {e}")

    # 9) Demonstrate remote state consumer operations
    if args.remote_state and args.workspace_id:
        _print_header("Remote state consumer operations")

        # List remote state consumers
        try:
            consumer_options = WorkspaceListRemoteStateConsumersOptions(page_size=10)
            consumers = list(
                client.workspaces.list_remote_state_consumers(
                    args.workspace_id, consumer_options
                )
            )
            print(f"Remote state consumers: {len(consumers)}")
            for consumer in consumers:
                print(f"- {consumer.name} (ID: {consumer.id})")
        except Exception as e:
            print(f"Error listing remote state consumers: {e}")

    # 10) Test force unlock
    if args.force_unlock and args.workspace_id:
        _print_header("Testing force unlock")
        try:
            print("Testing force_unlock()...")
            workspace = client.workspaces.force_unlock(args.workspace_id)
            print(f"force_unlock: Workspace {workspace.name} force unlocked")
        except Exception as e:
            print(f"force_unlock result: {e}")
            print("(Expected if workspace wasn't locked)")

    # 11) Test SSH key operations
    if args.ssh_keys and args.workspace_id:
        _print_header("Testing SSH key operations")

        # First, list available SSH keys
        try:
            print("Listing available SSH keys...")
            ssh_keys = list(client.ssh_keys.list(args.org))
            if ssh_keys:
                ssh_key = ssh_keys[0]
                print(f"Found SSH key: {ssh_key.name} (ID: {ssh_key.id})")

                # Test assign SSH key
                try:
                    print("Testing assign_ssh_key()...")
                    options = WorkspaceAssignSSHKeyOptions(ssh_key_id=ssh_key.id)
                    workspace = client.workspaces.assign_ssh_key(
                        args.workspace_id, options
                    )
                    print(f"assign_ssh_key: Assigned key to {workspace.name}")

                    # Test unassign SSH key
                    print("Testing unassign_ssh_key()...")
                    workspace = client.workspaces.unassign_ssh_key(args.workspace_id)
                    print(f"unassign_ssh_key: Removed key from {workspace.name}")

                except Exception as e:
                    print(f"SSH key assignment error: {e}")
            else:
                print("No SSH keys available for testing")
                print(
                    " assign_ssh_key and unassign_ssh_key methods available but not tested"
                )

        except Exception as e:
            print(f"SSH key listing error: {e}")

    # 14) Test data retention policies
    if args.retention and args.workspace_id:
        _print_header("Testing data retention policies")

        try:
            print("Testing read_data_retention_policy()...")
            policy = client.workspaces.read_data_retention_policy(args.workspace_id)
            print(f"read_data_retention_policy: {policy}")
        except Exception as e:
            print(f"read_data_retention_policy: {e}")
            print("(Expected if no policy is set)")

        try:
            print("Testing read_data_retention_policy_choice()...")
            choice = client.workspaces.read_data_retention_policy_choice(
                args.workspace_id
            )
            print(f"read_data_retention_policy_choice: {choice}")
        except Exception as e:
            print(f"read_data_retention_policy_choice: {e}")

    # 15) Test readme functionality
    if args.readme and args.workspace_id:
        _print_header("Testing readme functionality")

        try:
            print("Testing readme()...")
            readme = client.workspaces.readme(args.workspace_id)
            if readme:
                print(f"readme: Found README content ({len(readme)} characters)")
                print(
                    f"Preview: {readme[:100]}..."
                    if len(readme) > 100
                    else f"Content: {readme}"
                )
            else:
                print("readme: No README content found")
        except Exception as e:
            print(f"readme result: {e}")
            print("(Expected if workspace has no README)")

    # 16) Delete workspace if requested (should be last operation)
    if args.delete and args.workspace:
        _print_header(f"Deleting workspace: {args.workspace}")

        if args.safe_delete:
            client.workspaces.safe_delete(args.workspace, organization=args.org)
            print(f"Safely deleted workspace: {args.workspace}")
        else:
            client.workspaces.delete(args.workspace, organization=args.org)
            print(f"Deleted workspace: {args.workspace}")


if __name__ == "__main__":
    main()
