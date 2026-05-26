# Runs, plans, and applies

Runs represent the lifecycle of a Terraform operation. A run can have a plan,
an apply, policy checks, task stages, comments, events, and a configuration
version.

Upstream docs:

- Runs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run
- Plans: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/plans
- Applies: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/applies
- Configuration versions: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/configuration-versions

Examples:

- [run.py](../../examples/run.py)
- [plan.py](../../examples/plan.py)
- [apply.py](../../examples/apply.py)
- [configuration_version.py](../../examples/configuration_version.py)

## Common run methods

| Method | Purpose |
|---|---|
| `client.runs.list(workspace_id, options=None)` | Iterate runs for a workspace. |
| `client.runs.list_for_organization(organization, options=None)` | Iterate runs across an organization. |
| `client.runs.read(run_id)` | Read a run. |
| `client.runs.read_with_options(run_id, options)` | Read with included relationships. |
| `client.runs.create(options)` | Queue a run. |
| `client.runs.apply(run_id, options=None)` | Confirm/apply a run. |
| `client.runs.cancel(run_id, options=None)` | Cancel a run. |
| `client.runs.force_cancel(run_id, options=None)` | Force-cancel a run. |
| `client.runs.discard(run_id, options=None)` | Discard a run. |

## List workspace runs

```python
from pytfe import TFEClient
from pytfe.models import RunListOptions

client = TFEClient()

options = RunListOptions(page_size=50, status="planned")

for run in client.runs.list("ws-abc123", options):
    print(run.id, run.status)
```

## Read a run with relationships

```python
from pytfe.models import RunIncludeOpt, RunReadOptions

run = client.runs.read_with_options(
    "run-abc123",
    RunReadOptions(include=[RunIncludeOpt.RUN_WORKSPACE, RunIncludeOpt.RUN_PLAN]),
)

print(run.workspace.id if run.workspace else None)
print(run.plan.id if run.plan else None)
```

## Queue a run

```python
from pytfe.models import RunCreateOptions, Workspace

run = client.runs.create(
    RunCreateOptions(
        workspace=Workspace(id="ws-abc123"),
        message="Queued by pyTFE",
    )
)

print(run.id)
```

## Plans and JSON output

```python
plan = client.plans.read_for_run("run-abc123")
json_output = client.plans.read_json_output_for_run("run-abc123")

print(plan.id)
print(json_output.get("format_version"))
```

Plan JSON output and schema endpoints may redirect to signed blob URLs. pyTFE
handles those redirects internally.

## Applies and errored state

```python
apply = client.applies.read("apply-abc123")
logs = client.applies.logs(apply.id)

try:
    errored_state = client.applies.errored_state(apply.id)
except Exception:
    errored_state = None
```

`errored_state` is only available for applies that failed during state upload.
The API returns `404` when there is no recoverable errored state.

