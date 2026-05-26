# Variables and variable sets

pyTFE has separate services for workspace variables, variable sets, and
variables inside variable sets.

Upstream docs:

- Workspace variables: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/workspace-variables
- Variable sets: https://developer.hashicorp.com/terraform/enterprise/api-docs/variable-sets

Examples:

- [variables.py](../../examples/variables.py)
- [variable_sets.py](../../examples/variable_sets.py)

## Workspace variables

| Method | Purpose |
|---|---|
| `client.variables.list(workspace_id, options=None)` | Iterate variables directly attached to a workspace. |
| `client.variables.list_all(workspace_id, options=None)` | Iterate direct and inherited variables. |
| `client.variables.read(workspace_id, variable_id)` | Read a variable. |
| `client.variables.create(workspace_id, options)` | Create a variable. |
| `client.variables.update(workspace_id, variable_id, options)` | Update a variable. |
| `client.variables.delete(workspace_id, variable_id)` | Delete a variable. |

```python
from pytfe.models import CategoryType, VariableCreateOptions

variable = client.variables.create(
    "ws-abc123",
    VariableCreateOptions(
        key="TF_VAR_region",
        value="us-east-1",
        category=CategoryType.TERRAFORM,
        sensitive=False,
    ),
)

print(variable.id)
```

Use `list_all` when you need variables inherited from variable sets:

```python
for variable in client.variables.list_all("ws-abc123"):
    print(variable.key)
```

## Variable sets

| Method | Purpose |
|---|---|
| `client.variable_sets.list(organization, options=None)` | Iterate variable sets in an organization. |
| `client.variable_sets.list_for_workspace(workspace_id, options=None)` | Iterate variable sets attached to a workspace. |
| `client.variable_sets.list_for_project(project_id, options=None)` | Iterate variable sets attached to a project. |
| `client.variable_sets.read(varset_id, options=None)` | Read a variable set. |
| `client.variable_sets.create(organization, options)` | Create a variable set. |
| `client.variable_sets.update(varset_id, options)` | Update a variable set. |
| `client.variable_sets.delete(varset_id)` | Delete a variable set. |
| `client.variable_sets.apply_to_workspaces(...)` | Attach a variable set to workspaces. |
| `client.variable_sets.apply_to_projects(...)` | Attach a variable set to projects. |

## Variables inside variable sets

| Method | Purpose |
|---|---|
| `client.variable_set_variables.list(varset_id, options=None)` | Iterate variables in a variable set. |
| `client.variable_set_variables.read(varset_id, variable_id)` | Read a variable-set variable. |
| `client.variable_set_variables.create(varset_id, options)` | Create a variable-set variable. |
| `client.variable_set_variables.update(varset_id, variable_id, options)` | Update a variable-set variable. |
| `client.variable_set_variables.delete(varset_id, variable_id)` | Delete a variable-set variable. |

Prefer variable sets for shared values across many workspaces or projects.
Prefer workspace variables for workspace-specific values.

