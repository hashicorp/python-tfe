"""
Terraform Cloud/Enterprise Run Trigger Management Example

This example demonstrates comprehensive run trigger operations using the python-tfe SDK.
It provides a command-line interface for managing TFE run triggers with various operations
including create, read, delete, and advanced listing capabilities with filtering options.

Prerequisites:
    - Set TFE_TOKEN environment variable with your Terraform Cloud API token
    - Ensure you have access to the target organization and workspaces

Basic Usage:
    python examples/run_trigger.py --help

Core Operations:

1. List Run Triggers (default operation):
    python examples/run_trigger.py --org my-org --workspace-id ws-abc123
    python examples/run_trigger.py --org my-org --workspace-id ws-abc123 --page-size 20

2. Create New Run Trigger:
    python examples/run_trigger.py --org my-org --workspace-id ws-abc123 --source-workspace-id ws-def456 --create

3. Read Run Trigger Details:
    python examples/run_trigger.py --org my-org --trigger-id rt-abc123xyz

4. Delete Run Trigger:
    python examples/run_trigger.py --org my-org --trigger-id rt-abc123xyz --delete
"""

from __future__ import annotations

import argparse
import os
import time

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    RunTriggerCreateOptions,
    RunTriggerFilterOp,
    RunTriggerIncludeOp,
    RunTriggerListOptions,
    Workspace,
)


def _print_header(title: str) -> None:
    """Print a formatted header for operations."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Run Trigger demo for python-tfe SDK")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--org", required=True, help="Organization name")
    parser.add_argument(
        "--workspace-id", help="Target workspace ID for listing/creating run triggers"
    )
    parser.add_argument(
        "--source-workspace-id", help="Source workspace ID for creating run triggers"
    )
    parser.add_argument(
        "--trigger-id", help="Run Trigger ID for read/delete operations"
    )
    parser.add_argument(
        "--create", action="store_true", help="Create a new run trigger"
    )
    parser.add_argument("--delete", action="store_true", help="Delete the run trigger")
    parser.add_argument(
        "--filter-type",
        choices=["inbound", "outbound"],
        default="inbound",
        help="Filter by trigger type: inbound or outbound",
    )
    parser.add_argument(
        "--include-workspace",
        action="store_true",
        help="Include workspace relationships in read operations",
    )
    parser.add_argument(
        "--include-sourceable",
        action="store_true",
        help="Include sourceable relationships in read operations",
    )
    parser.add_argument("--page", type=int, default=1, help="Page number for listing")
    parser.add_argument(
        "--page-size", type=int, default=10, help="Page size for listing"
    )
    args = parser.parse_args()

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # 1) List run triggers for the workspace
    if args.workspace_id:
        _print_header("Listing run triggers")
        try:
            # Create options for listing run triggers with pagination and filtering
            filter_type = (
                RunTriggerFilterOp.RUN_TRIGGER_INBOUND
                if args.filter_type == "inbound"
                else RunTriggerFilterOp.RUN_TRIGGER_OUTBOUND
            )

            include_options = []
            if args.include_workspace:
                include_options.append(RunTriggerIncludeOp.RUN_TRIGGER_WORKSPACE)
            if args.include_sourceable:
                include_options.append(RunTriggerIncludeOp.RUN_TRIGGER_SOURCEABLE)

            options = RunTriggerListOptions(
                page_number=args.page,
                page_size=args.page_size,
                run_trigger_type=filter_type,
                include=include_options,
            )

            filter_info = f" ({args.filter_type} triggers)"
            include_info = (
                f" with includes: {[opt.value for opt in include_options]}"
                if include_options
                else ""
            )
            print(
                f"Fetching run triggers for workspace '{args.workspace_id}' (page {args.page}, size {args.page_size}){filter_info}{include_info}..."
            )

            # Get run triggers and convert to list safely
            run_trigger_gen = client.run_triggers.list(args.workspace_id, options)
            run_trigger_list = []
            count = 0
            for trigger in run_trigger_gen:
                run_trigger_list.append(trigger)
                count += 1
                if count >= args.page_size * 2:  # Safety limit based on page size
                    break

            print(f"Found {len(run_trigger_list)} run triggers")
            print()

            if not run_trigger_list:
                print("No run triggers found for this workspace.")
            else:
                for i, trigger in enumerate(run_trigger_list, 1):
                    print(
                        f"{i:2d}. {trigger.sourceable_name} → {trigger.workspace_name}"
                    )
                    print(f"ID: {trigger.id}")
                    print(f"Created: {trigger.created_at}")
                    if trigger.sourceable and hasattr(trigger.sourceable, "id"):
                        print(f"Source Workspace ID: {trigger.sourceable.id}")
                    if trigger.workspace and hasattr(trigger.workspace, "id"):
                        print(f"Target Workspace ID: {trigger.workspace.id}")
                    print()
        except Exception as e:
            print(f"Error listing run triggers: {e}")
            return

    # 2) Create a new run trigger if requested
    if args.create and args.workspace_id and args.source_workspace_id:
        _print_header("Creating a new run trigger")
        try:
            # Create a workspace object for the source
            source_workspace = Workspace(
                id=args.source_workspace_id,
                name=f"source-workspace-{int(time.time())}",
                organization=args.org,
            )

            create_options = RunTriggerCreateOptions(sourceable=source_workspace)

            print(
                f"Creating run trigger from workspace '{args.source_workspace_id}' to '{args.workspace_id}'..."
            )
            run_trigger = client.run_triggers.create(args.workspace_id, create_options)
            print("Successfully created run trigger!")
            print(f"ID: {run_trigger.id}")
            print(f"Source: {run_trigger.sourceable_name}")
            print(f"Target: {run_trigger.workspace_name}")
            print(f"Created: {run_trigger.created_at}")

            if run_trigger.sourceable:
                print(
                    f"   Source Workspace: {run_trigger.sourceable.name} (ID: {run_trigger.sourceable.id})"
                )
            if run_trigger.workspace:
                print(
                    f"   Target Workspace: {run_trigger.workspace.name} (ID: {run_trigger.workspace.id})"
                )
            print()

            args.trigger_id = (
                run_trigger.id
            )  # Use the created trigger for other operations
        except Exception as e:
            print(f"Error creating run trigger: {e}")
            return
    elif args.create:
        print("Error: --create requires both --workspace-id and --source-workspace-id")
        return

    # 3) Read run trigger details if trigger ID is provided
    if args.trigger_id:
        _print_header(f"Reading run trigger: {args.trigger_id}")
        try:
            print("Reading run trigger details...")
            run_trigger = client.run_triggers.read(args.trigger_id)

            print("Successfully read run trigger!")
            print(f"ID: {run_trigger.id}")
            print(f"Type: {run_trigger.type}")
            print(f"Source: {run_trigger.sourceable_name}")
            print(f"Target: {run_trigger.workspace_name}")
            print(f"Created: {run_trigger.created_at}")

            # Show detailed workspace information
            if run_trigger.sourceable:
                print("Source Workspace Details:")
                print(f"- Name: {run_trigger.sourceable.name}")
                print(f"- ID: {run_trigger.sourceable.id}")
                if (
                    hasattr(run_trigger.sourceable, "organization")
                    and run_trigger.sourceable.organization
                ):
                    print(f"- Organization: {run_trigger.sourceable.organization}")

            if run_trigger.workspace:
                print("Target Workspace Details:")
                print(f"- Name: {run_trigger.workspace.name}")
                print(f"- ID: {run_trigger.workspace.id}")
                if (
                    hasattr(run_trigger.workspace, "organization")
                    and run_trigger.workspace.organization
                ):
                    print(f"- Organization: {run_trigger.workspace.organization}")

            print()
        except Exception as e:
            print(f"Error reading run trigger: {e}")
            return

    # 4) Delete run trigger if requested (should be last operation)
    if args.delete and args.trigger_id:
        _print_header(f"Deleting run trigger: {args.trigger_id}")
        try:
            print(f"Deleting run trigger '{args.trigger_id}'...")
            client.run_triggers.delete(args.trigger_id)
            print(f"Successfully deleted run trigger: {args.trigger_id}")
            print()
        except Exception as e:
            print(f"Error deleting run trigger: {e}")
            return


if __name__ == "__main__":
    main()
