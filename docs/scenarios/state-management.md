# Scenario: State management

Terraform state can contain provider credentials, resource attributes, outputs,
and other sensitive values. Treat any downloaded state bytes as secret material.
Do not log state, commit state to source control, or store state in CI artifacts.

Upstream docs:

- State versions: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/state-versions
- State version outputs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/state-version-outputs

## Read current state metadata

```python
from pytfe import TFEClient


client = TFEClient()
workspace_id = "ws-abc123"

current = client.state_versions.read_current(workspace_id)
print(current.id, current.serial, current.status)
```

## Download current state bytes

```python
raw_state = client.state_versions.download_current(workspace_id)
print(f"downloaded {len(raw_state)} bytes")
```

The returned bytes are the raw state file. Keep them in memory when possible.
If you must write them to disk, use restricted permissions and remove the file
after use.

## List outputs

```python
for output in client.state_versions.list_outputs(current.id):
    print(output.name, output.sensitive)
```

For current workspace outputs:

```python
for output in client.state_version_outputs.read_current(workspace_id):
    print(output.name, output.sensitive)
```

Do not print sensitive output values.

## Upload state

Uploading state is an advanced operation. Prefer normal Terraform runs when
possible.

```python
import hashlib

from pytfe.models import StateVersionCreateOptions, WorkspaceLockOptions


raw_state = b"{... raw terraform state json ...}"

new_state = client.state_versions.upload(
    workspace_id,
    raw_state=raw_state,
    options=StateVersionCreateOptions(
        serial=43,
        md5=hashlib.md5(raw_state).hexdigest(),
    ),
)

print(new_state.id, new_state.status)
```

Use a serial number newer than the current state. Depending on server timing,
the returned state version may still be processing.

## Roll back a workspace

Rollback duplicates an older state version and makes the copy current. The
workspace must be locked by the caller first.

```python
client.workspaces.lock(
    workspace_id,
    WorkspaceLockOptions(reason="Rollback state with pyTFE"),
)

try:
    rolled_back = client.state_versions.rollback(
        workspace_id,
        "sv-previous123",
    )
    print(rolled_back.id)
finally:
    client.workspaces.unlock(workspace_id)
```

Use rollback only with an explicit operational reason and a recovery plan.
