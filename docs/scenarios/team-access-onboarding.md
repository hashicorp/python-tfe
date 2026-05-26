# Scenario: Team access onboarding

This scenario shows how to create a team, add members, grant workspace access,
and create a team token for automation.

Upstream docs:

- Teams: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/teams
- Team access: https://developer.hashicorp.com/terraform/enterprise/api-docs/team-access
- Team tokens: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/team-tokens

## Create a team

```python
from datetime import datetime, timezone

from pytfe import TFEClient
from pytfe.models import (
    TeamCreateOptions,
    TeamTokenCreateOptions,
    TeamWorkspaceAccessAddOptions,
    TeamWorkspaceAccessType,
)


client = TFEClient()

team = client.teams.create(
    "my-organization",
    TeamCreateOptions(
        name="platform-automation",
        visibility="organization",
    ),
)

print(team.id)
```

## Add users or organization memberships

If you know usernames:

```python
client.teams.add_users(team.id, ["alice", "bob"])
```

If you manage users by organization membership ID:

```python
client.teams.add_organization_memberships(
    team.id,
    ["ou-abc123", "ou-def456"],
)
```

You can inspect membership later:

```python
users = list(client.teams.list_users(team.id))
memberships = list(client.teams.list_organization_memberships(team.id))
```

## Grant workspace access

```python
grant = client.team_workspace_accesses.add(
    TeamWorkspaceAccessAddOptions(
        team_id=team.id,
        workspace_id="ws-abc123",
        access=TeamWorkspaceAccessType.WRITE,
    )
)

print(grant.id)
```

Use project access when the team needs the same access across a project:

```python
# See examples/team_project_access.py for a full project access example.
for access in client.team_project_accesses.list("team-abc123"):
    print(access.id)
```

## Create a team token

```python
token = client.team_tokens.create_with_options(
    team.id,
    TeamTokenCreateOptions(
        description="automation",
        expired_at=datetime(2026, 12, 31, tzinfo=timezone.utc),
    ),
)

print(token.id)
print(token.token)
```

The token value is sensitive. Store it in a secret manager immediately. Do not
print it in production logs.

## Cleanup

```python
client.team_workspace_accesses.remove("twsa-abc123")
client.team_tokens.delete_by_id("at-abc123")
client.teams.remove_users(team.id, ["alice", "bob"])
client.teams.delete(team.id)
```

Use the IDs returned by your create calls for cleanup.

