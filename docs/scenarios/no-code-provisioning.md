# Scenario: No-code provisioning

This scenario walks through the full no-code provisioning lifecycle from a
platform team's perspective:

1. Enable a private registry module for no-code use.
2. Constrain end users to specific allowed values for module variables.
3. Create a workspace from the no-code module on behalf of an end user.
4. Roll the workspace forward to a new module version (upgrade).

Upstream docs:

- No-code provisioning: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/no-code-provisioning
- Private registry modules: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/private-registry/modules

## Prerequisites

```bash
export TFE_TOKEN="your-api-token"        # user or team token (not org)
export TFE_ADDRESS="https://app.terraform.io"
export TFE_ORG="my-organization"
```

You also need:

- A private registry module already published in the organization.
- A project ID for the workspaces you'll create.
- The token must have permission to manage no-code modules and to create
  workspaces in the target project.

Organization tokens are **not** accepted by the no-code write endpoints. Use
a user or team token. See [authentication.md](../authentication.md).

## Step 1: Enable no-code provisioning on a registry module

```python
import os

from pytfe import TFEClient
from pytfe.models import (
    NoCodeModuleCreateOptions,
    NoCodeVariableOption,
)


client = TFEClient()
organization = os.environ["TFE_ORG"]
registry_module_id = "mod-abc123"

no_code_module = client.no_code_modules.create(
    organization,
    NoCodeModuleCreateOptions(
        registry_module_id=registry_module_id,
        enabled=True,
        version_pin="1.4.0",
    ),
)

print("no-code module id:", no_code_module.id)
```

`version_pin` defaults to the latest published version if omitted. Pinning
explicitly is safer in production: a registry publish would otherwise change
behaviour for every consumer with no review step.

## Step 2: Discover the module's variables

When you don't yet know what variables the module exposes, ask the API:

```python
for var in client.no_code_modules.read_variables(no_code_module.id, "1.4.0"):
    print(f"{var.name} ({var.type})", "required" if var.required else "optional")
    if var.description:
        print("   ", var.description)
```

`read_variables` returns one `RegistryModuleVariable` per declared variable
with `name`, `type`, `description`, `default`, `required`, `sensitive`, and
any `options` listed by the module author.

## Step 3: Constrain allowed values

For variables where end users should only pick from a curated set, attach
`NoCodeVariableOption` entries:

```python
from pytfe.models import NoCodeModuleUpdateOptions, NoCodeVariableOption

client.no_code_modules.update(
    no_code_module.id,
    NoCodeModuleUpdateOptions(
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
```

`update` replaces the entire `variable_options` list every time. To keep
existing options, include them (with their `id` set) in the next update.

## Step 4: Create a workspace from the module

This is what an end user (or a platform automation acting on their behalf)
runs. The workspace gets its Terraform code from the pinned module version
and its variable values from the inline `vars`.

```python
from pytfe.models import (
    NoCodeWorkspaceCreateOptions,
    NoCodeWorkspaceVariable,
    CategoryType,
)

workspace = client.no_code_modules.create_workspace(
    no_code_module.id,
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
                key="instance_size",
                value="medium",
                category=CategoryType.TERRAFORM,
            ),
        ],
    ),
)

print("workspace id:", workspace.id)
```

The returned `Workspace` is the same shape `client.workspaces.read` returns,
so you can chain it with the standard workspace, run, and state APIs.

### Agent execution mode

Workspaces that need to reach a private network use agents:

```python
from pytfe.models import ExecutionMode

workspace = client.no_code_modules.create_workspace(
    no_code_module.id,
    NoCodeWorkspaceCreateOptions(
        name="private-network-ws",
        project_id="prj-abc123",
        execution_mode=ExecutionMode.AGENT,
        agent_pool_id="apool-abc123",
    ),
)
```

The SDK raises `RequiredAgentPoolIDError` locally if `execution_mode=AGENT`
is set without an `agent_pool_id`.

## Step 5: Upgrade a workspace to a new module version

Bump the no-code module's `version_pin`, then upgrade each consuming
workspace. Upgrades are a three-step lifecycle: initiate → poll → confirm.

```python
import time

from pytfe.models import (
    NoCodeModuleUpdateOptions,
    NoCodeWorkspaceUpgradeOptions,
    NoCodeWorkspaceVariable,
    CategoryType,
)

# Bump the module version.
client.no_code_modules.update(
    no_code_module.id,
    NoCodeModuleUpdateOptions(version_pin="1.5.0"),
)

# Initiate the upgrade for one workspace, optionally changing variables.
upgrade = client.no_code_modules.upgrade_workspace(
    no_code_module.id,
    workspace.id,
    NoCodeWorkspaceUpgradeOptions(
        vars=[
            NoCodeWorkspaceVariable(
                key="instance_size",
                value="large",
                category=CategoryType.TERRAFORM,
            ),
        ],
    ),
)

terminal_plan_states = {"planned_and_finished", "errored", "canceled"}
while True:
    status = client.no_code_modules.read_workspace_upgrade(
        no_code_module.id, workspace.id, upgrade.id
    )
    print("upgrade status:", status.status)
    if status.status in terminal_plan_states:
        break
    time.sleep(5)

if status.status == "planned_and_finished":
    client.no_code_modules.confirm_workspace_upgrade(
        no_code_module.id, workspace.id, upgrade.id
    )
    print("upgrade applied")
```

`confirm_workspace_upgrade` returns `None`; success is signalled by HTTP
status. The plan URL on `status.plan_url` opens the upgrade plan in the
HCP Terraform UI for review before confirming.

## Cleanup

To disable no-code provisioning for the module (without deleting the
underlying registry module):

```python
client.no_code_modules.delete(no_code_module.id)
```

Workspaces already created from the module remain; they just no longer
receive new upgrades through the no-code flow. Delete the workspaces
separately through `client.workspaces.delete(...)` if appropriate.

## Operational notes

- Use a **team token** for automation. User tokens work but couple the
  automation to a single person.
- Pin `version_pin` explicitly. Defaulting to "latest" lets a publish change
  every workspace created from the module thereafter.
- Treat `variable_options` updates as set replacements — every update writes
  the full list.
- Audit who creates workspaces from no-code modules. Combine team workspace
  access (see [Team access onboarding](team-access-onboarding.md)) with
  no-code provisioning to keep ownership clean.
