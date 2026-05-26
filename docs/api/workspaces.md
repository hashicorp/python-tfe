# Workspaces

Workspaces are the center of most pyTFE workflows. Use `client.workspaces` for
workspace settings and relationships, then combine it with runs, variables,
state versions, teams, and policies as needed.

Upstream docs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/workspaces

Example: [workspace.py](../../examples/workspace.py)

## Common methods

| Method | Purpose |
|---|---|
| `client.workspaces.list(organization, options=None)` | Iterate workspaces in an organization. |
| `client.workspaces.read(name, *, organization)` | Read by name. `organization` is keyword-only. |
| `client.workspaces.read_by_id(workspace_id)` | Read by workspace ID. |
| `client.workspaces.create(organization, options)` | Create a workspace. |
| `client.workspaces.update(name, options, *, organization)` | Update by name. `organization` is keyword-only. |
| `client.workspaces.update_by_id(workspace_id, options)` | Update by workspace ID. |
| `client.workspaces.delete(name, *, organization)` / `delete_by_id(workspace_id)` | Delete a workspace. |
| `client.workspaces.safe_delete(name, *, organization)` / `safe_delete_by_id(workspace_id)` | Delete with the API safe-delete path. |
| `client.workspaces.lock(...)`, `unlock(...)`, `force_unlock(...)` | Manage workspace locks. |
| `client.workspaces.assign_ssh_key(...)`, `unassign_ssh_key(...)` | Manage workspace SSH key assignment. |
| `client.workspaces.current_assessment_result(workspace_id)` | Read the latest health assessment, or `None` if assessments are disabled. |
| `client.workspaces.list_applicable_varsets(workspace_id)` | Iterate variable sets that apply to a workspace (direct, inherited, and global). |
| `client.workspaces.list_remote_state_consumers(...)` and related methods | Manage remote state consumers. |
| `client.workspaces.list_tags(...)`, `add_tags(...)`, `remove_tags(...)` | Manage workspace tags. |
| `client.workspaces.list_tag_bindings(...)` and related methods | Manage tag bindings. |

## List and filter

```python
from pytfe import TFEClient
from pytfe.models import WorkspaceListOptions

client = TFEClient()

options = WorkspaceListOptions(page_size=50, search="prod")

for workspace in client.workspaces.list("my-organization", options):
    print(workspace.id, workspace.name)
```

`list` returns an iterator. Use `list(client.workspaces.list(...))` if you need
a materialized Python list.

## Create a workspace

```python
from pytfe import TFEClient
from pytfe.models import WorkspaceCreateOptions

client = TFEClient()

workspace = client.workspaces.create(
    "my-organization",
    WorkspaceCreateOptions(name="example-workspace"),
)

print(workspace.id)
```

## Read by name or ID

```python
workspace = client.workspaces.read("example-workspace", organization="my-organization")
same_workspace = client.workspaces.read_by_id(workspace.id)
```

`organization` is a keyword-only argument on `read`, `update`, `delete`, and
`safe_delete`. The workspace name is positional; the organization name must be
passed by keyword. The same applies when updating or deleting by name:

```python
from pytfe.models import WorkspaceUpdateOptions

client.workspaces.update(
    "example-workspace",
    WorkspaceUpdateOptions(description="Updated by pyTFE"),
    organization="my-organization",
)

client.workspaces.delete("example-workspace", organization="my-organization")
```

Prefer ID-based methods in automation when you already have the workspace ID.
They avoid ambiguity when names change.

## Related resources

- Runs: [runs-plans-applies.md](runs-plans-applies.md)
- State: [state-versions.md](state-versions.md)
- Variables: [variables-and-variable-sets.md](variables-and-variable-sets.md)
- Teams and access: [teams-and-access.md](teams-and-access.md)

