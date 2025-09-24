from __future__ import annotations

import argparse
import os
from datetime import datetime

from tfe import TFEClient, TFEConfig
from tfe.models.run import (
    RunCreateOptions,
    RunIncludeOpt,
    RunListForOrganizationOptions,
    RunListOptions,
    RunReadOptions,
    RunVariable,
)


def _print_header(title: str):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Runs demo for python-tfe SDK")
    parser.add_argument(
        "--address", default=os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    )
    parser.add_argument("--token", default=os.getenv("TFE_TOKEN", ""))
    parser.add_argument("--workspace-id", help="Workspace ID")
    parser.add_argument(
        "--organization",
        default=os.getenv("TFE_ORG", ""),
        help="Organization name (for org-level operations)",
    )
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=10)
    parser.add_argument("--create-run", action="store_true", help="Create a new run")
    parser.add_argument(
        "--run-actions", action="store_true", help="Demo run actions (safe mode)"
    )
    args = parser.parse_args()

    if not args.token:
        print("Error: TFE_TOKEN environment variable or --token required")
        return

    if not args.workspace_id and not args.organization:
        print("Error: At least one of --workspace-id or --organization is required")
        return

    if args.create_run and not args.workspace_id:
        print("Error: --create-run requires --workspace-id")
        return

    cfg = TFEConfig(address=args.address, token=args.token)
    client = TFEClient(cfg)

    # Workspace-specific operations
    if args.workspace_id:
        # 1) List runs in the workspace
        _print_header(f"Listing runs for workspace: {args.workspace_id}")

        options = RunListOptions(
            page_number=args.page,
            page_size=args.page_size,
        )

        try:
            run_list = client.runs.list(args.workspace_id, options)
        except Exception as e:
            print(f"Error listing runs: {e}")
            if args.organization:
                print("Trying organization-level listing instead...")
            else:
                return

        if "run_list" in locals():
            print(f"Total runs: {run_list.total_count}")
            print(f"Page {run_list.current_page} of {run_list.total_pages}")
            print()

            for run in run_list.items:
                print(f"- {run.id} | status={run.status} | created={run.created_at}")
                print(f"  message: {run.message}")
                print(
                    f"  has_changes: {run.has_changes} | is_destroy: {run.is_destroy}"
                )

            if not run_list.items:
                print("No runs found.")
            else:
                # 2) Read the most recent run with details
                _print_header("Reading most recent run details")

                latest_run = run_list.items[0]
                read_options = RunReadOptions(
                    include=[
                        RunIncludeOpt.RUN_PLAN,
                        RunIncludeOpt.RUN_APPLY,
                        RunIncludeOpt.RUN_CREATED_BY,
                        RunIncludeOpt.RUN_WORKSPACE,
                    ]
                )

                try:
                    detailed_run = client.runs.read_with_options(
                        latest_run.id, read_options
                    )

                    print(f"Run ID: {detailed_run.id}")
                    print(f"Status: {detailed_run.status}")
                    print(f"Source: {detailed_run.source}")
                    print(f"Message: {detailed_run.message}")
                    print(f"Created: {detailed_run.created_at}")
                    print(f"Auto Apply: {detailed_run.auto_apply}")
                    print(f"Plan Only: {detailed_run.plan_only}")
                    print(f"Position in Queue: {detailed_run.position_in_queue}")

                    if detailed_run.actions:
                        print("\nAvailable Actions:")
                        print(f"  Can Apply: {detailed_run.actions.is_confirmable}")
                        print(f"  Can Cancel: {detailed_run.actions.is_cancelable}")
                        print(f"  Can Discard: {detailed_run.actions.is_discardable}")
                        print(
                            f"  Can Force Cancel: {detailed_run.actions.is_force_cancelable}"
                        )

                    if detailed_run.created_by:
                        print(f"\nCreated by: {detailed_run.created_by.username}")

                except Exception as e:
                    print(f"Error reading run details: {e}")

        # 3) Optionally create a new run
        if args.create_run:
            _print_header("Creating a new plan-only run")

            try:
                # Get workspace object - convert to the model type expected by run
                workspace_data = client.workspaces.read_by_id(args.workspace_id)

                # Create the workspace object that run models expect
                from tfe.models.workspace import Workspace

                workspace = Workspace(
                    id=workspace_data.id,
                    name=workspace_data.name,
                    organization=workspace_data.organization,
                    execution_mode=workspace_data.execution_mode,
                    project_id=workspace_data.project_id,
                    tags=getattr(workspace_data, "tags", []),
                )

                # Create run with some example variables
                variables = [
                    RunVariable(key="environment", value="demo"),
                    RunVariable(key="instance_type", value="t3.micro"),
                ]

                create_options = RunCreateOptions(
                    workspace=workspace,
                    plan_only=True,
                    message=f"Demo run created by python-tfe SDK at {datetime.now()}",
                    variables=variables,
                )

                new_run = client.runs.create(args.workspace_id, create_options)

                print(f"Created new run: {new_run.id}")
                print(f"Status: {new_run.status}")
                print(f"Message: {new_run.message}")
                print(f"Variables: {len(variables)} variables passed")
                print(f"Plan Only: {new_run.plan_only}")

            except Exception as e:
                print(f"Error creating run: {e}")
                import traceback

                traceback.print_exc()

    # 4) Organization-level listing (if organization provided)
    if args.organization:
        _print_header(f"Listing runs across organization: {args.organization}")

        try:
            org_options = RunListForOrganizationOptions(
                page_number=args.page,
                page_size=5,  # Smaller for demo
                status="applied,planned,errored",
            )

            org_runs = client.runs.list_for_organization(args.organization, org_options)
            print(f"Found {len(org_runs.items)} runs across organization")

            for run in org_runs.items[:3]:  # Show first 3
                print(f"- {run.id} | status={run.status}")
                if run.workspace:
                    print(f"  workspace: {run.workspace.name}")

        except Exception as e:
            print(f"Error listing organization runs: {e}")

    # 5) Demonstrate run actions (safe mode - show but don't execute)
    if args.run_actions and args.workspace_id:
        _print_header("Run Actions Demo (Safe Mode)")

        # Get runs first if not already available
        if "run_list" not in locals() or not run_list.items:
            try:
                options = RunListOptions(page_size=1)
                run_list = client.runs.list(args.workspace_id, options)
            except Exception as e:
                print(f"Error getting runs for actions demo: {e}")
                return

        if not run_list.items:
            print("No runs available for actions demo")
            return

        demo_run = run_list.items[0]
        print(f"Demonstrating actions for run: {demo_run.id}")
        print(f"Current status: {demo_run.status}")

        # Show basic read (without options)
        print("\n1. Basic read():")
        try:
            basic_run = client.runs.read(demo_run.id)
            print(f"   Read run {basic_run.id} - status: {basic_run.status}")
        except Exception as e:
            print(f"   Error: {e}")

        # Show action methods (but don't execute them for safety)
        print("\n2. Available action methods (not executed):")
        print("   # Apply run:")
        print(
            f"   # client.runs.apply('{demo_run.id}', RunApplyOptions(comment='Applied via SDK'))"
        )

        print("   # Cancel run:")
        print(
            f"   # client.runs.cancel('{demo_run.id}', RunCancelOptions(comment='Canceled via SDK'))"
        )

        print("   # Force cancel run:")
        print(
            f"   # client.runs.force_cancel('{demo_run.id}', RunForceCancelOptions(comment='Force canceled'))"
        )

        print("   # Discard run:")
        print(
            f"   # client.runs.discard('{demo_run.id}', RunDiscardOptions(comment='Discarded via SDK'))"
        )

        print("   # Force execute run:")
        print(f"   # client.runs.force_execute('{demo_run.id}')")

        print("\n   Note: These actions are commented out for safety.")
        print("   Uncomment and use them carefully in your own code.")


if __name__ == "__main__":
    main()
