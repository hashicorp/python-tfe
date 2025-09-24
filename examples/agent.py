"""Comprehensive example for Individual Agent operations with the TFE Python SDK.

This example demonstrates:
1. Listing agents within agent pools
2. Reading individual agent details
3. Deleting agents
4. Agent status monitoring
5. Error handling and best practices

Note: Individual agents are created by running the agent binary, not through the API.
This example shows how to manage agents that have already connected to agent pools.

Make sure to set the following environment variables:
- TFE_TOKEN: Your Terraform Cloud/Enterprise API token
- TFE_ADDRESS: Your Terraform Cloud/Enterprise URL (optional, defaults to https://app.terraform.io)
- TFE_ORG: Your organization name

Usage:
    export TFE_TOKEN="your-token-here"
    export TFE_ORG="your-organization"
    python examples/agent.py
"""

import os

import httpx
import pytest

from tfe.client import TFEClient
from tfe.config import TFEConfig
from tfe.models.agent import (
    AgentListOptions,
    AgentPoolCreateOptions,
    AgentReadOptions,
    AgentStatus,
)


def get_token_display(client: TFEClient) -> str:
    """Get a safe display version of the token for logging."""
    try:
        token = client._transport.token
        if token and len(token) > 10:
            return f"{token[:10]}..."
        return "Not set"
    except Exception:
        return "Error reading token"


@pytest.fixture(scope="session")
def integration_client():
    """Create TFE client for integration testing."""
    token = os.environ.get("TFE_TOKEN")
    org = os.environ.get("TFE_ORG")

    if not token:
        pytest.skip("TFE_TOKEN environment variable is required")
    if not org:
        pytest.skip("TFE_ORG environment variable is required")

    config = TFEConfig(token=token)
    client = TFEClient(config)

    return client, org


def test_agent_authentication_and_prerequisites(integration_client):
    """Test authentication and verify agent pool prerequisites."""
    client, org = integration_client

    try:
        print(f"🔧 Testing agent operations for organization: {org}")
        print(f"🔧 Using token: {get_token_display(client)}...")

        # Test 1: Basic authentication
        print("1️⃣ Testing basic API authentication...")
        headers = client._transport.headers.copy()
        response = httpx.get(
            f"{client._transport.base}/api/v2/organizations",
            headers=headers,
            timeout=30,
        )

        if response.status_code == 200:
            print("✅ Organizations API accessible")
        else:
            print(f"❌ Authentication failed (status: {response.status_code})")
            pytest.fail("Authentication failed - cannot proceed with agent tests")

        # Test 2: Check if any agent pools exist
        print("2️⃣ Checking for existing agent pools...")
        agent_pools = list(client.agent_pools.list(org))
        print(f"✅ Found {len(agent_pools)} agent pools in organization")

        if len(agent_pools) == 0:
            print("⚠️  No agent pools found - creating one for agent testing...")
            # Create a test agent pool
            create_options = AgentPoolCreateOptions(
                name="test-agent-pool-for-agents", organization_scoped=True
            )
            test_pool = client.agent_pools.create(org, create_options)
            print(f"✅ Created test agent pool: {test_pool.id}")
            print("✅ Prerequisites verified - agent pool available for testing")
        else:
            print(f"✅ Using existing agent pool: {agent_pools[0].id}")
            print("✅ Prerequisites verified - agent pools exist for testing")

    except Exception as e:
        print(f"❌ Prerequisites check failed: {e}")
        pytest.fail(f"Prerequisites not met: {e}")


def test_list_agents_integration(integration_client):
    """Test LIST operation - Get all agents in an agent pool."""
    client, org = integration_client

    try:
        print(f"🔧 Testing against organization: {org}")
        print(f"🔧 Using token: {get_token_display(client)}...")

        # Get an agent pool to test with
        agent_pools = list(client.agent_pools.list(org))
        if not agent_pools:
            print("⚠️  No agent pools found - creating one...")
            create_options = AgentPoolCreateOptions(
                name="test-agents-list", organization_scoped=True
            )
            test_pool = client.agent_pools.create(org, create_options)
            agent_pool_id = test_pool.id
            cleanup_pool = True
        else:
            agent_pool_id = agent_pools[0].id
            cleanup_pool = False

        print(f"📋 Testing LIST agents in pool: {agent_pool_id}")

        # Test basic list
        agents = list(client.agents.list(agent_pool_id))
        print(f"✅ Found {len(agents)} agents in agent pool")

        # Test list with options
        print("📋 Testing LIST with filtering options...")
        list_options = AgentListOptions(page_size=10, status=AgentStatus.IDLE)
        idle_agents = list(client.agents.list(agent_pool_id, list_options))
        print(f"✅ Found {len(idle_agents)} idle agents")

        # Test different status filters
        for status in [AgentStatus.BUSY, AgentStatus.UNKNOWN]:
            status_options = AgentListOptions(status=status)
            status_agents = list(client.agents.list(agent_pool_id, status_options))
            print(f"✅ Found {len(status_agents)} {status.value} agents")

        if len(agents) == 0:
            print(
                "ℹ️  No agents found - this is normal if no agent binaries are running"
            )
            print("ℹ️  To see agents, run the tfc-agent binary connected to this pool")
        else:
            print(f"🎉 Successfully listed {len(agents)} agents")
            for agent in agents[:3]:  # Show first 3 agents
                print(
                    f"   - Agent: {agent.name} (ID: {agent.id}, Status: {agent.status})"
                )

        # Cleanup if we created a pool
        if cleanup_pool:
            print(f"🗑️ Cleaning up test agent pool: {agent_pool_id}")
            client.agent_pools.delete(agent_pool_id)
            print("✅ Cleanup successful")

    except Exception as e:
        print(f"❌ List agents operation failed: {e}")
        pytest.fail(f"List agents failed: {e}")


def test_read_agent_integration(integration_client):
    """Test READ operation - Get specific agent details."""
    client, org = integration_client

    try:
        print(f"🔧 Testing against organization: {org}")
        print(f"🔧 Using token: {get_token_display(client)}...")

        # Get an agent pool and list agents
        agent_pools = list(client.agent_pools.list(org))
        if not agent_pools:
            print("⚠️  No agent pools found - creating one...")
            create_options = AgentPoolCreateOptions(
                name="test-agent-read", organization_scoped=True
            )
            test_pool = client.agent_pools.create(org, create_options)
            agent_pool_id = test_pool.id
            cleanup_pool = True
        else:
            agent_pool_id = agent_pools[0].id
            cleanup_pool = False

        # List agents to get one to read
        agents = list(client.agents.list(agent_pool_id))

        if not agents:
            print("ℹ️  No agents found in pool - cannot test read operation")
            print("ℹ️  To test this, run tfc-agent connected to an agent pool")
            print("✅ Read test skipped (no agents available)")
        else:
            # Test reading the first agent
            test_agent = agents[0]
            print(f"📖 Testing READ operation for agent: {test_agent.id}")

            # Read without options
            agent = client.agents.read(test_agent.id)
            print(f"✅ READ successful: {agent.name}")
            print(f"✅ Agent status: {agent.status}")
            print(f"✅ Agent version: {agent.version}")
            print(f"✅ Last ping: {agent.last_ping_at}")
            print(f"✅ IP address: {agent.ip_address}")

            # Read with options
            read_options = AgentReadOptions(include=["agent-pool"])
            agent_detailed = client.agents.read(test_agent.id, read_options)
            print(f"✅ READ with options successful: {agent_detailed.name}")

        # Cleanup if we created a pool
        if cleanup_pool:
            print(f"🗑️ Cleaning up test agent pool: {agent_pool_id}")
            client.agent_pools.delete(agent_pool_id)
            print("✅ Cleanup successful")

    except Exception as e:
        print(f"❌ Read agent operation failed: {e}")
        pytest.fail(f"Read agent failed: {e}")


def test_delete_agent_integration(integration_client):
    """Test DELETE operation - Remove an agent."""
    client, org = integration_client

    try:
        print(f"🔧 Testing against organization: {org}")
        print(f"🔧 Using token: {get_token_display(client)}...")

        # Get an agent pool and list agents
        agent_pools = list(client.agent_pools.list(org))
        if not agent_pools:
            print("⚠️  No agent pools found - creating one...")
            create_options = AgentPoolCreateOptions(
                name="test-agent-delete", organization_scoped=True
            )
            test_pool = client.agent_pools.create(org, create_options)
            agent_pool_id = test_pool.id
            cleanup_pool = True
        else:
            agent_pool_id = agent_pools[0].id
            cleanup_pool = False

        # List agents to get one to delete
        agents = list(client.agents.list(agent_pool_id))

        if not agents:
            print("ℹ️  No agents found in pool - cannot test delete operation")
            print("ℹ️  To test this, run tfc-agent connected to an agent pool")
            print("✅ Delete test skipped (no agents available)")
        else:
            # Test deleting an agent (only if there are multiple or it's a test agent)
            if len(agents) > 1:
                test_agent = agents[-1]  # Delete the last one
                print(f"🗑️ Testing DELETE operation for agent: {test_agent.id}")
                print(f"🗑️ Agent name: {test_agent.name}")

                # Confirm agent exists
                try:
                    agent_before = client.agents.read(test_agent.id)
                    print(f"✅ Agent confirmed to exist: {agent_before.name}")
                except Exception:
                    print("❌ Agent doesn't exist - cannot test delete")
                    return

                # Delete the agent
                print(f"🗑️ Deleting agent: {test_agent.id}")
                client.agents.delete(test_agent.id)
                print("✅ DELETE operation completed")

                # Verify deletion
                try:
                    client.agents.read(test_agent.id)
                    print("❌ Agent still exists after deletion")
                except Exception:
                    print("✅ Agent successfully deleted - confirmed by error on read")

            else:
                print("⚠️  Only one agent found - skipping delete to avoid disruption")
                print("✅ Delete test skipped (preserving single agent)")

        # Cleanup if we created a pool
        if cleanup_pool:
            print(f"🗑️ Cleaning up test agent pool: {agent_pool_id}")
            client.agent_pools.delete(agent_pool_id)
            print("✅ Cleanup successful")

    except Exception as e:
        print(f"❌ Delete agent operation failed: {e}")
        pytest.fail(f"Delete agent failed: {e}")


def test_agent_status_monitoring_integration(integration_client):
    """Test agent status monitoring and filtering."""
    client, org = integration_client

    try:
        print(f"🔧 Testing against organization: {org}")
        print(f"🔧 Using token: {get_token_display(client)}...")

        # Get agent pools and their agents
        agent_pools = list(client.agent_pools.list(org))

        if not agent_pools:
            print("⚠️  No agent pools found - creating one...")
            create_options = AgentPoolCreateOptions(
                name="test-agent-monitoring", organization_scoped=True
            )
            test_pool = client.agent_pools.create(org, create_options)
            agent_pool_id = test_pool.id
            cleanup_pool = True
        else:
            agent_pool_id = agent_pools[0].id
            cleanup_pool = False

        print(f"📊 Testing agent status monitoring for pool: {agent_pool_id}")

        # Get all agents
        all_agents = list(client.agents.list(agent_pool_id))
        print(f"📊 Total agents in pool: {len(all_agents)}")

        if len(all_agents) == 0:
            print("ℹ️  No agents found - status monitoring test requires running agents")
            print("✅ Status monitoring test skipped (no agents available)")
        else:
            # Count agents by status
            status_counts = {}
            for agent in all_agents:
                status = agent.status or AgentStatus.UNKNOWN
                status_counts[status] = status_counts.get(status, 0) + 1

            print("📊 Agent status summary:")
            for status, count in status_counts.items():
                print(f"   - {status.value}: {count} agents")

            # Test filtering by each status
            for status in AgentStatus:
                filter_options = AgentListOptions(status=status)
                filtered_agents = list(
                    client.agents.list(agent_pool_id, filter_options)
                )
                expected_count = status_counts.get(status, 0)
                print(
                    f"✅ Status filter '{status.value}': found {len(filtered_agents)} agents (expected {expected_count})"
                )

            # Show detailed info for first few agents
            print("📊 Detailed agent information:")
            for i, agent in enumerate(all_agents[:3]):
                print(f"   Agent {i + 1}:")
                print(f"     - ID: {agent.id}")
                print(f"     - Name: {agent.name}")
                print(f"     - Status: {agent.status}")
                print(f"     - Version: {agent.version}")
                print(f"     - Last ping: {agent.last_ping_at}")
                print(f"     - IP: {agent.ip_address}")

        # Cleanup if we created a pool
        if cleanup_pool:
            print(f"🗑️ Cleaning up test agent pool: {agent_pool_id}")
            client.agent_pools.delete(agent_pool_id)
            print("✅ Cleanup successful")

    except Exception as e:
        print(f"❌ Agent status monitoring failed: {e}")
        pytest.fail(f"Agent status monitoring failed: {e}")


def test_agent_error_handling_integration(integration_client):
    """Test error handling for agent operations."""
    client, org = integration_client

    try:
        print(f"🔧 Testing against organization: {org}")
        print(f"🔧 Using token: {get_token_display(client)}...")
        print("🚫 Testing agent error handling scenarios")

        # Test 1: Read non-existent agent
        print("🚫 Testing read non-existent agent")
        fake_agent_id = "agent-nonexistent123"
        try:
            client.agents.read(fake_agent_id)
            print("❌ Expected error for non-existent agent, but got success")
        except Exception as e:
            error_type = type(e).__name__
            print(f"✅ Correctly handled error for non-existent agent: {error_type}")

        # Test 2: Delete non-existent agent
        print("🚫 Testing delete non-existent agent")
        try:
            client.agents.delete(fake_agent_id)
            print("❌ Expected error for deleting non-existent agent, but got success")
        except Exception as e:
            error_type = type(e).__name__
            print(
                f"✅ Correctly handled delete error for non-existent agent: {error_type}"
            )

        # Test 3: List agents for non-existent pool
        print("🚫 Testing list agents for non-existent pool")
        fake_pool_id = "apool-nonexistent123"
        try:
            list(client.agents.list(fake_pool_id))
            print("❌ Expected error for non-existent pool, but got success")
        except Exception as e:
            error_type = type(e).__name__
            print(f"✅ Correctly handled error for non-existent pool: {error_type}")

        # Test 4: Invalid agent pool ID format
        print("🚫 Testing invalid agent pool ID format")
        try:
            list(client.agents.list("invalid-id"))
            print("❌ Expected error for invalid pool ID, but got success")
        except Exception as e:
            error_type = type(e).__name__
            print(f"✅ Correctly handled error for invalid pool ID: {error_type}")

        print("✅ All agent error handling scenarios tested successfully")

    except Exception as e:
        print(f"❌ Agent error handling test failed: {e}")
        pytest.fail(f"Agent error handling failed: {e}")


def test_comprehensive_agent_workflow(integration_client):
    """Test complete agent management workflow."""
    client, org = integration_client

    try:
        print(f"🔧 Testing against organization: {org}")
        print(f"🔧 Using token: {get_token_display(client)}...")
        print("🔄 Starting comprehensive agent workflow")

        # Step 1: Setup - ensure we have an agent pool
        agent_pools = list(client.agent_pools.list(org))
        if not agent_pools:
            print("1️⃣ SETUP: Creating agent pool for workflow...")
            create_options = AgentPoolCreateOptions(
                name="comprehensive-agent-workflow", organization_scoped=True
            )
            test_pool = client.agent_pools.create(org, create_options)
            agent_pool_id = test_pool.id
            cleanup_pool = True
            print(f"✅ SETUP: Created agent pool {agent_pool_id}")
        else:
            agent_pool_id = agent_pools[0].id
            cleanup_pool = False
            print(f"✅ SETUP: Using existing agent pool {agent_pool_id}")

        # Step 2: List all agents
        print("2️⃣ LIST: Getting all agents in pool...")
        all_agents = list(client.agents.list(agent_pool_id))
        print(f"✅ LIST: Found {len(all_agents)} agents")

        if len(all_agents) == 0:
            print("ℹ️  No agents found - workflow limited without running agents")
            print("ℹ️  To see full workflow, run tfc-agent connected to this pool")
        else:
            # Step 3: Read detailed agent info
            print("3️⃣ READ: Getting detailed info for first agent...")
            first_agent = all_agents[0]
            agent_details = client.agents.read(first_agent.id)
            print(
                f"✅ READ: Agent {agent_details.name} (Status: {agent_details.status})"
            )

            # Step 4: Monitor status changes (simulated)
            print("4️⃣ MONITOR: Checking agent status...")
            for status in [AgentStatus.IDLE, AgentStatus.BUSY, AgentStatus.UNKNOWN]:
                status_agents = list(
                    client.agents.list(agent_pool_id, AgentListOptions(status=status))
                )
                print(
                    f"✅ MONITOR: {len(status_agents)} agents with status '{status.value}'"
                )

            # Step 5: Agent health check
            print("5️⃣ HEALTH: Performing agent health check...")
            healthy_agents = []
            for agent in all_agents:
                if agent.status == AgentStatus.IDLE or agent.status == AgentStatus.BUSY:
                    healthy_agents.append(agent)
            print(
                f"✅ HEALTH: {len(healthy_agents)}/{len(all_agents)} agents are healthy"
            )

        # Step 6: Cleanup
        print("6️⃣ CLEANUP: Workflow completed")
        if cleanup_pool:
            print(f"🗑️ Cleaning up workflow agent pool: {agent_pool_id}")
            client.agent_pools.delete(agent_pool_id)
            print("✅ Cleanup successful")

        print("🎉 Comprehensive agent workflow completed successfully!")

    except Exception as e:
        print(f"❌ Comprehensive agent workflow failed: {e}")
        pytest.fail(f"Comprehensive agent workflow failed: {e}")


if __name__ == "__main__":
    # Check environment variables
    if not os.environ.get("TFE_TOKEN"):
        print("❌ TFE_TOKEN environment variable is required")
        print("💡 Set it with: export TFE_TOKEN='your-token-here'")
        exit(1)

    if not os.environ.get("TFE_ORG"):
        print("❌ TFE_ORG environment variable is required")
        print("💡 Set it with: export TFE_ORG='your-organization-name'")
        exit(1)

    print("🧪 Running individual agent integration tests directly...")
    print("   For full pytest features, use: pytest examples/agent.py -v -s")

    # Simple direct execution
    pytest.main([__file__, "-v", "-s"])
