# Scenario: Migrate workspaces and state between instances

Upstream docs:

- Migration overview: https://developer.hashicorp.com/terraform/cloud-docs/migrate
- Workspaces: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/workspaces
- Workspace variables: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/workspace-variables
- State versions: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/state-versions

## What pyTFE covers

| Migration area | pyTFE coverage | Notes |
|---|---|---|
| Source and target clients | `TFEClient(TFEConfig(...))` | Use explicit configs so source and target tokens do not mix. |
| Workspace inventory and creation | `workspaces.list`, `read`, `create`, `update` | Copy only settings you understand. Keep VCS and agent settings deliberate. |
| Current state migration | `state_versions.read_current`, `download_current`, `upload` | Lock the target workspace before upload. Prefer new target workspaces. |
| Local state-file import | `workspaces.create`, `workspaces.lock`, `state_versions.upload`, `workspaces.unlock` | Useful when migrating many Terraform OSS state files. |
| Workspace variables | `variables.list`, `variables.create` | Sensitive values may not be readable. Supply them from a secret map. |
| Variable sets | `variable_sets`, `variable_set_variables` | Same sensitive-value caveat as workspace variables. |
| Teams and access | `teams`, `team_workspace_accesses`, `team_project_accesses` | Usernames, org membership IDs, and target team IDs need planning. |
| Policies and policy sets | `policies`, `policy_sets`, `policy_set_parameters`, `policy_set_versions` | Sensitive policy-set parameters must be rehydrated from a secure source. |
| SSH keys | `ssh_keys` | Public metadata can be listed, but private key material must be re-added. |
| Configuration versions | `configuration_versions.download`, `upload` | API availability and source retention vary. Keep local config archives when possible. |
| VCS connections | `oauth_clients`, `oauth_tokens`, workspace `vcs_repo` fields | Target VCS connections usually need a manual source-token to target-token map. GitHub App connections may need manual setup. |
| TFE admin settings | Partial or unsupported | SSO, cost estimation, some admin settings, and older TFE-only APIs are outside this scenario. |

## Prepare source and target clients

Use separate environment variables for the two sides:

```bash
export TFE_SOURCE_ADDRESS="https://tfe-source.example.com"
export TFE_SOURCE_TOKEN="source-user-token"
export TFE_SOURCE_ORG="source-org"

export TFE_TARGET_ADDRESS="https://app.terraform.io"
export TFE_TARGET_TOKEN="target-user-token"
export TFE_TARGET_ORG="target-org"
```

Then create explicit clients:

```python
import os

from pytfe import TFEClient, TFEConfig


source = TFEClient(
    TFEConfig(
        address=os.environ["TFE_SOURCE_ADDRESS"],
        token=os.environ["TFE_SOURCE_TOKEN"],
    )
)
target = TFEClient(
    TFEConfig(
        address=os.environ["TFE_TARGET_ADDRESS"],
        token=os.environ["TFE_TARGET_TOKEN"],
    )
)

source_org = os.environ["TFE_SOURCE_ORG"]
target_org = os.environ["TFE_TARGET_ORG"]
```

Use user or team tokens with enough permission to read source data and create
target workspaces, variables, and state versions.

## Create a matching target workspace

Start with a conservative subset of workspace settings. Do not blindly copy
agent pools, VCS OAuth token IDs, SSH key IDs, or project IDs across instances;
those IDs are instance-local and usually need a target-side mapping.

```python
from pytfe.errors import NotFound
from pytfe.models import Workspace, WorkspaceCreateOptions


def read_or_create_target_workspace(source_workspace: Workspace) -> Workspace:
    assert source_workspace.name is not None

    try:
        return target.workspaces.read(source_workspace.name, organization=target_org)
    except NotFound:
        pass

    options = WorkspaceCreateOptions(
        name=source_workspace.name,
        description=source_workspace.description,
        terraform_version=source_workspace.terraform_version,
        working_directory=source_workspace.working_directory,
        auto_apply=source_workspace.auto_apply,
        file_triggers_enabled=source_workspace.file_triggers_enabled,
        global_remote_state=source_workspace.global_remote_state,
        queue_all_runs=source_workspace.queue_all_runs,
        speculative_enabled=source_workspace.speculative_enabled,
        trigger_prefixes=source_workspace.trigger_prefixes or None,
        trigger_patterns=source_workspace.trigger_patterns or None,
    )
    return target.workspaces.create(target_org, options)
```

If the source workspace uses VCS, agents, SSH keys, or project placement,
create the target-side resources first and pass the mapped target IDs in a
separate migration pass.

## Copy workspace variables

Non-sensitive variables can be copied from the source API response. Sensitive
variables usually cannot be read back, so pass their values in from a secret
manager or an operator-reviewed JSON file.

```python
from pytfe.models import VariableCreateOptions


def copy_workspace_variables(
    source_workspace_id: str,
    target_workspace_id: str,
    *,
    sensitive_values: dict[str, str],
) -> list[str]:
    missing_sensitive: list[str] = []

    for variable in source.variables.list(source_workspace_id):
        if variable.sensitive:
            value = sensitive_values.get(variable.key or "")
            if value is None:
                missing_sensitive.append(variable.key or "<unknown>")
                continue
        else:
            value = variable.value

        target.variables.create(
            target_workspace_id,
            VariableCreateOptions(
                key=variable.key,
                value=value,
                description=variable.description,
                category=variable.category,
                hcl=variable.hcl,
                sensitive=variable.sensitive,
            ),
        )

    return missing_sensitive
```

Do not print sensitive values. If `missing_sensitive` is not empty, pause the
migration and fill the secret map before running a real plan.

## Migrate current state from a source workspace

This copies only the current state version. That is the safest default for a
trimmed migration. Historical state-version migration is possible with
`state_versions.list(...)`, but it is slower, noisier, and usually not needed
for a functional cutover.

```python
import hashlib

from pytfe.models import StateVersionCreateOptions, WorkspaceLockOptions


def migrate_current_state(source_workspace_id: str, target_workspace_id: str) -> str:
    source_current = source.state_versions.read_current(source_workspace_id)
    raw_state = source.state_versions.download_current(source_workspace_id)

    target.workspaces.lock(
        target_workspace_id,
        WorkspaceLockOptions(reason="Migrate current state with pyTFE"),
    )
    try:
        migrated = target.state_versions.upload(
            target_workspace_id,
            raw_state=raw_state,
            options=StateVersionCreateOptions(
                serial=source_current.serial or 1,
                md5=hashlib.md5(raw_state).hexdigest(),
            ),
        )
    finally:
        target.workspaces.unlock(target_workspace_id)

    return migrated.id
```

Use this against a target workspace that has never run Terraform. If the target
already has state, choose a serial strictly greater than the target current
serial and confirm that replacing the state is intentional.

## Import many local state files

The state-only workflow from local `terraform.tfstate` files uses the same
workspace-create, lock, upload, and unlock sequence.

```python
from pathlib import Path


def upload_local_state_file(
    workspace_name: str,
    state_path: Path,
    *,
    serial: int = 1,
) -> str:
    try:
        workspace = target.workspaces.read(workspace_name, organization=target_org)
    except NotFound:
        workspace = target.workspaces.create(
            target_org,
            WorkspaceCreateOptions(name=workspace_name),
        )

    raw_state = state_path.read_bytes()

    target.workspaces.lock(
        workspace.id,
        WorkspaceLockOptions(reason=f"Import {state_path.name} with pyTFE"),
    )
    try:
        state_version = target.state_versions.upload(
            workspace.id,
            raw_state=raw_state,
            options=StateVersionCreateOptions(
                serial=serial,
                md5=hashlib.md5(raw_state).hexdigest(),
            ),
        )
    finally:
        target.workspaces.unlock(workspace.id)

    return state_version.id
```

For bulk migrations, keep a manifest that maps each state file to the intended
target workspace name. Run a dry-run pass that creates no resources and prints
the planned mappings before uploading anything.

## End-to-end skeleton

```python
sensitive_values_by_workspace = {
    # "source-workspace-name": {"TF_VAR_password": "..."}
}

for source_workspace in source.workspaces.list(source_org):
    if not source_workspace.name:
        continue

    target_workspace = read_or_create_target_workspace(source_workspace)

    missing = copy_workspace_variables(
        source_workspace.id,
        target_workspace.id,
        sensitive_values=sensitive_values_by_workspace.get(source_workspace.name, {}),
    )
    if missing:
        print(f"skipped sensitive values for {source_workspace.name}: {missing}")

    migrated_state_id = migrate_current_state(
        source_workspace.id,
        target_workspace.id,
    )
    print(source_workspace.name, "state migrated as", migrated_state_id)
```

After migration, queue a speculative or no-op plan in each target workspace
before enabling normal automation.

## Operational checklist

- Stop source-side Terraform operations before copying state.
- Prefer new target workspaces that have never performed a run.
- Keep state bytes, variable values, SSH keys, and configuration archives out
  of logs and CI artifacts.
- Build explicit ID maps for VCS OAuth tokens, SSH keys, projects, teams, and
  agent pools. Do not reuse source IDs in the target instance.
- Rehydrate sensitive variables, sensitive policy-set parameters, SSH private
  keys, and configuration archives from a secure operator-provided source.
- Validate the target workspace with a plan before applying.
- Keep the source organization read-only until the target validation is
  complete and rollback expectations are documented.
