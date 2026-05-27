# No-code provisioning

No-code provisioning lets users create workspaces from a curated registry
module without writing Terraform code. The workflow has three actors:

- A platform admin enables a registry module for no-code use and sets allowed
  variable values.
- An end user creates a workspace from that module, supplying only variable
  values.
- Either party can later upgrade an existing no-code workspace to a newer
  module version.

`client.no_code_modules` covers all four pieces: module CRUD, variable
introspection, workspace creation, and workspace upgrade lifecycle.

Upstream docs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/no-code-provisioning

Example: [no_code_provisioning.py](../../examples/no_code_provisioning.py)

## Token requirements

Every write endpoint (`create`, `update`, `delete`, `create_workspace`,
`upgrade_workspace`, `confirm_workspace_upgrade`) requires a **user or team
token**. Organization tokens are not accepted by the API. Read endpoints
(`read`, `read_variables`, `read_workspace_upgrade`) do not have this
restriction.

## Common methods

| Method | Purpose |
|---|---|
| `client.no_code_modules.create(organization, options)` | Enable no-code provisioning for a registry module. |
| `client.no_code_modules.read(no_code_module_id, options=None)` | Read a no-code module; pass `NoCodeModuleReadOptions(include=[VARIABLE_OPTIONS])` to materialise allowed-values. |
| `client.no_code_modules.update(no_code_module_id, options)` | Update enabled flag, version pin, or variable options. |
| `client.no_code_modules.delete(no_code_module_id)` | Disable no-code provisioning for the module. |
| `client.no_code_modules.read_variables(no_code_module_id, version)` | Iterate variables declared by a specific module version, for form-building. |
| `client.no_code_modules.create_workspace(no_code_module_id, options)` | Create a workspace from the no-code module. |
| `client.no_code_modules.upgrade_workspace(no_code_module_id, workspace_id, options=None)` | Start an upgrade; returns a `WorkspaceUpgrade` to poll. |
| `client.no_code_modules.read_workspace_upgrade(no_code_module_id, workspace_id, upgrade_id)` | Poll upgrade status. |
| `client.no_code_modules.confirm_workspace_upgrade(no_code_module_id, workspace_id, upgrade_id)` | Confirm and apply the upgrade plan. |

## Enable a registry module for no-code use

```python
from pytfe import TFEClient
from pytfe.models import (
    NoCodeModuleCreateOptions,
    NoCodeVariableOption,
)


client = TFEClient()

no_code_module = client.no_code_modules.create(
    "my-organization",
    NoCodeModuleCreateOptions(
        registry_module_id="mod-abc123",
        enabled=True,
        version_pin="1.4.0",
        variable_options=[
            NoCodeVariableOption(
                variable_name="region",
                variable_type="string",
                options=["us-east-1", "us-west-2", "eu-west-1"],
            ),
            NoCodeVariableOption(
                variable_name="instance_size",
                variable_type="string",
                options=["small", "medium", "large"],
            ),
        ],
    ),
)

print(no_code_module.id)
```

`version_pin` defaults to the latest version when omitted. Each
`NoCodeVariableOption` constrains end users to one of the listed values for
that variable.

## Read a module with its variable options

`variable_options` are returned by reference only unless you ask for them with
the `include` query:

```python
from pytfe.models import NoCodeModuleIncludeOpt, NoCodeModuleReadOptions

module = client.no_code_modules.read(
    "nocode-abc123",
    NoCodeModuleReadOptions(include=[NoCodeModuleIncludeOpt.VARIABLE_OPTIONS]),
)

for option in module.variable_options:
    print(option.variable_name, option.options)
```

Without the include, `module.variable_options` contains stubs with `id` only.

## Update variable options

To update an existing option, pass its `id` in the entry; entries without an
`id` are added as new options. To remove an option, omit it from the list —
update calls replace the entire `variable-options` set.

The HCP API requires every PATCH on a no-code module to include the
`registry-module` relationship in the body, or the server returns `404`. The
SDK handles this transparently: if you don't supply `registry_module_id`
on `NoCodeModuleUpdateOptions`, the resource issues an extra GET to pick up
the current module's relationship. Pass `registry_module_id` explicitly to
skip the round trip:

```python
NoCodeModuleUpdateOptions(
    registry_module_id="mod-abc123",
    enabled=False,
)
```

```python
from pytfe.models import NoCodeModuleUpdateOptions, NoCodeVariableOption

updated = client.no_code_modules.update(
    "nocode-abc123",
    NoCodeModuleUpdateOptions(
        version_pin="1.5.0",
        variable_options=[
            NoCodeVariableOption(
                id="vo-existing123",
                variable_name="region",
                variable_type="string",
                options=["us-east-1", "us-east-2", "us-west-2"],
            ),
            NoCodeVariableOption(
                variable_name="environment",
                variable_type="string",
                options=["dev", "staging", "prod"],
            ),
        ],
    ),
)
```

## Introspect variables for a module version

When building a UI that lets users pick variable values, use
`read_variables` to discover what the module accepts:

```python
for var in client.no_code_modules.read_variables("nocode-abc123", "1.4.0"):
    print(var.name, var.type, var.required, var.options)
```

The returned `RegistryModuleVariable` objects include `name`, `type`,
`description`, `default`, `required`, `sensitive`, and `options`.

## Create a workspace from a no-code module

```python
from pytfe.models import (
    NoCodeWorkspaceCreateOptions,
    NoCodeWorkspaceVariable,
    CategoryType,
)

workspace = client.no_code_modules.create_workspace(
    "nocode-abc123",
    NoCodeWorkspaceCreateOptions(
        name="customer-acme-us-east-1",
        project_id="prj-abc123",
        description="Production environment for ACME (us-east-1)",
        terraform_version="1.7.0",
        vars=[
            NoCodeWorkspaceVariable(
                key="region",
                value="us-east-1",
                category=CategoryType.TERRAFORM,
            ),
            NoCodeWorkspaceVariable(
                key="environment",
                value="prod",
                category=CategoryType.TERRAFORM,
            ),
        ],
    ),
)

print(workspace.id, workspace.execution_mode)
```

The returned `Workspace` is parsed the same way as `client.workspaces.read`,
so relationships (`project`, `agent_pool`, `vars`) are available when the
server includes them.

For agent execution, set both `execution_mode` and `agent_pool_id`:

```python
from pytfe.models import ExecutionMode

workspace = client.no_code_modules.create_workspace(
    "nocode-abc123",
    NoCodeWorkspaceCreateOptions(
        name="private-network-ws",
        project_id="prj-abc123",
        execution_mode=ExecutionMode.AGENT,
        agent_pool_id="apool-abc123",
    ),
)
```

The SDK raises `RequiredAgentPoolIDError` if `execution_mode=AGENT` is set
without an `agent_pool_id`.

## Upgrade a no-code workspace

Upgrades are a three-step lifecycle: initiate → poll → confirm.

```python
import time

from pytfe.models import (
    NoCodeWorkspaceUpgradeOptions,
    NoCodeWorkspaceVariable,
    CategoryType,
)

upgrade = client.no_code_modules.upgrade_workspace(
    "nocode-abc123",
    "ws-abc123",
    NoCodeWorkspaceUpgradeOptions(
        vars=[
            NoCodeWorkspaceVariable(
                key="region",
                value="us-west-2",
                category=CategoryType.TERRAFORM,
            ),
        ],
    ),
)

terminal_plan_states = {"planned_and_finished", "errored", "canceled"}
while True:
    status = client.no_code_modules.read_workspace_upgrade(
        "nocode-abc123", "ws-abc123", upgrade.id
    )
    print(status.status, status.plan_url)
    if status.status in terminal_plan_states:
        break
    time.sleep(5)

if status.status == "planned_and_finished":
    client.no_code_modules.confirm_workspace_upgrade(
        "nocode-abc123", "ws-abc123", upgrade.id
    )
```

`confirm_workspace_upgrade` returns `None` and signals success via HTTP
status; the API responds with a plain-text body (`"Workspace update
completed"`) which is intentionally not surfaced.

## Operational notes

- **Variable options are wire-replaced, not merged.** Every `update` call
  with a `variable_options` list replaces the whole set. To keep an existing
  option, include it (with its `id`) in the list.
- **`version_pin` controls what the no-code workspace gets.** Update it to
  roll out a new module version; downstream workspaces still need explicit
  `upgrade_workspace` calls to adopt it.
- **Pin a version explicitly in production.** Defaulting to "latest" means a
  registry module publish can change behaviour for every consumer.
- **Treat the workspace returned by `create_workspace` like any other.**
  Once created, use `client.workspaces`, `client.runs`, `client.state_versions`
  to manage it.
