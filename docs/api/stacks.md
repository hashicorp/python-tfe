# Stacks

HCP Terraform Stacks let you manage multiple Terraform components as a single
unit, with coordinated deployments across multiple environments. The pytfe SDK
covers the full lifecycle: creating stacks, preparing configurations,
orchestrating deployment groups and runs, inspecting deployment steps, reading
stack states, and handling diagnostics.

Upstream docs:

- Stacks: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/stacks/stacks
- Stack configurations: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/stacks/stack-configurations
- Stack deployments: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/stacks/stack-deployments
- Stack deployment groups: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/stacks/stack-deployment-groups
- Stack deployment runs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/stacks/stack-deployment-runs
- Stack deployment steps: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/stacks/stack-deployment-steps
- Stack states: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/stacks/stack-states
- Stack diagnostics: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/stacks/stack-diagnostics

Examples:

- [stack.py](../../examples/stack.py)
- [stack_configuration.py](../../examples/stack_configuration.py)
- [stack_deployment.py](../../examples/stack_deployment.py)
- [stack_deployment_group.py](../../examples/stack_deployment_group.py)
- [stack_deployment_run.py](../../examples/stack_deployment_run.py)
- [stack_deployment_step.py](../../examples/stack_deployment_step.py)
- [stack_state.py](../../examples/stack_state.py)
- [stack_configuration_summary.py](../../examples/stack_configuration_summary.py)
- [stack_deployment_group_summary.py](../../examples/stack_deployment_group_summary.py)
- [stack_diagnostic.py](../../examples/stack_diagnostic.py)

See the end-to-end scenario at [stack-deployment.md](../scenarios/stack-deployment.md).

---

## Stacks (`client.stacks`)

| Method | Purpose |
|---|---|
| `client.stacks.create(options)` | Create a stack in a project. |
| `client.stacks.update(stack_id, options)` | Update a stack's name, description, or VCS settings. |
| `client.stacks.list(organization, options)` | Iterate stacks in an organization. |
| `client.stacks.read(stack_id)` | Read a single stack. |
| `client.stacks.delete(stack_id)` | Delete a stack. |
| `client.stacks.force_delete(stack_id)` | Force-delete a stack that cannot be deleted normally. |

```python
from pytfe import TFEClient
from pytfe.models import Project, StackCreateOptions, StackListOptions, VCSRepo

client = TFEClient()

# Create
stack = client.stacks.create(
    StackCreateOptions(
        name="k8s-stack",
        project=Project(id="prj-abc123"),
        vcs_repo=VCSRepo(
            identifier="my-org/k8s-stack",
            branch="main",
            oauth_token_id="ot-abc123",
        ),
    )
)
print(stack.id, stack.name)

# List
for stack in client.stacks.list("my-org", StackListOptions(page_size=20)):
    print(stack.id, stack.name, stack.deployment_names)

# Read / update / delete
stack = client.stacks.read("st-abc123")
client.stacks.delete("st-abc123")
```

---

## Stack configurations (`client.stack_configurations`)

A stack configuration is a versioned snapshot of the stack's source,
created whenever a VCS commit triggers preparation. Its `status` progresses
from `pending` through `converging` to `converged` (or `errored` if
preparation fails). Check `client.stack_diagnostics` for details when a
configuration errors.

| Method | Purpose |
|---|---|
| `client.stack_configurations.create(stack_id, options)` | Create (trigger preparation of) a new configuration. |
| `client.stack_configurations.list(stack_id, options=None)` | Iterate configurations for a stack, newest first. |
| `client.stack_configurations.read(configuration_id, options=None)` | Read a configuration, optionally with included relationships. |

```python
from pytfe.models import (
    StackConfigurationCreateOptions,
    StackConfigurationIncludeOps,
    StackConfigurationReadOptions,
    StackConfigurationSource,
)

# Trigger preparation from the latest VCS commit
config = client.stack_configurations.create(
    "st-abc123",
    StackConfigurationCreateOptions(source=StackConfigurationSource.FETCH),
)
print(config.id, config.status)

# Read with diagnostics included
config = client.stack_configurations.read(
    "stc-abc123",
    StackConfigurationReadOptions(
        include=[StackConfigurationIncludeOps.STACK_DIAGNOSTICS]
    ),
)

# Iterate configurations for a stack
for config in client.stack_configurations.list("st-abc123"):
    print(config.id, config.status, config.sequence_number)
```

---

## Stack configuration summaries (`client.stack_configuration_summaries`)

Lightweight rollup of status and deployment counts per configuration — useful
for dashboards without fetching every configuration individually. Each summary
also carries `group_status_summary` and `run_status_summary` objects with
aggregated counts across all deployment groups and runs.

| Method | Purpose |
|---|---|
| `client.stack_configuration_summaries.list(stack_id, options=None)` | Iterate configuration summaries for a stack, newest first. |

```python
from pytfe.models import StackConfigurationSummaryListOptions

for summary in client.stack_configuration_summaries.list("st-abc123"):
    print(summary.id, f"seq={summary.sequence_number}", summary.status)
    if summary.group_status_summary:
        g = summary.group_status_summary
        print(f"  groups: succeeded={g.succeeded} failed={g.failed}")
    if summary.run_status_summary:
        r = summary.run_status_summary
        print(f"  runs:   succeeded={r.succeeded} failed={r.failed}")
```

---

## Stack deployments (`client.stack_deployments`)

A stack deployment represents one named environment (e.g. `dev`, `staging`,
`prod`) that receives configuration changes. Deployments are defined in the
stack's source and tracked here for status and history.

| Method | Purpose |
|---|---|
| `client.stack_deployments.list(stack_id, options=None)` | Iterate deployments for a stack. |

```python
for deployment in client.stack_deployments.list("st-abc123"):
    print(deployment.id, deployment.name)
```

---

## Stack deployment groups (`client.stack_deployment_groups`)

A deployment group coordinates the plan and apply runs for one deployment
within a configuration. Use `approve_all_plans` to advance pending plan steps,
or `rerun` to retry specific failed deployments.

| Method | Purpose |
|---|---|
| `client.stack_deployment_groups.list(configuration_id, options=None)` | Iterate deployment groups for a configuration. |
| `client.stack_deployment_groups.read(group_id)` | Read a deployment group. |
| `client.stack_deployment_groups.read_by_name(configuration_id, name)` | Read a deployment group by its deployment name. |
| `client.stack_deployment_groups.approve_all_plans(group_id)` | Approve all pending plan steps in the group. |
| `client.stack_deployment_groups.rerun(group_id, options)` | Rerun specific failed deployments in the group. |

```python
from pytfe.models import StackDeploymentGroupRerunOptions

# List all groups for a configuration
for group in client.stack_deployment_groups.list("stc-abc123"):
    print(group.id, group.status)

# Read by deployment name
dev_group = client.stack_deployment_groups.read_by_name("stc-abc123", "dev")

# Approve all pending plans
client.stack_deployment_groups.approve_all_plans("sdg-abc123")

# Rerun failed deployments
client.stack_deployment_groups.rerun(
    "sdg-abc123",
    StackDeploymentGroupRerunOptions(deployments=["dev", "staging"]),
)
```

---

## Stack deployment group summaries (`client.stack_deployment_group_summaries`)

Per-group rollup of run counts within a configuration — one record per
deployment group, with `status_counts` broken down by run status.

| Method | Purpose |
|---|---|
| `client.stack_deployment_group_summaries.list(configuration_id, options=None)` | Iterate group summaries for a configuration. |

```python
for summary in client.stack_deployment_group_summaries.list("stc-abc123"):
    print(summary.name, summary.status)
    if summary.status_counts:
        c = summary.status_counts
        print(
            f"  pending={c.pending} deploying={c.deploying} "
            f"succeeded={c.succeeded} failed={c.failed}"
        )
```

---

## Stack deployment runs (`client.stack_deployment_runs`)

A deployment run is the individual plan + apply execution within a deployment
group. Each run progresses through statuses such as `pre-deploying`,
`deploying`, `pending-operator`, `succeeded`, or `failed`.

| Method | Purpose |
|---|---|
| `client.stack_deployment_runs.list(group_id, options=None)` | Iterate runs for a deployment group. |
| `client.stack_deployment_runs.read(run_id, options=None)` | Read a run, optionally with included relationships. |
| `client.stack_deployment_runs.approve_all_plans(run_id)` | Approve all pending plan steps in the run. |
| `client.stack_deployment_runs.cancel(run_id)` | Cancel an in-progress run. |

```python
from pytfe.models import StackDeploymentRunIncludeOpt, StackDeploymentRunReadOptions

# List runs in a deployment group
for run in client.stack_deployment_runs.list("sdg-abc123"):
    print(run.id, run.status)

# Read with relationships
run = client.stack_deployment_runs.read(
    "sdr-abc123",
    StackDeploymentRunReadOptions(
        include=[StackDeploymentRunIncludeOpt.STACK_DEPLOYMENT_GROUP]
    ),
)

# Cancel
client.stack_deployment_runs.cancel("sdr-abc123")
```

---

## Stack deployment steps (`client.stack_deployment_steps`)

Steps are the granular plan and apply operations within a run. A step in
`pending-operator` status requires an explicit `advance()` call before the
deployment can proceed — this is the operator approval gate.

| Method | Purpose |
|---|---|
| `client.stack_deployment_steps.list(run_id, options=None)` | Iterate steps for a run. |
| `client.stack_deployment_steps.read(step_id, options=None)` | Read a step, optionally with included relationships. |
| `client.stack_deployment_steps.advance(step_id)` | Approve a `pending-operator` step to allow it to proceed. |
| `client.stack_deployment_steps.list_diagnostics(step_id, options=None)` | Iterate diagnostics attached to a step. |
| `client.stack_deployment_steps.download_artifact(step_id, artifact_type)` | Download a step artifact as raw bytes. |

Artifact types: `PLAN_DESCRIPTION`, `APPLY_DESCRIPTION`, `PLAN_DEBUG_LOG`,
`APPLY_DEBUG_LOG`.

```python
from pytfe.models import StackDeploymentStepArtifactType

for step in client.stack_deployment_steps.list("sdr-abc123"):
    print(step.id, step.operation_type, step.status)

# Advance a step waiting for operator approval
client.stack_deployment_steps.advance("sds-abc123")

# Download the plan description
plan_bytes = client.stack_deployment_steps.download_artifact(
    "sds-abc123",
    StackDeploymentStepArtifactType.PLAN_DESCRIPTION,
)
print(plan_bytes.decode())

# List diagnostics for a failed step
for diag in client.stack_deployment_steps.list_diagnostics("sds-abc123"):
    print(diag.id, diag.severity, diag.summary)
```

---

## Stack states (`client.stack_states`)

A stack state captures the Terraform state snapshot for one deployment at a
point in time. The `is_current` flag identifies the live state for each
deployment. Each state carries a `components` list describing which stack
components contributed to the snapshot.

| Method | Purpose |
|---|---|
| `client.stack_states.list(stack_id, options=None)` | Iterate all state snapshots for a stack across all deployments. |
| `client.stack_states.read(state_id)` | Read a single state snapshot. |
| `client.stack_states.download_description(state_id)` | Download the raw state description bytes. |

```python
from pytfe.models import StackStateListOptions

# Current state per deployment
for state in client.stack_states.list("st-abc123"):
    if state.is_current:
        print(
            state.id,
            f"deployment={state.deployment}",
            f"resources={state.resource_instance_count}",
        )
        for comp in state.components:
            print(f"  component={comp.address}")

# Download raw state description (treat as sensitive)
raw = client.stack_states.download_description("sts-abc123")
```

The description bytes are a JSON blob containing resource instance details.
Treat them as sensitive — they may contain provider credentials or other
secret material.

---

## Stack diagnostics (`client.stack_diagnostics`)

Diagnostics are error or warning records attached to a configuration or a
deployment step. They surface problems such as provider checksum mismatches,
deprecated filename extensions, or validation failures. Acknowledging a
diagnostic marks it as reviewed.

Diagnostic IDs use the `std-` prefix.

| Method | Purpose |
|---|---|
| `client.stack_diagnostics.read(diagnostic_id)` | Read a stack diagnostic. |
| `client.stack_diagnostics.acknowledge(diagnostic_id)` | Acknowledge a diagnostic (mark as reviewed). |

```python
diag = client.stack_diagnostics.read("std-abc123")
print(diag.severity, diag.summary)
print(diag.detail)

# diags is populated when the server rolls up multiple sub-diagnostics
if diag.diags:
    for nested in diag.diags:
        print(" ", nested.get("severity"), nested.get("summary"))

if not diag.acknowledged:
    client.stack_diagnostics.acknowledge("std-abc123")
```
