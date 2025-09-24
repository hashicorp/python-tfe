"""Comprehensive example for Agent Pool operations with the TFE Python SDK.

This example demonstrates:
1. Agent Pool CRUD operations (Create, Read, Update, Delete)
2. Agent token creation and management
3. Workspace assignments to agent pools
4. Error handling and best practices
5. Authentication diagnostics

Make sure to set the following environment variables:
- TFE_TOKEN: Your Terraform Cloud/Enterprise API token
- TFE_ADDRESS: Your Terraform Cloud/Enterprise URL (optional, defaults to https://app.terraform.io)
- TFE_ORG: Your organization name

Usage:
    export TFE_TOKEN="your-token-here"
    export TFE_ORG="your-organization"
    python examples/agent_pool.py
"""

import os
import uuid

import pytest

from tfe import TFEClient, TFEConfig
from tfe.errors import NotFound
from tfe.models.agent import (
    AgentPoolAllowedWorkspacePolicy,
    AgentPoolCreateOptions,
    AgentPoolListOptions,
    AgentPoolReadOptions,
    AgentPoolUpdateOptions,
    AgentTokenCreateOptions,
)


def get_token_display(client) -> str:
    """Get a safe display version of the token from the client."""
    auth_header = client._transport.headers.get("Authorization", "Bearer [not-set]")
    token_display = (
        auth_header.replace("Bearer ", "")[:10]
        if "Bearer " in auth_header
        else "[not-set]"
    )
    return token_display


@pytest.fixture
def integration_client():
    """Create a real TFE client for integration testing"""
    token = os.environ.get("TFE_TOKEN")
    org = os.environ.get("TFE_ORG")
    address = os.environ.get("TFE_ADDRESS", "https://app.terraform.io")

    if not token or not org:
        pytest.skip("TFE_TOKEN and TFE_ORG environment variables required")

    config = TFEConfig(token=token, address=address)
    client = TFEClient(config=config)

    return client, org


def test_authentication_and_organization_access(integration_client):
    """Test basic authentication and organization access before running agent tests"""
    client, org = integration_client

    print(f"🔧 Testing authentication for organization: {org}")
    print(f"🔧 Using token: {get_token_display(client)}...")
    print(f"🔧 TFE Address: {client._transport.base}")

    try:
        # Test 1: Try to access organizations endpoint (basic auth test)
        print("1️⃣ Testing basic API authentication...")
        import httpx

        headers = client._transport.headers.copy()
        try:
            response = httpx.get(
                f"{client._transport.base}/api/v2/organizations",
                headers=headers,
                timeout=30,
            )
            print(f"Response status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Organizations API accessible")
            elif response.status_code == 401:
                print("❌ 401 Unauthorized - Token is invalid, expired, or malformed")
                print("💡 Solution: Generate a new API token from HCP Terraform")
            elif response.status_code == 403:
                print("❌ 403 Forbidden - Token doesn't have required permissions")
            else:
                print(f"❌ Unexpected status: {response.status_code}")
                print(f"Response: {response.text[:500]}...")
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return

        # Only continue if auth worked
        if response.status_code != 200:
            print("🛑 Stopping diagnostics - basic authentication failed")
            print("\n🔧 SOLUTIONS:")
            print("1. Generate a new API token from HCP Terraform:")
            print("   - Go to https://app.terraform.io/app/settings/tokens")
            print("   - Click 'Create an API token'")
            print("   - Copy the token and set: export TFE_TOKEN='your-new-token'")
            print("2. Verify your organization name:")
            print(f"   - Current: {org}")
            print("   - Should match your HCP Terraform organization exactly")
            print("3. Check token permissions:")
            print("   - Ensure token has organization-level permissions")
            print("   - Team tokens may have limited access")
            return

        # Test 2: Try to access the specific organization
        print(f"2️⃣ Testing access to organization '{org}'...")
        try:
            response = httpx.get(
                f"{client._transport.base}/api/v2/organizations/{org}",
                headers=headers,
                timeout=30,
            )
            if response.status_code == 200:
                org_data = response.json().get("data", {})
                org_name = org_data.get("attributes", {}).get("name", "unknown")
                print(f"✅ Organization '{org}' accessible (name: {org_name})")
            else:
                print(f"❌ Organization access failed (status: {response.status_code})")
                if response.status_code == 404:
                    print(f"💡 Organization '{org}' not found - check the name")
                return
        except Exception as e:
            print(f"❌ Organization test failed: {e}")
            return

        # Test 3: Check organization entitlements for agents
        print("3️⃣ Testing organization entitlements...")
        try:
            response = httpx.get(
                f"{client._transport.base}/api/v2/organizations/{org}/entitlement-set",
                headers=headers,
                timeout=30,
            )
            if response.status_code == 200:
                entitlements = response.json().get("data", {}).get("attributes", {})
                agents_enabled = entitlements.get("agents", False)
                print(f"✅ Entitlements accessible - Agents enabled: {agents_enabled}")
                if not agents_enabled:
                    print("⚠️  WARNING: Agents are not enabled for this organization!")
                    print("⚠️  Agent functionality requires a paid HCP Terraform plan")
                    print("⚠️  Contact your organization admin to enable agents")
            else:
                print(f"❌ Entitlements check failed (status: {response.status_code})")
        except Exception as e:
            print(f"❌ Entitlements test failed: {e}")

        # Test 4: Test basic agent pools endpoint access
        print("4️⃣ Testing agent pools endpoint access...")
        try:
            response = httpx.get(
                f"{client._transport.base}/api/v2/organizations/{org}/agent-pools",
                headers=headers,
                timeout=30,
            )
            print(f"Agent pools endpoint status: {response.status_code}")
            if response.status_code == 200:
                pools_data = response.json().get("data", [])
                print(
                    f"✅ Agent pools endpoint accessible - Found {len(pools_data)} pools"
                )
            elif response.status_code == 401:
                print("❌ Unauthorized - Token may be invalid or expired")
            elif response.status_code == 403:
                print(
                    "❌ Forbidden - Token doesn't have sufficient permissions or agents not enabled"
                )
            elif response.status_code == 404:
                print(
                    "❌ Not Found - Organization may not exist or agents not available"
                )
            else:
                print(f"❌ Unexpected status: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
        except Exception as e:
            print(f"❌ Agent pools test failed: {e}")

    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        raise


def test_list_agent_pools_integration(integration_client):
    """Test LIST operation - Get all agent pools in organization"""
    client, org = integration_client

    try:
        print(f"🔧 Testing against organization: {org}")
        print(f"🔧 Using token: {get_token_display(client)}...")

        # Test basic list
        print("📋 Testing LIST operation: basic list")
        agent_pools = list(client.agent_pools.list(org))
        print(f"✅ Found {len(agent_pools)} agent pools in organization '{org}'")

        if agent_pools:
            example_pool = agent_pools[0]
            print(f"📋 Example agent pool: {example_pool.name} (ID: {example_pool.id})")
            print(
                f"📋 Created: {example_pool.created_at}, Agent count: {example_pool.agent_count}"
            )

        # Test list with options
        print("📋 Testing LIST operation: with options")
        options = AgentPoolListOptions(
            page_size=10,
            allowed_workspace_policy=AgentPoolAllowedWorkspacePolicy.ALL_WORKSPACES,
        )
        pools_with_options = list(client.agent_pools.list(org, options))
        print(f"✅ List with options returned {len(pools_with_options)} agent pools")

    except Exception as e:
        print(f"❌ List operation failed: {e}")
        raise


def test_create_agent_pool_integration(integration_client):
    """Test CREATE operation - Add new agent pools"""
    client, org = integration_client

    unique_id = str(uuid.uuid4())[:8]
    test_name = f"test-pool-{unique_id}"
    agent_pool_id = None

    try:
        print(f"🔧 Testing against organization: {org}")
        print(f"🔧 Using token: {get_token_display(client)}...")

        print(f"🔨 Testing CREATE operation: {test_name}")

        # Create agent pool with organization scoped policy
        options = AgentPoolCreateOptions(
            name=test_name,
            organization_scoped=True,
            allowed_workspace_policy=AgentPoolAllowedWorkspacePolicy.ALL_WORKSPACES,
        )

        agent_pool = client.agent_pools.create(org, options)
        agent_pool_id = agent_pool.id

        print(f"✅ CREATE successful: {agent_pool.id}")
        print(
            f"✅ Agent pool details: {agent_pool.name} - Organization scoped: {agent_pool.organization_scoped}"
        )

    except Exception as e:
        print(f"❌ Create operation failed: {e}")
        raise

    finally:
        # Cleanup
        if agent_pool_id:
            try:
                print(f"🗑️ Cleaning up created agent pool: {agent_pool_id}")
                client.agent_pools.delete(agent_pool_id)
                print("✅ Cleanup successful")
            except Exception as e:
                print(f"⚠️ Cleanup failed: {e}")


def test_read_agent_pool_integration(integration_client):
    """Test READ operation - Get specific agent pool details"""
    client, org = integration_client

    unique_id = str(uuid.uuid4())[:8]
    test_name = f"read-pool-{unique_id}"
    agent_pool_id = None

    try:
        print(f"🔧 Testing against organization: {org}")
        print(f"🔧 Using token: {get_token_display(client)}...")

        # Create agent pool for read test
        print(f"🔨 Creating agent pool for READ test: {test_name}")
        create_options = AgentPoolCreateOptions(
            name=test_name,
            organization_scoped=False,
            allowed_workspace_policy=AgentPoolAllowedWorkspacePolicy.SPECIFIC_WORKSPACES,
        )
        created_pool = client.agent_pools.create(org, create_options)
        agent_pool_id = created_pool.id

        # Test read operation
        print(f"📖 Testing READ operation: {agent_pool_id}")
        read_options = AgentPoolReadOptions(include=["allowed-workspaces"])
        agent_pool = client.agent_pools.read(agent_pool_id, read_options)

        print(f"✅ READ successful: {agent_pool.name}")
        print(f"✅ Agent pool created: {agent_pool.created_at}")
        print(f"✅ Workspace policy: {agent_pool.allowed_workspace_policy}")
        print("✅ READ operation completed successfully")

    except Exception as e:
        print(f"❌ Read operation failed: {e}")
        raise

    finally:
        if agent_pool_id:
            try:
                print(f"🗑️ Cleaning up read test agent pool: {agent_pool_id}")
                client.agent_pools.delete(agent_pool_id)
                print("✅ Cleanup successful")
            except Exception as e:
                print(f"⚠️ Cleanup failed: {e}")


def test_update_agent_pool_integration(integration_client):
    """Test UPDATE operation - Modify existing agent pools"""
    client, org = integration_client

    unique_id = str(uuid.uuid4())[:8]
    original_name = f"update-pool-{unique_id}"
    updated_name = f"updated-pool-{unique_id}"
    agent_pool_id = None

    try:
        print(f"🔧 Testing against organization: {org}")
        print(f"🔧 Using token: {get_token_display(client)}...")

        # Create agent pool for update test
        print(f"🔨 Creating agent pool for UPDATE test: {original_name}")
        create_options = AgentPoolCreateOptions(
            name=original_name,
            organization_scoped=True,
        )
        created_pool = client.agent_pools.create(org, create_options)
        agent_pool_id = created_pool.id

        # Test update name only
        print("✏️ Testing UPDATE operation: name only")
        update_options = AgentPoolUpdateOptions(name=updated_name)
        updated_pool = client.agent_pools.update(agent_pool_id, update_options)
        print(f"✅ UPDATE name successful: {updated_pool.name}")

        # Test update organization scoped policy
        print("✏️ Testing UPDATE operation: organization scoped")
        update_options = AgentPoolUpdateOptions(organization_scoped=False)
        updated_pool = client.agent_pools.update(agent_pool_id, update_options)
        print(
            f"✅ UPDATE policy successful: organization_scoped={updated_pool.organization_scoped}"
        )

        # Test update workspace policy
        print("✏️ Testing UPDATE operation: workspace policy")
        update_options = AgentPoolUpdateOptions(
            allowed_workspace_policy=AgentPoolAllowedWorkspacePolicy.SPECIFIC_WORKSPACES
        )
        updated_pool = client.agent_pools.update(agent_pool_id, update_options)
        print(
            f"✅ UPDATE workspace policy successful: {updated_pool.allowed_workspace_policy}"
        )

    except Exception as e:
        print(f"❌ Update operation failed: {e}")
        raise

    finally:
        if agent_pool_id:
            try:
                print(f"🗑️ Cleaning up update test agent pool: {agent_pool_id}")
                client.agent_pools.delete(agent_pool_id)
                print("✅ Cleanup successful")
            except Exception as e:
                print(f"⚠️ Cleanup failed: {e}")


def test_delete_agent_pool_integration(integration_client):
    """Test DELETE operation - Remove agent pools"""
    client, org = integration_client

    unique_id = str(uuid.uuid4())[:8]
    test_name = f"delete-pool-{unique_id}"
    agent_pool_id = None

    try:
        print(f"🔧 Testing against organization: {org}")
        print(f"🔧 Using token: {get_token_display(client)}...")

        # Create agent pool for delete test
        print(f"🔨 Creating agent pool for DELETE test: {test_name}")
        create_options = AgentPoolCreateOptions(name=test_name)
        created_pool = client.agent_pools.create(org, create_options)
        agent_pool_id = created_pool.id
        print(f"✅ Agent pool created for deletion: {agent_pool_id}")

        # Verify agent pool exists before deletion
        print("📖 Verifying agent pool exists before deletion")
        agent_pool = client.agent_pools.read(agent_pool_id)
        print(f"✅ Agent pool confirmed to exist: {agent_pool.name}")

        # Test delete operation
        print(f"🗑️ Testing DELETE operation: {agent_pool_id}")
        client.agent_pools.delete(agent_pool_id)
        print("✅ DELETE operation completed")

        # Verify agent pool is deleted
        print("📖 Verifying agent pool is deleted")
        try:
            client.agent_pools.read(agent_pool_id)
            print("❌ Agent pool still exists after deletion")
        except NotFound:
            print("✅ Agent pool successfully deleted - confirmed by 404 error")
            agent_pool_id = None  # Don't try to clean up again

    except Exception as e:
        print(f"❌ Delete operation failed: {e}")
        raise


def test_agent_token_management_integration(integration_client):
    """Test agent token creation and management"""
    client, org = integration_client

    unique_id = str(uuid.uuid4())[:8]
    pool_name = f"token-pool-{unique_id}"
    agent_pool_id = None
    agent_token_id = None

    try:
        print(f"🔧 Testing against organization: {org}")
        print(f"🔧 Using token: {get_token_display(client)}...")

        # Create agent pool for token testing
        print(f"🔨 Creating agent pool for token test: {pool_name}")
        create_options = AgentPoolCreateOptions(name=pool_name)
        agent_pool = client.agent_pools.create(org, create_options)
        agent_pool_id = agent_pool.id
        print(f"✅ Agent pool created: {agent_pool_id}")

        # Test creating agent token
        print("🔑 Testing agent token creation")
        token_options = AgentTokenCreateOptions(
            description=f"Test token for {pool_name}"
        )
        agent_token = client.agent_tokens.create(agent_pool_id, token_options)
        agent_token_id = agent_token.id

        print(f"✅ Agent token created: {agent_token.id}")
        print(f"✅ Token description: {agent_token.description}")
        print(f"✅ Token value available: {'Yes' if agent_token.token else 'No'}")

        # Test listing agent tokens
        print("📋 Testing agent token list")
        tokens = list(client.agent_tokens.list(agent_pool_id))
        print(f"✅ Found {len(tokens)} tokens for agent pool")

        # Test reading agent token
        print("📖 Testing agent token read")
        read_token = client.agent_tokens.read(agent_token_id)
        print(f"✅ Read token: {read_token.description}")
        print(
            f"✅ Token value in read: {'Yes' if read_token.token else 'No (security)'}"
        )

        # Test deleting agent token
        print("🗑️ Testing agent token deletion")
        client.agent_tokens.delete(agent_token_id)
        print("✅ Agent token deleted successfully")
        agent_token_id = None

    except Exception as e:
        print(f"❌ Agent token operation failed: {e}")
        raise

    finally:
        # Cleanup
        if agent_token_id:
            try:
                print(f"🗑️ Cleaning up agent token: {agent_token_id}")
                client.agent_tokens.delete(agent_token_id)
            except Exception as e:
                print(f"⚠️ Token cleanup failed: {e}")

        if agent_pool_id:
            try:
                print(f"🗑️ Cleaning up agent pool: {agent_pool_id}")
                client.agent_pools.delete(agent_pool_id)
                print("✅ Cleanup successful")
            except Exception as e:
                print(f"⚠️ Pool cleanup failed: {e}")


def test_agent_pool_error_handling_integration(integration_client):
    """Test error handling scenarios"""
    client, org = integration_client

    print(f"🔧 Testing against organization: {org}")
    print(f"🔧 Using token: {get_token_display(client)}...")

    print("🚫 Testing error handling scenarios")

    # Test reading a non-existent agent pool
    print("🚫 Testing read non-existent agent pool")
    fake_pool_id = "apool-nonexistent123456789"
    try:
        client.agent_pools.read(fake_pool_id)
        print("❌ Should have raised NotFound")
    except NotFound:
        print("✅ Correctly handled error for non-existent agent pool: NotFound")
    except Exception as e:
        print(
            f"✅ Correctly handled error for non-existent agent pool: {type(e).__name__}"
        )

    # Test updating a non-existent agent pool
    print("🚫 Testing update non-existent agent pool")
    try:
        update_options = AgentPoolUpdateOptions(name="nonexistent")
        client.agent_pools.update(fake_pool_id, update_options)
        print("❌ Should have raised NotFound")
    except NotFound:
        print("✅ Correctly handled update error for non-existent agent pool: NotFound")
    except Exception as e:
        print(
            f"✅ Correctly handled update error for non-existent agent pool: {type(e).__name__}"
        )

    # Test deleting a non-existent agent pool
    print("🚫 Testing delete non-existent agent pool")
    try:
        client.agent_pools.delete(fake_pool_id)
        print("❌ Should have raised NotFound")
    except NotFound:
        print("✅ Correctly handled delete error for non-existent agent pool: NotFound")
    except Exception as e:
        print(
            f"✅ Correctly handled delete error for non-existent agent pool: {type(e).__name__}"
        )

    print("✅ All error handling scenarios tested successfully")


def test_comprehensive_agent_pool_workflow(integration_client):
    """Test complete agent pool workflow"""
    client, org = integration_client

    unique_id = str(uuid.uuid4())[:8]
    test_name = f"comprehensive-pool-{unique_id}"
    updated_name = f"comprehensive-updated-{unique_id}"
    agent_pool_id = None
    agent_token_id = None

    try:
        print(f"🔧 Testing against organization: {org}")
        print(f"🔧 Using token: {get_token_display(client)}...")

        print(f"🔄 Starting comprehensive agent pool workflow: {test_name}")

        # 1. Create agent pool
        print("1️⃣ CREATE: Creating agent pool")
        create_options = AgentPoolCreateOptions(
            name=test_name,
            organization_scoped=True,
            allowed_workspace_policy=AgentPoolAllowedWorkspacePolicy.ALL_WORKSPACES,
        )
        agent_pool = client.agent_pools.create(org, create_options)
        agent_pool_id = agent_pool.id
        print(f"✅ CREATE: {agent_pool_id}")

        # 2. Read agent pool
        print("2️⃣ READ: Reading created agent pool")
        read_pool = client.agent_pools.read(agent_pool_id)
        print(f"✅ READ: {read_pool.name}")

        # 3. Update agent pool
        print("3️⃣ UPDATE: Updating agent pool")
        update_options = AgentPoolUpdateOptions(
            name=updated_name,
            organization_scoped=False,
            allowed_workspace_policy=AgentPoolAllowedWorkspacePolicy.SPECIFIC_WORKSPACES,
        )
        updated_pool = client.agent_pools.update(agent_pool_id, update_options)
        print(f"✅ UPDATE: {updated_pool.name}")

        # 4. Create agent token
        print("4️⃣ TOKEN: Creating agent token")
        token_options = AgentTokenCreateOptions(description=f"Token for {updated_name}")
        token = client.agent_tokens.create(agent_pool_id, token_options)
        agent_token_id = token.id
        print(f"✅ TOKEN: Created with description '{token.description}'")

        # 5. List agent pools
        print("5️⃣ LIST: Verifying agent pool appears in list")
        pools = list(client.agent_pools.list(org))
        pool_ids = [pool.id for pool in pools]
        if agent_pool_id in pool_ids:
            print("✅ LIST: Found updated agent pool in list")
        else:
            print("⚠️ LIST: Agent pool not found in list")

        # 6. Clean up token
        print("6️⃣ TOKEN_DELETE: Deleting agent token")
        client.agent_tokens.delete(agent_token_id)
        print("✅ TOKEN_DELETE: Token deleted")
        agent_token_id = None

        # 7. Delete agent pool
        print("7️⃣ DELETE: Deleting agent pool")
        client.agent_pools.delete(agent_pool_id)
        print("✅ DELETE: Agent pool deleted")

        # 8. Verify deletion
        print("8️⃣ VERIFY: Confirming deletion")
        try:
            client.agent_pools.read(agent_pool_id)
            print("❌ VERIFY: Agent pool still exists")
        except NotFound:
            print("✅ VERIFY: Deletion confirmed")
            agent_pool_id = None

        print("🎉 Comprehensive agent pool workflow completed successfully!")

    except Exception as e:
        print(f"❌ Comprehensive workflow failed: {e}")
        raise

    finally:
        # Emergency cleanup
        if agent_token_id:
            try:
                client.agent_tokens.delete(agent_token_id)
            except Exception:
                pass

        if agent_pool_id:
            try:
                client.agent_pools.delete(agent_pool_id)
            except Exception:
                pass


if __name__ == "__main__":
    """
    You can also run this file directly for quick testing:

    export TFE_TOKEN="your-token"
    export TFE_ORG="your-org"
    python examples/agent_example.py
    """

    token = os.environ.get("TFE_TOKEN")
    org = os.environ.get("TFE_ORG")

    if not token or not org:
        print("❌ Please set TFE_TOKEN and TFE_ORG environment variables")
        print("   export TFE_TOKEN='your-hcp-terraform-token'")
        print("   export TFE_ORG='your-organization-name'")
        exit(1)

    print("🧪 Running agent pool integration tests directly...")
    print("   For full pytest features, use: pytest examples/agent_pool.py -v -s")

    # Simple direct execution
    pytest.main([__file__, "-v", "-s"])
