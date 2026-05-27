# Run tasks

Run tasks integrate external systems into the run lifecycle. pyTFE supports
organization run tasks, workspace run task attachments, run task webhook
callbacks, task stages, and task results.

Upstream docs:

- Run tasks: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run-tasks/run-tasks
- Run task stages and results: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run-tasks/run-task-stages-and-results
- Run task integration: https://developer.hashicorp.com/terraform/enterprise/api-docs/run-tasks/run-tasks-integration

Examples:

- [run_task.py](../../examples/run_task.py)
- [workspace_run_task.py](../../examples/workspace_run_task.py)
- [run_task_integration.py](../../examples/run_task_integration.py)
- [task_stage_example.py](../../examples/task_stage_example.py)
- [task_result.py](../../examples/task_result.py)

## Organization run tasks

| Method | Purpose |
|---|---|
| `client.run_tasks.list(organization, options=None)` | Iterate run tasks in an organization. |
| `client.run_tasks.read(task_id)` | Read a run task. |
| `client.run_tasks.read_with_options(task_id, options)` | Read with included relationships. |
| `client.run_tasks.create(organization, options)` | Create a run task. |
| `client.run_tasks.update(task_id, options)` | Update a run task. |
| `client.run_tasks.delete(task_id)` | Delete a run task. |

```python
from pytfe.models import RunTaskCreateOptions

task = client.run_tasks.create(
    "my-organization",
    RunTaskCreateOptions(
        name="security-check",
        url="https://example.com/tfc/run-task",
        category="task",
        enabled=True,
    ),
)

print(task.id)
```

## Workspace run task attachments

Attach an organization run task to a workspace with
`client.workspace_run_tasks`:

```python
from pytfe.models import (
    RunTask,
    Stage,
    TaskEnforcementLevel,
    WorkspaceRunTaskCreateOptions,
)

attachment = client.workspace_run_tasks.create(
    "ws-abc123",
    WorkspaceRunTaskCreateOptions(
        enforcement_level=TaskEnforcementLevel.MANDATORY,
        run_task=RunTask(id="task-abc123"),
        stages=[Stage.PRE_PLAN],
    ),
)

print(attachment.id)
```

Stage enum values must match the API wire values. Do not convert documented
stage names to a different spelling.

## Integration callbacks

Run task callback handling is exposed through `client.run_task_integrations`.
The callback URL and token come from a run task webhook payload:

```python
from pytfe.models import TaskResultCallbackRequestOptions, TaskResultStatus


client.run_task_integrations.callback(
    callback_url,
    access_token,
    TaskResultCallbackRequestOptions(
        status=TaskResultStatus.passed,
        message="Checks passed",
    ),
)
```

## Task stages and results

Use `client.task_stages` and `client.task_results` for stage-level inspection
and overrides:

```python
stage = client.task_stages.read("ts-abc123")
result = client.task_results.read("taskrs-abc123")
```
