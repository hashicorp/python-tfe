# Scenario: Run task integration

Run tasks let HCP Terraform call an external service during the run lifecycle.
pyTFE supports managing run tasks, attaching them to workspaces, sending
callback responses, and reading task stages/results.

Upstream docs:

- Run tasks: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run-tasks/run-tasks
- Run task integration: https://developer.hashicorp.com/terraform/enterprise/api-docs/run-tasks/run-tasks-integration
- Run task stages and results: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run-tasks/run-task-stages-and-results

## Create a run task

```python
from pytfe import TFEClient
from pytfe.models import (
    RunTask,
    RunTaskCreateOptions,
    Stage,
    TaskEnforcementLevel,
    TaskResultCallbackRequestOptions,
    TaskResultStatus,
    WorkspaceRunTaskCreateOptions,
)


client = TFEClient()

task = client.run_tasks.create(
    "my-organization",
    RunTaskCreateOptions(
        name="external-security-check",
        description="Example external check",
        url="https://example.com/tfc/run-task",
        category="task",
        hmac_key="shared-secret",
        enabled=True,
    ),
)
```

## Attach the task to a workspace

```python
workspace_task = client.workspace_run_tasks.create(
    "ws-abc123",
    WorkspaceRunTaskCreateOptions(
        enforcement_level=TaskEnforcementLevel.MANDATORY,
        run_task=RunTask(id=task.id),
        stages=[Stage.PRE_PLAN],
    ),
)

print(workspace_task.id)
```

Stage enum values should match the API contract. Check upstream docs and go-tfe
when adding or changing stage handling.

## Send a callback response

When HCP Terraform triggers the run task, it sends your service a request body
that includes a callback URL and callback access token. Use those values for the
callback; do not use the SDK client's normal `TFE_TOKEN`.

```python
client.run_task_integrations.callback(
    callback_url,
    callback_access_token,
    TaskResultCallbackRequestOptions(
        status=TaskResultStatus.passed,
        message="External check passed",
        url="https://example.com/results/123",
    ),
)
```

## Inspect task stages and results

```python
for stage in client.task_stages.list("run-abc123"):
    print(stage.id, stage.stage, stage.status)

stage = client.task_stages.read("ts-abc123")
result = client.task_results.read("taskrs-abc123")
```

If a stage is awaiting override and your token has permission:

```python
client.task_stages.override("ts-abc123", "Approved by platform team")
```

## Security notes

- Verify webhook signatures in your run task service.
- Store the HMAC key in a secret manager.
- Use the callback access token only for the callback request.
- Do not log webhook payloads if they may contain sensitive plan data.

