# Scenario: Recover from an errored apply

When an apply fails after Terraform has already mutated real infrastructure but
before the new state file is uploaded, HCP Terraform stores the in-flight state
on the apply record. The workspace's current state still points at the old
version, so re-running Terraform without recovery will either replay destructive
changes or report drift it cannot reconcile.

This scenario walks through the recovery path:

1. Detect that an apply finished in `errored` and has recoverable errored state.
2. Download the errored state bytes.
3. Inspect or repair the state locally.
4. Upload the repaired state as the workspace's new current state version.

Upstream docs:

- Applies: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/applies
- State versions: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/state-versions
- Manipulating Terraform state: https://developer.hashicorp.com/terraform/cli/state

## Prerequisites

- A workspace with an apply in `errored` status.
- A token with workspace write access and permission to upload state versions.
- The workspace must be locked by the same caller before uploading state.

```bash
export TFE_TOKEN="your-api-token"
export TFE_ADDRESS="https://app.terraform.io"
```

## Step 1: Download the errored state

```python
from pytfe import TFEClient
from pytfe.errors import NotFound


client = TFEClient()
apply_id = "apply-abc123"

try:
    errored_state = client.applies.errored_state(apply_id)
except NotFound:
    errored_state = None

if errored_state is None:
    raise SystemExit("apply has no recoverable errored state")

print(f"downloaded {len(errored_state)} bytes")
```

`applies.errored_state` returns the raw bytes of the state file Terraform was
about to upload when the apply failed. `NotFound` means the apply either
succeeded, failed before any state was produced, or has already been recovered.

Treat the returned bytes as secret. Do not log them or commit them to source
control.

## Step 2: Inspect or repair the state locally

Write the state to a temporary file with restricted permissions and use the
Terraform CLI to inspect or surgically edit it:

```python
import os
import tempfile

with tempfile.NamedTemporaryFile(
    prefix="errored-",
    suffix=".tfstate",
    delete=False,
) as fh:
    os.chmod(fh.name, 0o600)
    fh.write(errored_state)
    statefile_path = fh.name

print(f"wrote state to {statefile_path}")
```

Typical local commands:

```bash
terraform show -json "$statefile_path" | jq '.values.root_module.resources[].address'
terraform state list -state="$statefile_path"
terraform state rm -state="$statefile_path" 'aws_instance.removed_by_mistake'
```

Always make a backup copy before editing. State surgery is irreversible.

## Step 3: Upload the repaired state

The workspace must be locked by the caller before uploading state. Read the
current serial first and use a strictly greater serial for the new version.

```python
import hashlib
from pathlib import Path

from pytfe.models import StateVersionCreateOptions, WorkspaceLockOptions


workspace_id = "ws-abc123"

repaired = Path(statefile_path).read_bytes()

current = client.state_versions.read_current(workspace_id)
new_serial = (current.serial or 0) + 1

client.workspaces.lock(
    workspace_id,
    WorkspaceLockOptions(reason="Recover errored apply state via pyTFE"),
)

try:
    new_state = client.state_versions.upload(
        workspace_id,
        raw_state=repaired,
        options=StateVersionCreateOptions(
            serial=new_serial,
            md5=hashlib.md5(repaired).hexdigest(),
        ),
    )
    print("uploaded", new_state.id, new_state.status)
finally:
    client.workspaces.unlock(workspace_id)
    os.unlink(statefile_path)
```

`state_versions.upload` follows the API's hosted upload-URL workflow: create the
state-version record, `PUT` the raw bytes to the signed Archivist URL, then
read the version back. Depending on server timing the returned version may
still be processing; poll `read` if you need to wait for `finalized`.

## Step 4: Confirm the next run sees the repaired state

After unlocking, queue a no-op plan to confirm Terraform sees the recovered
state:

```python
from pytfe.models import RunCreateOptions, Workspace

run = client.runs.create(
    RunCreateOptions(
        workspace=Workspace(id=workspace_id),
        message="Verify errored-state recovery",
        is_destroy=False,
    )
)
print("verification run:", run.id)
```

A plan that shows zero changes confirms recovery succeeded. A plan with
unexpected creates or destroys means the repaired state still diverges from
reality; do not apply until the divergence is understood.

## Operational notes

- Always lock the workspace before uploading state. The API returns `409` if
  the workspace is unlocked or locked by a different caller.
- Pick a `serial` strictly greater than the current state's serial. Reusing or
  decreasing the serial is rejected.
- Keep the downloaded bytes out of logs, CI artifacts, and long-lived disk.
  Remove the temporary file in a `finally` block.
- Recovery is a manual operational action. Pair it with an incident note and a
  follow-up to investigate why the apply failed mid-upload.
