#!/usr/bin/env python3
"""
Complete OAuth Client Testing Suite

This file contains individual tests for all 8 OAuth client functions:

PUBLIC FUNCTIONS AVAILABLE FOR TESTING:
1. list() - List all OAuth clients for an organization
2. create() - Create OAuth client with VCS provider connection
3. read() - Read an OAuth client by ID
4. read_with_options() - Read OAuth client with include options
5. update() - Update an existing OAuth client
6. delete() - Delete an OAuth client
7. add_projects() - Add projects to an OAuth client
8. remove_projects() - Remove projects from an OAuth client

USAGE:
- Uncomment specific test sections to test individual functions
- Tests require valid TFE credentials and organization access
- Some tests require existing projects in your organization
- GitHub token required for creating GitHub OAuth clients
- Modify test data (organization, tokens, etc.) as needed for your environment

REQUIREMENTS:
- Set TFE_ADDRESS and TFE_TOKEN environment variables
- Set OAUTH_CLIENT_GITHUB_TOKEN environment variable for GitHub tests
- Ensure you have organization access and proper permissions
"""

import os
import random
import sys
import time

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pytfe import TFEClient, TFEConfig
from pytfe.errors import NotFound
from pytfe.models import (
    OAuthClientAddProjectsOptions,
    OAuthClientCreateOptions,
    OAuthClientIncludeOpt,
    OAuthClientListOptions,
    OAuthClientReadOptions,
    OAuthClientRemoveProjectsOptions,
    OAuthClientUpdateOptions,
    ServiceProviderType,
)


def main():
    """Test all OAuth client functions individually."""

    print("=" * 80)
    print("OAUTH CLIENT COMPLETE TESTING SUITE")
    print("=" * 80)
    print("Testing ALL 8 functions in src/tfe/resources/oauth_client.py")
    print("Comprehensive test coverage for all OAuth client operations")
    print("=" * 80)

    # Initialize the TFE client
    client = TFEClient(TFEConfig.from_env())
    organization_name = "aayush-test"  # Replace with your organization

    # Variables to store created resources for dependent tests
    created_oauth_client = None
    test_projects = []

    # Check for required environment variables
    github_token = os.getenv("OAUTH_CLIENT_GITHUB_TOKEN")
    if not github_token:
        print(
            "\n WARNING: OAUTH_CLIENT_GITHUB_TOKEN not set. GitHub-related tests will be skipped."
        )
        print(
            "Set this environment variable to test OAuth client creation with GitHub."
        )

    # =====================================================
    # TEST 1: LIST OAUTH CLIENTS
    # =====================================================
    print("\n" + "=" * 60)
    print("TEST 1: list() - List all OAuth clients for organization")
    print("=" * 60)

    try:
        print(f"Listing OAuth clients for organization: {organization_name}")

        # Test basic list without options
        oauth_clients = list(client.oauth_clients.list(organization_name))
        print(f"Found {len(oauth_clients)} OAuth clients")

        for i, oauth_client in enumerate(oauth_clients[:3], 1):
            print(f"{i}. {oauth_client.id} - {oauth_client.service_provider}")
            if oauth_client.name:
                print(f"Name: {oauth_client.name}")
            print(f"Service Provider: {oauth_client.service_provider_name}")

        # Test list with options
        if len(oauth_clients) > 0:
            print("\nTesting list() with options:")
            options = OAuthClientListOptions(
                include=[
                    OAuthClientIncludeOpt.OAUTH_TOKENS,
                    OAuthClientIncludeOpt.PROJECTS,
                ],
                page_size=10,
            )
            oauth_clients_with_options = list(
                client.oauth_clients.list(organization_name, options)
            )
            print(f"Found {len(oauth_clients_with_options)} OAuth clients with options")

            if oauth_clients_with_options:
                first_client = oauth_clients_with_options[0]
                print(
                    f"First client includes - OAuth Tokens: {len(first_client.oauth_tokens or [])}"
                )
                print(
                    f"                         - Projects: {len(first_client.projects or [])}"
                )

    except Exception as e:
        print(f"Error listing OAuth clients: {e}")

    # =====================================================
    # TEST 2: CREATE OAUTH CLIENT
    # =====================================================
    print("\n" + "=" * 60)
    print("TEST 2: create() - Create OAuth client with VCS provider")
    print("=" * 60)

    if github_token:
        try:
            unique_suffix = f"{int(time.time())}-{random.randint(1000, 9999)}"
            client_name = f"test-github-client-{unique_suffix}"

            print(f"Creating GitHub OAuth client: {client_name}")

            create_options = OAuthClientCreateOptions(
                name=client_name,
                api_url="https://api.github.com",
                http_url="https://github.com",
                oauth_token=github_token,
                service_provider=ServiceProviderType.GITHUB,
                organization_scoped=True,
            )

            created_oauth_client = client.oauth_clients.create(
                organization_name, create_options
            )
            print(f"Created OAuth client: {created_oauth_client.id}")
            print(f"Name: {created_oauth_client.name}")
            print(f"Service Provider: {created_oauth_client.service_provider}")
            print(f"API URL: {created_oauth_client.api_url}")
            print(f"HTTP URL: {created_oauth_client.http_url}")
            print(f"Organization Scoped: {created_oauth_client.organization_scoped}")

        except Exception as e:
            print(f"Error creating OAuth client: {e}")
    else:
        print("Skipped - OAUTH_CLIENT_GITHUB_TOKEN not set")

    # =====================================================
    # TEST 3: READ OAUTH CLIENT
    # =====================================================
    print("\n" + "=" * 60)
    print("TEST 3: read() - Read OAuth client by ID")
    print("=" * 60)

    if created_oauth_client:
        try:
            print(f"Reading OAuth client: {created_oauth_client.id}")

            read_oauth_client = client.oauth_clients.read(created_oauth_client.id)
            print(f"Read OAuth client: {read_oauth_client.id}")
            print(f"Name: {read_oauth_client.name}")
            print(f"Service Provider: {read_oauth_client.service_provider}")
            print(f"Created At: {read_oauth_client.created_at}")
            print(f"Callback URL: {read_oauth_client.callback_url}")
            print(f"Connect Path: {read_oauth_client.connect_path}")

        except Exception as e:
            print(f"Error reading OAuth client: {e}")
    else:
        # Try to read an existing OAuth client if no client was created
        try:
            oauth_clients = list(client.oauth_clients.list(organization_name))
            if oauth_clients:
                test_client = oauth_clients[0]
                print(f"Reading existing OAuth client: {test_client.id}")

                read_oauth_client = client.oauth_clients.read(test_client.id)
                print(f"Read existing OAuth client: {read_oauth_client.id}")
                print(f"Service Provider: {read_oauth_client.service_provider}")
            else:
                print("No existing OAuth clients found to test read()")
        except Exception as e:
            print(f"Error reading existing OAuth client: {e}")

    # =====================================================
    # TEST 4: READ OAUTH CLIENT WITH OPTIONS
    # =====================================================
    print("\n" + "=" * 60)
    print("TEST 4: read_with_options() - Read OAuth client with includes")
    print("=" * 60)

    target_client = created_oauth_client
    if not target_client:
        # Try to use an existing client
        try:
            oauth_clients = list(client.oauth_clients.list(organization_name))
            if oauth_clients:
                target_client = oauth_clients[0]
        except Exception:
            pass

    if target_client:
        try:
            print(f"Reading OAuth client with options: {target_client.id}")

            read_options = OAuthClientReadOptions(
                include=[
                    OAuthClientIncludeOpt.OAUTH_TOKENS,
                    OAuthClientIncludeOpt.PROJECTS,
                ]
            )

            read_oauth_client = client.oauth_clients.read_with_options(
                target_client.id, read_options
            )
            print(f"Read OAuth client with options: {read_oauth_client.id}")
            print(f"OAuth Tokens: {len(read_oauth_client.oauth_tokens or [])}")
            print(f"Projects: {len(read_oauth_client.projects or [])}")

            if read_oauth_client.oauth_tokens:
                print(" OAuth Token details:")
                for i, token in enumerate(read_oauth_client.oauth_tokens[:2], 1):
                    if isinstance(token, dict):
                        print(f"{i}. Token ID: {token.get('id', 'N/A')}")

        except Exception as e:
            print(f"Error reading OAuth client with options: {e}")
    else:
        print("No OAuth client available to test read_with_options()")

    # =====================================================
    # TEST 5: UPDATE OAUTH CLIENT
    # =====================================================
    print("\n" + "=" * 60)
    print("TEST 5: update() - Update existing OAuth client")
    print("=" * 60)

    if created_oauth_client:
        try:
            print(f"Updating OAuth client: {created_oauth_client.id}")

            update_options = OAuthClientUpdateOptions(
                name=f"{created_oauth_client.name}-updated",
                organization_scoped=False,  # Toggle the organization scoped setting
            )

            updated_oauth_client = client.oauth_clients.update(
                created_oauth_client.id, update_options
            )
            print(f"Updated OAuth client: {updated_oauth_client.id}")
            print(f"Updated Name: {updated_oauth_client.name}")
            print(
                f"     Updated Organization Scoped: {updated_oauth_client.organization_scoped}"
            )

            # Update our reference
            created_oauth_client = updated_oauth_client

        except Exception as e:
            print(f"Error updating OAuth client: {e}")
    else:
        print("No OAuth client created to test update()")

    # =====================================================
    # TEST 6: PREPARE TEST PROJECTS (for project operations)
    # =====================================================
    print("\n" + "=" * 60)
    print("PREPARATION: Getting projects for project operations tests")
    print("=" * 60)

    try:
        # Try to get some existing projects
        projects = list(client.projects.list(organization_name))
        if projects:
            # Use first 2 projects for testing
            test_projects = [
                {"type": "projects", "id": project.id} for project in projects[:2]
            ]
            print(
                f"    Found {len(projects)} projects, using {len(test_projects)} for testing:"
            )
            for i, project_ref in enumerate(test_projects, 1):
                corresponding_project = projects[i - 1]
                print(
                    f"     {i}. {corresponding_project.name} (ID: {project_ref['id']})"
                )
        else:
            print("No projects found - project operations tests will be skipped")

    except Exception as e:
        print(f"Error getting projects: {e}")

    # =====================================================
    # TEST 7: ADD PROJECTS TO OAUTH CLIENT
    # =====================================================
    print("\n" + "=" * 60)
    print("TEST 7: add_projects() - Add projects to OAuth client")
    print("=" * 60)

    if created_oauth_client and test_projects:
        try:
            print(f"Adding projects to OAuth client: {created_oauth_client.id}")
            print(f"Projects to add: {[p['id'] for p in test_projects]}")

            add_options = OAuthClientAddProjectsOptions(projects=test_projects)

            client.oauth_clients.add_projects(created_oauth_client.id, add_options)
            print(
                f"    Successfully added {len(test_projects)} projects to OAuth client"
            )

            # Verify the projects were added by reading the client with projects included
            read_options = OAuthClientReadOptions(
                include=[OAuthClientIncludeOpt.PROJECTS]
            )
            updated_client = client.oauth_clients.read_with_options(
                created_oauth_client.id, read_options
            )
            print(
                f"    Verification: OAuth client now has {len(updated_client.projects or [])} projects"
            )

        except Exception as e:
            print(f"Error adding projects to OAuth client: {e}")
    else:
        if not created_oauth_client:
            print("No OAuth client created to test add_projects()")
        if not test_projects:
            print("No projects available to test add_projects()")

    # =====================================================
    # TEST 8: REMOVE PROJECTS FROM OAUTH CLIENT
    # =====================================================
    print("\n" + "=" * 60)
    print("TEST 8: remove_projects() - Remove projects from OAuth client")
    print("=" * 60)

    if created_oauth_client and test_projects:
        try:
            print(f"Removing projects from OAuth client: {created_oauth_client.id}")
            print(f"Projects to remove: {[p['id'] for p in test_projects]}")

            remove_options = OAuthClientRemoveProjectsOptions(projects=test_projects)

            client.oauth_clients.remove_projects(
                created_oauth_client.id, remove_options
            )
            print(
                f"    Successfully removed {len(test_projects)} projects from OAuth client"
            )

            # Verify the projects were removed by reading the client with projects included
            read_options = OAuthClientReadOptions(
                include=[OAuthClientIncludeOpt.PROJECTS]
            )
            updated_client = client.oauth_clients.read_with_options(
                created_oauth_client.id, read_options
            )
            print(
                f"    Verification: OAuth client now has {len(updated_client.projects or [])} projects"
            )

        except Exception as e:
            print(f"Error removing projects from OAuth client: {e}")
    else:
        if not created_oauth_client:
            print("No OAuth client created to test remove_projects()")
        if not test_projects:
            print("No projects available to test remove_projects()")

    # =====================================================
    # TEST 9: DELETE OAUTH CLIENT
    # =====================================================
    print("\n" + "=" * 60)
    print("TEST 9: delete() - Delete OAuth client")
    print("=" * 60)

    if created_oauth_client:
        try:
            print(f"Deleting OAuth client: {created_oauth_client.id}")

            # First, let's confirm it exists
            try:
                client.oauth_clients.read(created_oauth_client.id)
                print("Confirmed OAuth client exists before deletion")
            except NotFound:
                print("OAuth client not found before deletion attempt")

            # Delete the OAuth client
            client.oauth_clients.delete(created_oauth_client.id)
            print(f"Successfully deleted OAuth client: {created_oauth_client.id}")

            # Verify deletion by trying to read it
            try:
                client.oauth_clients.read(created_oauth_client.id)
                print("Warning: OAuth client still exists after deletion")
            except NotFound:
                print("Verification: OAuth client successfully deleted (not found)")
            except Exception as e:
                print(f"? Verification error: {e}")

        except Exception as e:
            print(f"Error deleting OAuth client: {e}")
    else:
        print("No OAuth client created to test delete()")

    # =====================================================
    # SUMMARY
    # =====================================================
    print("\n" + "=" * 80)
    print("OAUTH CLIENT TESTING COMPLETE")
    print("=" * 80)
    print("Functions tested:")
    print(" 1. list() - List OAuth clients for organization")
    print(" 2. create() - Create OAuth client with VCS provider")
    print(" 3. read() - Read OAuth client by ID")
    print(" 4. read_with_options() - Read OAuth client with includes")
    print(" 5. update() - Update existing OAuth client")
    print(" 6. add_projects() - Add projects to OAuth client")
    print(" 7. remove_projects() - Remove projects from OAuth client")
    print(" 8. delete() - Delete OAuth client")
    print("\nAll OAuth client functions have been tested!")
    print("Check the output above for any errors or warnings.")
    print("=" * 80)


if __name__ == "__main__":
    main()
