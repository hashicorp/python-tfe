"""
Integration Test Example for python-tfe

This file demonstrates how to create integration tests that work with real HCP Terraform API.
These tests create and delete actual resources, so use with caution!

Setup Instructions:
1. Create a test organization in HCP Terraform (https://app.terraform.io)
2. Generate an organization or user API token with appropriate permissions
3. Set environment variables:
   export TFE_TOKEN="your-api-token-here"
   export TFE_ORG="your-test-organization-name"
4. Copy this file to your tests directory:
   cp examples/integration_test_example.py tests/test_integration_local.py
5. Run the tests:
   pytest tests/test_integration_local.py -v -s

Important Notes:
- These tests make real API calls and create/delete actual resources
- Always use a dedicated test organization, never production
- Tests will fail if you don't have proper permissions
- Clean up is automatic, but verify resources are deleted after testing
"""

import os
import uuid

import pytest

from tfe._http import HTTPTransport
from tfe.config import TFEConfig
from tfe.resources.projects import Projects


@pytest.fixture
def integration_client():
    """Create a real Projects client for integration testing"""
    token = os.environ.get("TFE_TOKEN")
    org = os.environ.get("TFE_ORG")

    if not token:
        pytest.skip(
            "TFE_TOKEN environment variable is required. "
            "Get your token from HCP Terraform: Settings → API Tokens"
        )

    if not org:
        pytest.skip(
            "TFE_ORG environment variable is required. "
            "Use your organization name from HCP Terraform URL"
        )

    print(f"\n🔧 Testing against organization: {org}")
    print(f"🔧 Using token: {token[:10]}...")

    config = TFEConfig()

    try:
        transport = HTTPTransport(
            config.address,
            token,
            timeout=config.timeout,
            verify_tls=config.verify_tls,
            user_agent_suffix=None,
            max_retries=3,
            backoff_base=0.1,
            backoff_cap=1.0,
            backoff_jitter=True,
            http2=False,
            proxies=None,
            ca_bundle=None,
        )
    except Exception as e:
        pytest.fail(f"Failed to create HTTP transport: {e}")

    return Projects(transport), org


def test_list_projects_integration(integration_client):
    """Test listing projects in your HCP Terraform organization

    This is the safest test to run first - it only reads data.
    """
    projects, org = integration_client

    try:
        project_list = list(projects.list(org))
        print(f"✅ Found {len(project_list)} projects in organization '{org}'")

        assert isinstance(project_list, list)

        if project_list:
            project = project_list[0]
            assert hasattr(project, "id"), "Project should have an ID"
            assert hasattr(project, "name"), "Project should have a name"
            assert hasattr(project, "organization"), (
                "Project should have an organization"
            )
            print(f"📋 Example project: {project.name} (ID: {project.id})")
        else:
            print("📋 No projects found - this is normal for a new organization")

    except Exception as e:
        pytest.fail(
            f"Failed to list projects. Check your TFE_TOKEN and TFE_ORG. Error: {e}"
        )


def test_project_crud_integration(integration_client):
    """Test complete Create, Read, Update, Delete operations

    ⚠️  WARNING: This test creates and deletes real resources!
    Only run this in a test organization, never in production.
    """
    projects, org = integration_client

    # Generate unique names to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    test_name = f"integration-test-{unique_id}"
    updated_name = f"integration-test-{unique_id}-updated"
    project_id = None

    try:
        # CREATE - Test project creation
        print(f"🔨 Creating project: {test_name}")
        created_project = projects.create(org, test_name)

        assert created_project.name == test_name, (
            f"Expected name {test_name}, got {created_project.name}"
        )
        assert created_project.organization == org, (
            f"Expected org {org}, got {created_project.organization}"
        )
        assert created_project.id.startswith("prj-"), (
            f"Project ID should start with 'prj-', got {created_project.id}"
        )

        project_id = created_project.id
        print(f"✅ Created project: {project_id}")

        # READ - Test reading the created project
        print(f"📖 Reading project: {project_id}")
        read_project = projects.read(project_id)

        assert read_project.id == project_id, (
            f"Expected ID {project_id}, got {read_project.id}"
        )
        assert read_project.name == test_name, (
            f"Expected name {test_name}, got {read_project.name}"
        )
        print(f"✅ Successfully read project: {read_project.name}")

        # UPDATE - Test updating the project name
        print(f"✏️  Updating project name to: {updated_name}")
        updated_project = projects.update(project_id, updated_name)

        assert updated_project.id == project_id, (
            f"Project ID should remain {project_id}"
        )
        assert updated_project.name == updated_name, (
            f"Expected updated name {updated_name}, got {updated_project.name}"
        )
        print(f"✅ Successfully updated project: {updated_project.name}")

    except Exception as e:
        pytest.fail(f"CRUD operation failed: {e}")

    finally:
        # DELETE - Always clean up, even if tests fail
        if project_id:
            try:
                print(f"🗑️  Deleting test project: {project_id}")
                projects.delete(project_id)
                print("✅ Test project deleted successfully")
            except Exception as e:
                print(f"❌ Warning: Failed to clean up project {project_id}: {e}")
                print(
                    "   You may need to manually delete this project in HCP Terraform"
                )


def test_error_handling_integration(integration_client):
    """Test that the client handles API errors appropriately"""
    projects, org = integration_client

    # Test reading a non-existent project
    fake_project_id = "prj-nonexistent123456789"

    try:
        projects.read(fake_project_id)
        pytest.fail("Should have raised an exception for non-existent project")
    except Exception as e:
        print(
            f"✅ Correctly handled error for non-existent project: {type(e).__name__}"
        )
        # This should raise a NotFound or similar error
        assert "not found" in str(e).lower() or "404" in str(e)


if __name__ == "__main__":
    """
    You can also run this file directly for quick testing:

    export TFE_TOKEN="your-token"
    export TFE_ORG="your-org"
    python examples/integration_test_example.py
    """
    import sys

    token = os.environ.get("TFE_TOKEN")
    org = os.environ.get("TFE_ORG")

    if not token or not org:
        print("❌ Please set TFE_TOKEN and TFE_ORG environment variables")
        print("   export TFE_TOKEN='your-hcp-terraform-token'")
        print("   export TFE_ORG='your-organization-name'")
        sys.exit(1)

    print("🧪 Running integration tests directly...")
    print(
        "   For full pytest features, use: pytest examples/integration_test_example.py -v -s"
    )

    # Simple direct execution
    pytest.main([__file__, "-v", "-s"])
