# Scenario: API-driven run

This scenario shows the common API-driven workflow:

1. Create or read a workspace.
2. Create a configuration version.
3. Upload Terraform configuration.
4. Queue a run using that configuration version.
5. Wait for the plan.
6. Read plan JSON output.
7. Apply the run.
8. Read the final run status.

Upstream docs:

- Configuration versions: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/configuration-versions
- Runs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run
- Plans: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/plans
- Applies: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/applies

## Prerequisites

Set authentication and choose an organization:

```bash
export TFE_TOKEN="your-api-token"
export TFE_ADDRESS="https://app.terraform.io"
export TFE_ORG="my-organization"
```

The token needs permission to create or update the workspace, create
configuration versions, queue runs, and apply runs.

## End-to-end example

```python
import os
import time
from pathlib import Path

from pytfe import TFEClient
from pytfe.models import (
    ConfigurationVersion,
    ConfigurationVersionCreateOptions,
    RunApplyOptions,
    RunCreateOptions,
    Workspace,
    WorkspaceCreateOptions,
)
from pytfe.errors import TFEError


client = TFEClient()
organization = os.environ["TFE_ORG"]
workspace_name = "pytfe-api-driven-example"
terraform_dir = Path("./terraform")


def read_or_create_workspace() -> Workspace:
    try:
        return client.workspaces.read(organization, workspace_name)
    except TFEError:
        return client.workspaces.create(
            organization,
            WorkspaceCreateOptions(name=workspace_name),
        )


workspace = read_or_create_workspace()

config_version = client.configuration_versions.create(
    workspace.id,
    ConfigurationVersionCreateOptions(auto_queue_runs=False),
)

if not config_version.upload_url:
    raise RuntimeError("configuration version did not include an upload URL")

client.configuration_versions.upload(config_version.upload_url, str(terraform_dir))

run = client.runs.create(
    RunCreateOptions(
        workspace=Workspace(id=workspace.id),
        configuration_version=ConfigurationVersion(id=config_version.id),
        message="Queued by pyTFE",
    )
)

terminal_statuses = {"applied", "errored", "canceled", "discarded"}
plan_ready_statuses = {
    "planned",
    "planned_and_finished",
    "planned_and_saved",
    "policy_checked",
    "policy_soft_failed",
    "cost_estimated",
}

while True:
    run = client.runs.read(run.id)
    status = run.status.value if run.status else ""
    print("run status:", status)

    if status in plan_ready_statuses or status in terminal_statuses:
        break

    time.sleep(5)

plan_json = client.plans.read_json_output_for_run(run.id)
print("plan format:", plan_json.get("format_version"))

if (run.status.value if run.status else "") not in terminal_statuses:
    client.runs.apply(run.id, RunApplyOptions(comment="Applied by pyTFE"))

while True:
    run = client.runs.read(run.id)
    status = run.status.value if run.status else ""
    print("run status:", status)

    if status in terminal_statuses:
        break

    time.sleep(5)

print("final status:", run.status)
```

## Notes

- `ConfigurationVersionCreateOptions(auto_queue_runs=False)` keeps the example
  explicit: the code uploads configuration first, then queues a run.
- `configuration_versions.upload(upload_url, path)` packages the directory into
  a tar gzip archive and uploads it to the hosted upload URL.
- Plan JSON endpoints may redirect to signed blob URLs. pyTFE follows those
  redirects internally.
- Always add cleanup if this runs in CI or repeated integration tests.

