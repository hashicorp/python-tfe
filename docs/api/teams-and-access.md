# Teams and access

Team and access APIs control who can view, plan, apply, manage variables, and
administer workspaces or projects.

Upstream docs:

- Teams: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/teams
- Team tokens: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/team-tokens
- Team access: https://developer.hashicorp.com/terraform/enterprise/api-docs/team-access
- Project team access: https://developer.hashicorp.com/terraform/enterprise/api-docs/project-team-access
- Organization memberships: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/organization-memberships

Examples:

- [team.py](../../examples/team.py)
- [team_workspace_access.py](../../examples/team_workspace_access.py)
- [team_project_access.py](../../examples/team_project_access.py)
- [team_token.py](../../examples/team_token.py)

## Teams

| Method | Purpose |
|---|---|
| `client.teams.list(organization, options=None)` | Iterate teams in an organization. |
| `client.teams.read(team_id)` | Read a team. |
| `client.teams.create(organization, options)` | Create a team. |
| `client.teams.update(team_id, options)` | Update a team. |
| `client.teams.delete(team_id)` | Delete a team. |
| `client.teams.add_users(team_id, usernames)` | Add users by username. |
| `client.teams.remove_users(team_id, usernames)` | Remove users by username. |
| `client.teams.add_organization_memberships(team_id, ids)` | Add users by organization membership ID. |
| `client.teams.remove_organization_memberships(team_id, ids)` | Remove users by organization membership ID. |
| `client.teams.list_users(team_id)` | List users included in a team. |
| `client.teams.list_organization_memberships(team_id)` | List team memberships. |

## Workspace access

```python
from pytfe.models import (
    TeamWorkspaceAccessAddOptions,
    TeamWorkspaceAccessType,
)

grant = client.team_workspace_accesses.add(
    TeamWorkspaceAccessAddOptions(
        team_id="team-abc123",
        workspace_id="ws-abc123",
        access=TeamWorkspaceAccessType.WRITE,
    )
)

print(grant.id)
```

Use `TeamWorkspaceAccessType.CUSTOM` with the custom permission fields when you
need to model fine-grained access.

## Project access

`client.team_project_accesses` manages access grants between teams and projects.
Use project access for broad permissions across all workspaces in a project.
Use workspace access for exceptions or smaller scopes.

## Team tokens

Team tokens are useful for automation owned by a team:

```python
token = client.team_tokens.create("team-abc123")
print(token.token)
```

Store returned token values in a secret manager. Token values are sensitive and
may only be returned at creation time.

