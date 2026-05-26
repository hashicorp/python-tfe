# State versions

State versions represent Terraform state snapshots stored by HCP Terraform or
Terraform Enterprise. Use this API carefully: state can contain sensitive
values.

Upstream docs:

- State versions: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/state-versions
- State version outputs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/state-version-outputs

Example: [state_versions.py](../../examples/state_versions.py)

## Common methods

| Method | Purpose |
|---|---|
| `client.state_versions.list(options=None)` | Iterate state versions with optional organization/workspace filters. |
| `client.state_versions.read(state_version_id)` | Read a state version. |
| `client.state_versions.read_current(workspace_id)` | Read the current state version for a workspace. |
| `client.state_versions.create(workspace, options, organization=None)` | Create a state-version record. |
| `client.state_versions.upload(...)` | Create a state version and upload raw state bytes. |
| `client.state_versions.download(state_version_id)` | Download raw state bytes. |
| `client.state_versions.download_current(workspace_id)` | Download current raw state bytes. |
| `client.state_versions.list_outputs(state_version_id, options=None)` | Iterate outputs for a state version. |
| `client.state_versions.rollback(workspace_id, state_version_id)` | Roll a workspace back to an earlier state version. |
| `client.state_version_outputs.read(output_id)` | Read a single output. |
| `client.state_version_outputs.read_current(workspace_id, options=None)` | Iterate current outputs for a workspace. |

## List state versions

```python
from pytfe import TFEClient
from pytfe.models import StateVersionListOptions

client = TFEClient()

options = StateVersionListOptions(
    organization="my-organization",
    workspace="example-workspace",
    page_size=50,
)

for state_version in client.state_versions.list(options):
    print(state_version.id, state_version.serial, state_version.status)
```

## Read or download current state

```python
current = client.state_versions.read_current("ws-abc123")
raw_state = client.state_versions.download_current("ws-abc123")

print(current.id)
print(len(raw_state))
```

Downloaded state bytes should be treated as sensitive.

## Upload state

```python
import hashlib

from pytfe.models import StateVersionCreateOptions

raw_state = b"{... terraform state json ...}"

state_version = client.state_versions.upload(
    "ws-abc123",
    raw_state=raw_state,
    options=StateVersionCreateOptions(
        serial=42,
        md5=hashlib.md5(raw_state).hexdigest(),
    ),
)

print(state_version.id, state_version.status)
```

`upload` follows the API's hosted upload URL workflow and returns a refreshed
state-version object. Depending on server timing, the returned state version may
still be processing.

## Roll back a workspace

```python
rolled_back = client.state_versions.rollback(
    "ws-abc123",
    "sv-previous123",
)

print(rolled_back.id)
```

The workspace must be locked by the caller before rollback; otherwise the API
returns a conflict.
