# Scenario: Stack deployment lifecycle

This scenario walks through the complete operational lifecycle of an HCP
Terraform Stack: from watching a configuration converge, through monitoring
deployment group progress, approving operator-gated plan steps, to reading the
final state and handling diagnostics.

Upstream docs:

- Stacks: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/stacks/stacks
- Stack configurations: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/stacks/stack-configurations
- Stack deployment groups: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/stacks/stack-deployment-groups
- Stack deployment runs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/stacks/stack-deployment-runs
- Stack deployment steps: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/stacks/stack-deployment-steps
- Stack states: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/stacks/stack-states

## Prerequisites

```bash
export TFE_TOKEN="your-api-token"
export TFE_ADDRESS="https://app.terraform.io"
```

The token needs permission to read and manage the stack and its deployments.

---

## 1. Read a stack and its latest configuration

```python
import os
from pytfe import TFEClient

client = TFEClient()
stack_id = "st-abc123"

stack = client.stacks.read(stack_id)
print(stack.name, stack.deployment_names)

# Get the most recent configuration (list returns newest first)
configs = list(client.stack_configurations.list(stack_id))
latest_config = configs[0] if configs else None
if latest_config:
    print(latest_config.id, latest_config.status, latest_config.sequence_number)
```

If the configuration `status` is `errored`, check diagnostics before
proceeding (see section 6).

---

## 2. Watch configuration summaries for an overview

Configuration summaries give a quick view of each configuration's health
without fetching every individual configuration or deployment group.

```python
from pytfe.models import StackConfigurationSummaryListOptions

for summary in client.stack_configuration_summaries.list(stack_id):
    print(f"seq={summary.sequence_number}  status={summary.status}")
    if summary.group_status_summary:
        g = summary.group_status_summary
        print(f"  groups: succeeded={g.succeeded} failed={g.failed}")
    if summary.run_status_summary:
        r = summary.run_status_summary
        print(f"  runs:   succeeded={r.succeeded} failed={r.failed}")
    # Stop after the most recent few
    break
```

---

## 3. List deployment groups and their status

Each deployment group coordinates one named environment (e.g. `dev`) within a
configuration. A `succeeded` group means all its runs finished cleanly.

```python
config_id = latest_config.id

for group in client.stack_deployment_groups.list(config_id):
    print(group.id, group.name, group.status)
```

For a compact view using summaries:

```python
for summary in client.stack_deployment_group_summaries.list(config_id):
    c = summary.status_counts
    if c:
        print(
            f"{summary.name}: succeeded={c.succeeded} failed={c.failed} "
            f"pending={c.pending} deploying={c.deploying}"
        )
```

---

## 4. Inspect runs and advance operator-gated steps

A deployment run goes through plan and apply steps. If a step reaches
`pending-operator`, the deployment is paused for approval. Call `advance()` to
allow the step to continue.

```python
from pytfe.models import DeploymentStepStatus

group = client.stack_deployment_groups.read_by_name(config_id, "dev")

for run in client.stack_deployment_runs.list(group.id):
    print(f"run {run.id}  status={run.status}")

    for step in client.stack_deployment_steps.list(run.id):
        print(f"  step {step.id}  op={step.operation_type}  status={step.status}")

        if step.status == DeploymentStepStatus.PENDING_OPERATOR:
            print("  → advancing operator-gated step")
            client.stack_deployment_steps.advance(step.id)
```

To approve all pending plans in a group at once (skipping per-step iteration):

```python
client.stack_deployment_groups.approve_all_plans(group.id)
```

---

## 5. Download plan and apply artifacts

Plan and apply descriptions give a human-readable summary of proposed and
applied changes. Debug logs provide full Terraform output.

```python
from pytfe.models import StackDeploymentStepArtifactType

for step in client.stack_deployment_steps.list(run.id):
    if step.operation_type == "plan":
        plan_bytes = client.stack_deployment_steps.download_artifact(
            step.id, StackDeploymentStepArtifactType.PLAN_DESCRIPTION
        )
        print(plan_bytes.decode())
    elif step.operation_type == "apply":
        apply_bytes = client.stack_deployment_steps.download_artifact(
            step.id, StackDeploymentStepArtifactType.APPLY_DESCRIPTION
        )
        print(apply_bytes.decode())
```

---

## 6. Handle diagnostics on configuration errors

When a configuration's `status` is `errored`, diagnostics explain what went
wrong. They are also attached to individual deployment steps via
`list_diagnostics`.

```python
# Diagnostics from a configuration (fetched via its relationships URL)
# Use the read endpoint to get the diagnostic ID, then read it directly:
diag = client.stack_diagnostics.read("std-abc123")
print(diag.severity, diag.summary)
print(diag.detail)

# Nested sub-diagnostics (present when the server rolls up multiple warnings)
if diag.diags:
    for nested in diag.diags:
        print(" ", nested.get("severity"), nested.get("summary"))

# Acknowledge after review
if not diag.acknowledged:
    client.stack_diagnostics.acknowledge(diag.id)
```

Diagnostics from a failed deployment step:

```python
for diag in client.stack_deployment_steps.list_diagnostics(step.id):
    print(diag.id, diag.severity, diag.summary)
    if not diag.acknowledged:
        client.stack_diagnostics.acknowledge(diag.id)
```

---

## 7. Read current stack state

After a successful deployment, each environment has a current state snapshot
containing the resource instances that were applied.

```python
for state in client.stack_states.list(stack_id):
    if not state.is_current:
        continue
    print(
        f"deployment={state.deployment}  "
        f"resources={state.resource_instance_count}  "
        f"gen={state.generation}"
    )
    for comp in state.components:
        print(f"  component={comp.address}  resources={comp.resource_instance_count}")
```

To download the raw state description for a specific environment:

```python
# Find the current state for "dev"
dev_state = next(
    (s for s in client.stack_states.list(stack_id) if s.is_current and s.deployment == "dev"),
    None,
)

if dev_state:
    raw = client.stack_states.download_description(dev_state.id)
    # raw is a JSON blob — treat as sensitive
    print(f"downloaded {len(raw)} bytes for {dev_state.deployment}")
```

The description bytes may contain provider credentials or other sensitive
resource attributes. Do not log or commit them.

---

## 8. Rerun failed deployments

If specific deployments in a group failed, rerun them without touching the
ones that succeeded.

```python
from pytfe.models import StackDeploymentGroupRerunOptions

client.stack_deployment_groups.rerun(
    group.id,
    StackDeploymentGroupRerunOptions(deployments=["dev"]),
)
```
