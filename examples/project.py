"""
Real-time Project SDK Integration Example

This example demonstrates how to use the TFE Python SDK for project operations
with real API calls. This is NOT a unit test - it uses the actual SDK client
to perform CRUD operations on real projects.

Setup Instructions:
1. Set environment variables:
   export TFE_TOKEN="your-api-token-here"
   export TFE_ORG="your-test-organization-name"
2. Run the example:
   python examples/project.py

Important Notes:
- This makes real API calls and creates/deletes actual resources
- Always use a dedicated test organization, never production
- Resources are automatically cleaned up after demonstration
"""

import os
import uuid

from tfe import TFEClient
from tfe.models.project import (
    ProjectCreateOptions,
    ProjectListOptions,
    ProjectUpdateOptions,
)


def project_sdk_example():
    """Demonstrate Project SDK operations with real API calls."""

    # Initialize SDK client
    token = os.getenv("TFE_TOKEN")
    org_name = os.getenv("TFE_ORG")

    if not token or not org_name:
        print("❌ Please set TFE_TOKEN and TFE_ORG environment variables")
        print("   export TFE_TOKEN='your-hcp-terraform-token'")
        print("   export TFE_ORG='your-organization-name'")
        return

    print("🚀 TFE Python SDK - Project Operations Example")
    print("=" * 50)
    print(f"🔧 Organization: {org_name}")
    print(f"🔧 Token: {token[:10]}...")

    # Create SDK client
    client = TFEClient()

    unique_id = str(uuid.uuid4())[:8]
    test_project_name = f"sdk-example-{unique_id}"
    test_description = f"SDK example project created at {unique_id}"
    project_id = None

    try:
        print("\n1️⃣ LIST: Getting existing projects...")
        # List existing projects
        existing_projects = list(client.projects.list(org_name))
        print(f"✅ Found {len(existing_projects)} existing projects")

        if existing_projects:
            print("📋 Example existing projects:")
            for i, project in enumerate(existing_projects[:3]):  # Show first 3
                print(f"   - {project.name} (ID: {project.id})")
                if i == 2 and len(existing_projects) > 3:
                    print(f"   ... and {len(existing_projects) - 3} more")

        print(f"\n2️⃣ CREATE: Creating new project '{test_project_name}'...")
        # Create a new project
        create_options = ProjectCreateOptions(
            name=test_project_name, description=test_description
        )
        created_project = client.projects.create(org_name, create_options)
        project_id = created_project.id

        print("✅ Project created successfully!")
        print(f"   ID: {created_project.id}")
        print(f"   Name: {created_project.name}")
        print(f"   Description: {created_project.description}")
        print(f"   Organization: {created_project.organization}")
        print(f"   Created: {created_project.created_at}")

        print("\n3️⃣ READ: Reading project details...")
        # Read the created project
        read_project = client.projects.read(project_id)
        print("✅ Project read successfully:")
        print(f"   Name: {read_project.name}")
        print(f"   Workspace Count: {read_project.workspace_count}")
        print(f"   Updated: {read_project.updated_at}")

        print("\n4️⃣ UPDATE: Updating project...")
        # Update the project
        updated_name = f"sdk-updated-{unique_id}"
        updated_description = f"SDK example project updated at {unique_id}"
        update_options = ProjectUpdateOptions(
            name=updated_name, description=updated_description
        )
        updated_project = client.projects.update(project_id, update_options)

        print("✅ Project updated successfully!")
        print(f"   New Name: {updated_project.name}")
        print(f"   New Description: {updated_project.description}")

        print("\n5️⃣ LIST WITH OPTIONS: Testing list with pagination...")
        # Test list with options
        list_options = ProjectListOptions(page_size=5)
        projects_with_options = list(client.projects.list(org_name, list_options))
        print(f"✅ List with options returned {len(projects_with_options)} projects")

        # Verify our updated project appears in the list
        found_project = None
        for project in projects_with_options:
            if project.id == project_id:
                found_project = project
                break

        if found_project:
            print(f"✅ Confirmed updated project appears in list: {found_project.name}")
        else:
            print("⚠️  Updated project not found in list (may be on another page)")

        print("\n6️⃣ DELETE: Cleaning up created project...")
        # Delete the project
        client.projects.delete(project_id)
        print("✅ Project deleted successfully!")

        # Verify deletion
        print("🔍 Verifying project deletion...")
        try:
            client.projects.read(project_id)
            print("❌ Warning: Project still exists after deletion")
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                print("✅ Confirmed: Project successfully deleted")
            else:
                print(f"⚠️  Unexpected error during verification: {e}")

        project_id = None  # Clear since deleted

        print("\n🎉 Project SDK Example Completed Successfully!")
        print("=" * 50)
        print("✅ All CRUD operations (Create, Read, Update, Delete) working")
        print("✅ SDK client properly configured and functional")
        print("✅ Real API integration successful")

    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        print("🔧 Check your TFE_TOKEN and TFE_ORG environment variables")
        print("🔧 Ensure your token has proper permissions for project operations")

    finally:
        # Emergency cleanup if something went wrong
        if project_id:
            try:
                print(f"\n🧹 Emergency cleanup: Deleting project {project_id}")
                client.projects.delete(project_id)
                print("✅ Emergency cleanup successful")
            except Exception as cleanup_error:
                print(
                    f"⚠️  Warning: Failed to clean up project {project_id}: {cleanup_error}"
                )


def demonstrate_error_handling():
    """Demonstrate proper error handling with the SDK."""

    print("\n🚫 Error Handling Demonstration")
    print("-" * 30)

    token = os.getenv("TFE_TOKEN")
    org_name = os.getenv("TFE_ORG")

    if not token or not org_name:
        print("❌ Skipping error handling demo - environment variables not set")
        return

    client = TFEClient()

    # Test reading a non-existent project
    print("🔍 Testing error handling for non-existent project...")
    try:
        fake_project_id = "prj-nonexistent123456789"
        client.projects.read(fake_project_id)
        print("❌ Unexpected: Should have failed for non-existent project")
    except Exception as e:
        print(f"✅ Correctly handled error: {type(e).__name__}")
        print(f"   Message: {str(e)[:100]}...")

    print("✅ Error handling demonstration complete")


def main():
    """Main function to run all examples."""
    print("🧪 TFE Python SDK Project Examples")
    print("This demonstrates real SDK usage with actual API calls\n")

    # Run main project operations example
    project_sdk_example()

    # Run error handling demonstration
    demonstrate_error_handling()


if __name__ == "__main__":
    main()
