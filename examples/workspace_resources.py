"""Example script for working with workspace resources in Terraform Enterprise.

This script demonstrates how to list resources within a workspace.
"""

import argparse
import sys

from pytfe import TFEClient
from pytfe.models import WorkspaceResourceListOptions


def list_workspace_resources(
    client: TFEClient,
    workspace_id: str,
    page_number: int | None = None,
    page_size: int | None = None,
) -> None:
    """List all resources in a workspace."""
    try:
        print(f"Listing resources for workspace: {workspace_id}")

        # Prepare list options
        options = None
        if page_number or page_size:
            options = WorkspaceResourceListOptions()
            if page_number:
                options.page_number = page_number
            if page_size:
                options.page_size = page_size

        # List workspace resources (returns an iterator)
        resources = list(client.workspace_resources.list(workspace_id, options))

        if not resources:
            print("No resources found in this workspace.")
            return

        print(f"\nFound {len(resources)} resource(s):")
        print("-" * 80)

        for resource in resources:
            print(f"ID: {resource.id}")
            print(f"Address: {resource.address}")
            print(f"Name: {resource.name}")
            print(f"Module: {resource.module}")
            print(f"Provider: {resource.provider}")
            print(f"Provider Type: {resource.provider_type}")
            print(f"Created At: {resource.created_at}")
            print(f"Updated At: {resource.updated_at}")
            print(f"Modified By State Version: {resource.modified_by_state_version_id}")
            if resource.name_index:
                print(f"Name Index: {resource.name_index}")
            print("-" * 80)

    except Exception as e:
        print(f"Error listing workspace resources: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function to handle command line arguments and execute operations."""
    parser = argparse.ArgumentParser(
        description="Manage workspace resources in Terraform Enterprise",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all resources in a workspace
  python workspace_resources.py --list --workspace-id ws-abc123

  # List with pagination
  python workspace_resources.py --list --workspace-id ws-abc123 --page-number 2 --page-size 50

Environment variables:
  TFE_TOKEN: Your Terraform Enterprise API token
  TFE_URL: Your Terraform Enterprise URL (default: https://app.terraform.io)
  TFE_ORG: Your Terraform Enterprise organization name
        """,
    )

    # Add command flags
    parser.add_argument("--list", action="store_true", help="List workspace resources")
    parser.add_argument(
        "--workspace-id",
        required=True,
        help="ID of the workspace (required, e.g., ws-abc123)",
    )
    parser.add_argument("--page-number", type=int, help="Page number for pagination")
    parser.add_argument("--page-size", type=int, help="Page size for pagination")

    args = parser.parse_args()

    if not args.list:
        parser.print_help()
        sys.exit(1)

    # Initialize TFE client
    try:
        client = TFEClient()
    except Exception as e:
        print(f"Error initializing TFE client: {e}", file=sys.stderr)
        print(
            "Make sure TFE_TOKEN and TFE_URL environment variables are set.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Execute the list command
    list_workspace_resources(
        client,
        args.workspace_id,
        args.page_number,
        args.page_size,
    )


if __name__ == "__main__":
    main()
