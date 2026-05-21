# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Simple Agent Pool operations example with the TFE Python SDK.

This example demonstrates:
1. Agent Pool CRUD operations (Create, Read, Update, Delete)
2. Agent token creation and management
3. Workspace assignment using assign_to_workspaces and remove_from_workspaces
4. Project assignment using update_allowed_projects (Go SDK parity)
5. Dedicated relationship update methods: update_allowed_workspaces,
   update_allowed_projects, update_excluded_workspaces
6. Proper error handling

Make sure to set the following environment variables:
- TFE_TOKEN: Your Terraform Cloud/Enterprise API token
- TFE_ADDRESS: Your Terraform Cloud/Enterprise URL (optional, defaults to https://app.terraform.io)
- TFE_ORG: Your organization name
- TFE_WORKSPACE_ID: A workspace ID for testing workspace assignment (optional)
- TFE_PROJECT_ID: A project ID for testing project assignment (optional)

Usage:
    export TFE_TOKEN="your-token-here"
    export TFE_ORG="your-organization"
    python examples/agent_pool.py
"""

import os
import uuid

from pytfe import TFEClient, TFEConfig
from pytfe.errors import NotFound
from pytfe.models import (
    AgentPoolAllowedProjectsUpdateOptions,
    AgentPoolAllowedWorkspacePolicy,
    AgentPoolAllowedWorkspacesUpdateOptions,
    AgentPoolAssignToWorkspacesOptions,
    AgentPoolCreateOptions,
    AgentPoolExcludedWorkspacesUpdateOptions,
    AgentPoolListOptions,
    AgentPoolRemoveFromWorkspacesOptions,
    AgentPoolUpdateOptions,
    AgentTokenCreateOptions,
)


def main():
    """Main function demonstrating agent pool operations."""
    # Get environment variables
    token = os.environ.get("TFE_TOKEN")
    org = os.environ.get("TFE_ORG")
    address = os.environ.get("TFE_ADDRESS", "https://app.terraform.io")
    workspace_id = os.environ.get(
        "TFE_WORKSPACE_ID"
    )  # optional, for workspace assignment
    project_id = os.environ.get("TFE_PROJECT_ID")  # optional, for project assignment

    if not token:
        print("TFE_TOKEN environment variable is required")
        return 1

    if not org:
        print("TFE_ORG environment variable is required")
        return 1

    # Create TFE client
    config = TFEConfig(token=token, address=address)
    client = TFEClient(config=config)

    print(f"Connected to: {address}")
    print(f" Organization: {org}")

    try:
        # Example 1: List existing agent pools
        print("\n Listing existing agent pools...")
        list_options = AgentPoolListOptions(page_size=10)  # Optional parameters
        agent_pools = client.agent_pools.list(org, options=list_options)

        # Convert to list to get count and iterate
        pool_list = list(agent_pools)
        print(f"Found {len(pool_list)} agent pools:")
        for pool in pool_list:
            print(f"  - {pool.name} (ID: {pool.id}, Agents: {pool.agent_count})")

        # Example 2: Create a new agent pool
        print("\n Creating a new agent pool...")
        unique_name = f"sdk-example-pool-{uuid.uuid4().hex[:8]}"

        create_options = AgentPoolCreateOptions(
            name=unique_name,
            organization_scoped=True,  # Optional parameter
            allowed_workspace_policy=AgentPoolAllowedWorkspacePolicy.ALL_WORKSPACES,  # Optional
        )

        new_pool = client.agent_pools.create(org, create_options)
        print(f"Created agent pool: {new_pool.name} (ID: {new_pool.id})")

        # Example 3: Read the agent pool
        print("\n Reading agent pool details...")
        pool_details = client.agent_pools.read(new_pool.id)
        print(f"Name: {pool_details.name}")
        print(f"Organization Scoped: {pool_details.organization_scoped}")
        print(f"Policy: {pool_details.allowed_workspace_policy}")
        print(f"Agent Count: {pool_details.agent_count}")

        # Example 4: Update the agent pool
        print("\n Updating agent pool...")
        update_options = AgentPoolUpdateOptions(
            name=f"{unique_name}-updated",
            organization_scoped=False,  # Making this optional parameter different
        )

        updated_pool = client.agent_pools.update(new_pool.id, update_options)
        print(f"Updated agent pool name to: {updated_pool.name}")

        # Example 5: Workspace assignment
        # assign_to_workspaces sends PATCH /agent-pools/:id with relationships.allowed-workspaces
        # remove_from_workspaces sends PATCH /agent-pools/:id with relationships.excluded-workspaces
        if workspace_id:
            print("\n Assigning workspace to agent pool...")
            updated_pool = client.agent_pools.assign_to_workspaces(
                new_pool.id,
                AgentPoolAssignToWorkspacesOptions(workspace_ids=[workspace_id]),
            )
            print(f"  Assigned workspace {workspace_id} to pool {updated_pool.name}")

            print("\n Removing workspace from agent pool...")
            updated_pool = client.agent_pools.remove_from_workspaces(
                new_pool.id,
                AgentPoolRemoveFromWorkspacesOptions(workspace_ids=[workspace_id]),
            )
            print(f"  Removed workspace {workspace_id} from pool {updated_pool.name}")

            # Example 5b: Dedicated update methods
            # update_allowed_workspaces / update_excluded_workspaces send the
            # relationship array unconditionally — even an empty list — so they can
            # also CLEAR the relationship.
            print(
                "\n Using update_allowed_workspaces (dedicated, supports clearing)..."
            )
            updated_pool = client.agent_pools.update_allowed_workspaces(
                new_pool.id,
                AgentPoolAllowedWorkspacesUpdateOptions(workspace_ids=[workspace_id]),
            )
            print(
                f"  Set allowed-workspaces to [{workspace_id}] on pool {updated_pool.name}"
            )

            print("\n Clearing allowed-workspaces via update_allowed_workspaces...")
            updated_pool = client.agent_pools.update_allowed_workspaces(
                new_pool.id,
                AgentPoolAllowedWorkspacesUpdateOptions(workspace_ids=[]),
            )
            print(f"  Cleared allowed-workspaces on pool {updated_pool.name}")

            print(
                "\n Using update_excluded_workspaces (dedicated, supports clearing)..."
            )
            updated_pool = client.agent_pools.update_excluded_workspaces(
                new_pool.id,
                AgentPoolExcludedWorkspacesUpdateOptions(workspace_ids=[workspace_id]),
            )
            print(
                f"  Set excluded-workspaces to [{workspace_id}] on pool {updated_pool.name}"
            )
        else:
            print("\n Skipping workspace assignment (set TFE_WORKSPACE_ID to test)")

        # Example 5c: Project assignment (parity — AllowedProjects relationship)
        if project_id:
            print("\n Assigning project to agent pool (update_allowed_projects)...")
            updated_pool = client.agent_pools.update_allowed_projects(
                new_pool.id,
                AgentPoolAllowedProjectsUpdateOptions(project_ids=[project_id]),
            )
            print(
                f"  Set allowed-projects to [{project_id}] on pool {updated_pool.name}"
            )

            print("\n Clearing allowed-projects via update_allowed_projects...")
            updated_pool = client.agent_pools.update_allowed_projects(
                new_pool.id,
                AgentPoolAllowedProjectsUpdateOptions(project_ids=[]),
            )
            print(f"  Cleared allowed-projects on pool {updated_pool.name}")
        else:
            print("\n Skipping project assignment (set TFE_PROJECT_ID to test)")

        # Example 6: Create an agent token
        print("\n Creating agent token...")
        token_options = AgentTokenCreateOptions(
            description="SDK example token"  # Optional description
        )

        agent_token = client.agent_tokens.create(new_pool.id, token_options)
        print(f"Created agent token: {agent_token.id}")
        if agent_token.token:
            print(f"  Token (first 10 chars): {agent_token.token[:10]}...")

        # Example 7: List agent tokens
        print("\n Listing agent tokens...")
        tokens = client.agent_tokens.list(new_pool.id)

        # Convert to list to get count and iterate
        token_list = list(tokens)
        print(f"Found {len(token_list)} tokens:")
        for token in token_list:
            print(f"  - {token.description or 'No description'} (ID: {token.id})")

        # Example 8: Clean up - delete the token and pool
        print("\n Cleaning up...")
        client.agent_tokens.delete(agent_token.id)
        print("Deleted agent token")

        client.agent_pools.delete(new_pool.id)
        print("Deleted agent pool")

        print("\n Agent pool operations completed successfully!")
        return 0

    except NotFound as e:
        print(f" Resource not found: {e}")
        return 1
    except Exception as e:
        print(f" Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
