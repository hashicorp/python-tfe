#!/usr/bin/env python3
"""
Organization Tags Management Example

This example demonstrates all available organization tags operations in the Python TFE SDK,
including list, delete, and add workspaces operations.

Usage:
    python examples/organization_tags.py

Requirements:
    - TFE_TOKEN environment variable set
    - TFE_ADDRESS environment variable set (optional, defaults to Terraform Cloud)
    - An existing organization in your Terraform Cloud/Enterprise instance
    - At least one workspace for testing workspace associations

Organization Tags Operations Demonstrated:
    1. List all organization tags
    2. List tags with filtering and pagination
    3. Add workspaces to a tag
    4. Delete organization tags
"""

import os

from pytfe import TFEClient, TFEConfig
from pytfe.models import (
    AddWorkspacesToTagOptions,
    OrganizationTagsDeleteOptions,
    OrganizationTagsListOptions,
)


def test_list_organization_tags(client, organization_name):
    """Test listing organization tags with various options."""
    print("=== Testing Organization Tags List Operations ===")

    # 1. List all organization tags
    print("\n1. Listing All Organization Tags:")
    try:
        tags = list(client.organization_tags.list(organization_name))
        print(f"   Found {len(tags)} organization tags")
        if tags:
            for tag in tags[:5]:  # Show first 5
                print(f"     - {tag.name} (ID: {tag.id})")
                print(f"       Workspaces: {tag.instance_count}")
                print(f"       Created: {tag.created_at}")
    except Exception as e:
        print(f"   Error: {e}")
        return []

    # 2. List with pagination
    print("\n2. Listing Tags with Pagination:")
    try:
        options = OrganizationTagsListOptions(page_number=1, page_size=10)
        tags_page = list(client.organization_tags.list(organization_name, options))
        print(f"   Page 1 has {len(tags_page)} tags")
    except Exception as e:
        print(f"   Error: {e}")

    # 3. List with filters
    print("\n3. Listing Tags with Filter:")
    try:
        # Filter tags by name pattern
        options = OrganizationTagsListOptions(
            filter="prod",  # Filters by workspace name containing pattern
            page_size=20,
        )
        filtered_tags = list(
            client.organization_tags.list(organization_name, options)
        )
        print(f"   Found {len(filtered_tags)} tags matching filter 'prod'")
        for tag in filtered_tags[:3]:
            print(f"     - {tag.name}")
    except Exception as e:
        print(f"   Error: {e}")

    # 4. List with query search
    print("\n4. Listing Tags with Query Search:")
    try:
        # Search tags by name
        options = OrganizationTagsListOptions(
            query="production",
            page_size=20,
        )
        search_tags = list(client.organization_tags.list(organization_name, options))
        print(f"   Found {len(search_tags)} tags matching query 'production'")
        for tag in search_tags[:3]:
            print(f"     - {tag.name}")
    except Exception as e:
        print(f"   Error: {e}")

    return tags


def test_add_workspaces_to_tag(client, tag_id, workspace_ids):
    """Test adding workspaces to an organization tag."""
    print("\n=== Testing Add Workspaces to Tag ===")

    if not tag_id:
        print("   No tag ID provided, skipping test")
        return

    if not workspace_ids:
        print("   No workspace IDs provided, skipping test")
        return

    print(f"\n1. Adding {len(workspace_ids)} workspace(s) to tag {tag_id}:")
    try:
        options = AddWorkspacesToTagOptions(workspace_ids=workspace_ids)
        client.organization_tags.add_workspaces(tag_id, options)
        print("   Successfully added workspace(s) to tag")
        for ws_id in workspace_ids:
            print(f"     - {ws_id}")
    except Exception as e:
        print(f"   Error: {e}")


def test_delete_organization_tags(client, organization_name, tag_ids):
    """Test deleting organization tags."""
    print("\n=== Testing Organization Tags Delete Operations ===")

    if not tag_ids:
        print("   No tag IDs provided, skipping test")
        return

    print(f"\n1. Deleting {len(tag_ids)} tag(s):")
    try:
        options = OrganizationTagsDeleteOptions(ids=tag_ids)
        client.organization_tags.delete(organization_name, options)
        print("   Successfully deleted tag(s)")
        for tag_id in tag_ids:
            print(f"     - {tag_id}")
    except Exception as e:
        print(f"   Error: {e}")


def get_workspace_ids(client, organization_name, limit=2):
    """Helper function to get workspace IDs for testing."""
    try:
        workspaces = list(client.workspaces.list(organization_name))
        if workspaces:
            return [ws.id for ws in workspaces[:limit]]
    except Exception:
        pass
    return []


def main():
    """Main function to demonstrate all organization tags operations."""
    print("\n" + "=" * 70)
    print("Organization Tags Management Example")
    print("=" * 70)

    # Initialize client
    token = os.getenv("TFE_TOKEN")
    if not token:
        print("\nError: TFE_TOKEN environment variable not set")
        return

    address = os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    config = TFEConfig(address=address, token=token)
    client = TFEClient(config)

    # Get organization from environment or use default
    organization_name = os.getenv("TFE_ORGANIZATION", "aayush-test")
    print(f"\nOrganization: {organization_name}")
    print(f"API Address: {address}")
    print("-" * 70)

    # Test listing organization tags
    tags = test_list_organization_tags(client, organization_name)

    # Get workspace IDs for testing
    workspace_ids = get_workspace_ids(client, organization_name)
    if workspace_ids:
        print(f"\nFound {len(workspace_ids)} workspace(s) for testing:")
        for ws_id in workspace_ids:
            print(f"  - {ws_id}")

    # Test adding workspaces to a tag (if tag exists)
    if tags and workspace_ids:
        test_tag_id = tags[0].id
        print(f"\nUsing tag: {tags[0].name} ({test_tag_id})")
        test_add_workspaces_to_tag(client, test_tag_id, workspace_ids)

    # Note: Delete operation is commented out to prevent accidental deletion
    # Uncomment the following lines if you want to test tag deletion
    """
    # Test deleting organization tags
    if tags:
        # Delete only tags created for testing (be careful!)
        test_tag_ids = [tag.id for tag in tags if "test" in tag.name.lower()]
        if test_tag_ids:
            print(f"\nFound {len(test_tag_ids)} test tag(s) to delete")
            test_delete_organization_tags(client, organization_name, test_tag_ids)
        else:
            print("\nNo test tags found to delete (tags with 'test' in name)")
    """

    print("\n" + "=" * 70)
    print("Organization Tags Management Example Complete")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
