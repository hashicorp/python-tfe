# Scenario: Manage workspace variables

HCP Terraform has two related variable concepts:

- Workspace variables belong directly to one workspace.
- Variable sets are reusable collections that can apply to many workspaces or
  projects.

Use workspace variables for workspace-specific values. Use variable sets for
shared values such as cloud regions, common Terraform inputs, or provider
credentials reused across many workspaces.

Upstream docs:

- Workspace variables: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/workspace-variables
- Variable sets: https://developer.hashicorp.com/terraform/enterprise/api-docs/variable-sets

## Workspace variables

```python
from pytfe import TFEClient
from pytfe.models import CategoryType, VariableCreateOptions, VariableUpdateOptions


client = TFEClient()
workspace_id = "ws-abc123"

region = client.variables.create(
    workspace_id,
    VariableCreateOptions(
        key="TF_VAR_region",
        value="us-east-1",
        category=CategoryType.TERRAFORM,
        sensitive=False,
    ),
)

updated = client.variables.update(
    workspace_id,
    region.id,
    VariableUpdateOptions(value="us-west-2"),
)

for variable in client.variables.list(workspace_id):
    print(variable.id, variable.key, variable.category, variable.sensitive)

client.variables.delete(workspace_id, updated.id)
```

Sensitive variable values may not be returned by the API after creation. Store
the source value in your secret manager; do not rely on reading it back.

## Inherited variables

`client.variables.list(...)` returns variables directly attached to a workspace.
Use `list_all(...)` when you also need variables inherited from variable sets:

```python
for variable in client.variables.list_all("ws-abc123"):
    print(variable.key)
```

## Variable sets

```python
from pytfe.models import (
    CategoryType,
    VariableSetApplyToWorkspacesOptions,
    VariableSetCreateOptions,
    VariableSetVariableCreateOptions,
    Workspace,
)


varset = client.variable_sets.create(
    "my-organization",
    VariableSetCreateOptions.model_validate(
        {
            "name": "shared-cloud-settings",
            "description": "Shared cloud settings",
            "global": False,
        }
    ),
)

client.variable_set_variables.create(
    varset.id,
    VariableSetVariableCreateOptions(
        key="TF_VAR_owner",
        value="platform-team",
        category=CategoryType.TERRAFORM,
        sensitive=False,
    ),
)

client.variable_sets.apply_to_workspaces(
    varset.id,
    VariableSetApplyToWorkspacesOptions(
        workspaces=[Workspace(id="ws-abc123")],
    ),
)
```

## Update and cleanup

```python
from pytfe.models import VariableSetVariableUpdateOptions


for variable in client.variable_set_variables.list(varset.id):
    if variable.key == "TF_VAR_owner":
        client.variable_set_variables.update(
            varset.id,
            variable.id,
            VariableSetVariableUpdateOptions(value="infra-team"),
        )

client.variable_sets.delete(varset.id)
```

## Operational tips

- Treat sensitive variables as write-only.
- Prefer variable sets for shared values to avoid drift between workspaces.
- Use workspace variables for exceptions and workspace-local values.
- Be deliberate with global variable sets because they apply broadly.
