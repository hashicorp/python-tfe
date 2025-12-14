"""Simple Individual Agent operations example with the TFE Python SDK.

This example demonstrates:
1. Listing agents within agent pools
2. Reading individual agent details
3. Agent status monitoring
4. Using the organization SDK client

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

from pytfe.client import TFEClient
from pytfe.config import TFEConfig
from pytfe.errors import NotFound
from pytfe.models import AgentListOptions


def main():
    """Main function demonstrating agent operations."""
    # Get environment variables
    token = os.environ.get("TFE_TOKEN")
    org = os.environ.get("TFE_ORG")
    address = os.environ.get("TFE_ADDRESS", "https://app.terraform.io")

    if not token:
        print("TFE_TOKEN environment variable is required")
        return 1

    if not org:
        print("TFE_ORG environment variable is required")
        return 1

    # Create TFE client
    config = TFEConfig(token=token, address=address)
    client = TFEClient(config)

    print(f"Connected to: {address}")
    print(f" Organization: {org}")

    try:
        # Example 1: Find agent pools to demonstrate agent operations
        print("\n Finding agent pools...")
        agent_pools = client.agent_pools.list(org)

        # Convert to list to check if empty and get count
        pool_list = list(agent_pools)
        if not pool_list:
            print("No agent pools found. Create an agent pool first.")
            return 1

        print(f"Found {len(pool_list)} agent pools:")
        for pool in pool_list:
            print(f"  - {pool.name} (ID: {pool.id}, Agents: {pool.agent_count})")

        # Example 2: List agents in each pool
        print("\n Listing agents in each pool...")
        total_agents = 0

        for pool in pool_list:
            print(f"\n Agents in pool '{pool.name}':")

            # Use optional parameters for listing
            list_options = AgentListOptions(page_size=10)  # Optional parameter
            agents = client.agents.list(pool.id, options=list_options)

            # Convert to list to check if empty and iterate
            agent_list = list(agents)
            if agent_list:
                total_agents += len(agent_list)
                for agent in agent_list:
                    print(f"Agent {agent.id}")
                    print(f"Name: {agent.name or 'Unnamed'}")
                    print(f"Status: {agent.status}")
                    print(f"Version: {agent.version or 'Unknown'}")
                    print(f"IP: {agent.ip_address or 'Unknown'}")
                    print(f"Last Ping: {agent.last_ping_at or 'Never'}")

                    # Example 3: Read detailed agent information
                    try:
                        agent_details = client.agents.read(agent.id)
                        print("Agent details retrieved successfully")
                        print(f"Full name: {agent_details.name or 'Unnamed'}")
                        print(f"Current status: {agent_details.status}")
                    except NotFound:
                        print("Agent details not accessible")
                    except Exception as e:
                        print(f"Error reading agent details: {e}")

                    print("")
            else:
                print("No agents found in this pool")

        if total_agents == 0:
            print("\n No agents found in any pools.")
            print("To see agents in action:")
            print("1. Create an agent pool")
            print("2. Run a Terraform Enterprise agent binary connected to the pool")
            print("3. Run this example again")
        else:
            print(f"\n Total agents found across all pools: {total_agents}")

        print("\n Agent operations completed successfully!")
        return 0

    except NotFound as e:
        print(f" Resource not found: {e}")
        return 1
    except Exception as e:
        print(f" Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
