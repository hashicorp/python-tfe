# Scenario: Agent pool setup

HCP Terraform agents let Terraform runs reach private networks that the hosted
runners cannot. A working agent setup needs four pieces:

1. An agent pool in the organization.
2. An agent authentication token for each running agent process.
3. Workspaces (or projects) configured to use the pool.
4. One or more agent processes started with the token, pointing at the API
   address.

This scenario covers the SDK side: creating the pool, generating a token, and
attaching workspaces. Starting the agent process itself is done outside Python
with the `tfc-agent` binary.

Upstream docs:

- Agents: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/agents
- Agent tokens: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/agent-tokens
- Agent pool concepts: https://developer.hashicorp.com/terraform/cloud-docs/agents

## Prerequisites

```bash
export TFE_TOKEN="your-api-token"
export TFE_ADDRESS="https://app.terraform.io"
```

The token needs `manage-agent-pools` permission on the organization, and
workspace write access on any workspaces you intend to attach.

## Step 1: Create the agent pool

```python
from pytfe import TFEClient
from pytfe.models import AgentPoolCreateOptions


client = TFEClient()
organization = "my-organization"

pool = client.agent_pools.create(
    organization,
    AgentPoolCreateOptions(
        name="private-network-pool",
        organization_scoped=False,
        allowed_workspace_ids=["ws-abc123"],
    ),
)

print(pool.id, pool.name)
```

Set `organization_scoped=True` to allow every workspace in the organization to
use the pool. Set it to `False` and pass `allowed_workspace_ids` (and/or
`allowed_project_ids`) to scope the pool explicitly. Scoped pools are safer for
shared organizations because they prevent unrelated workspaces from picking up
the agent.

## Step 2: Create an agent token

Each running agent process needs its own token:

```python
from pytfe.models import AgentTokenCreateOptions

token = client.agent_tokens.create(
    pool.id,
    AgentTokenCreateOptions(description="agent-host-1"),
)

print(token.id)
print(token.token)
```

The token value is returned only at creation time. Store it in a secret manager
immediately and reference it from the agent host's environment.

For multiple agents, create one token per host so revocation is granular:

```python
for host in ["agent-host-1", "agent-host-2", "agent-host-3"]:
    t = client.agent_tokens.create(
        pool.id,
        AgentTokenCreateOptions(description=host),
    )
    save_to_secret_manager(host, t.token)
```

## Step 3: Attach workspaces to the pool

A workspace uses an agent pool when its `execution_mode` is `agent` and its
`agent_pool_id` references the pool:

```python
from pytfe.models import ExecutionMode, WorkspaceUpdateOptions

client.workspaces.update_by_id(
    "ws-abc123",
    WorkspaceUpdateOptions(
        execution_mode=ExecutionMode.AGENT,
        agent_pool_id=pool.id,
    ),
)
```

For a scoped pool, you can also widen or narrow the allowed list later:

```python
from pytfe.models import AgentPoolAssignToWorkspacesOptions

client.agent_pools.assign_to_workspaces(
    pool.id,
    AgentPoolAssignToWorkspacesOptions(
        workspace_ids=["ws-abc123", "ws-def456"],
    ),
)
```

`assign_to_workspaces` replaces the allowed-workspaces list in full; it does
not append. Always pass the complete intended list.

## Step 4: Start the agent process

Outside Python, on the host that has the network path to your private
infrastructure:

```bash
export TFC_AGENT_TOKEN="<token value from Step 2>"
export TFC_AGENT_NAME="agent-host-1"
export TFC_ADDRESS="https://app.terraform.io"

tfc-agent
```

Confirm the agent registered:

```python
for agent in client.agents.list(pool.id):
    print(agent.id, agent.name, agent.status)
```

A healthy agent reports `status="idle"` or `status="busy"`.

## Cleanup

Revoke tokens when a host is decommissioned. Delete the pool only after no
workspaces or projects reference it.

```python
client.agent_tokens.delete(token.id)

# Detach the workspace before deleting the pool.
client.workspaces.update_by_id(
    "ws-abc123",
    WorkspaceUpdateOptions(execution_mode=ExecutionMode.REMOTE),
)
client.agent_pools.delete(pool.id)
```

## Operational notes

- Treat agent tokens like SSH keys: one per host, rotated, stored in a secret
  manager.
- Prefer scoped pools over organization-scoped pools when only some workspaces
  need private-network access.
- Agent processes hold long-lived connections. Restart them after rotating
  tokens or upgrading the agent binary.
- An agent pool with no running agents will leave runs queued indefinitely.
  Monitor `client.agents.list(pool.id)` from your observability stack.
