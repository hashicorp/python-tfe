# Getting started

pyTFE is a Python client for the HCP Terraform and Terraform Enterprise API v2.
The client exposes one `TFEClient` object with resource services such as
`client.workspaces`, `client.runs`, and `client.state_versions`.

## Install

```bash
pip install pytfe
```

For local development from this repository:

```bash
pip install -e .[dev]
```

## Configure credentials

The quickest setup is environment variables:

```bash
export TFE_TOKEN="your-api-token"
export TFE_ADDRESS="https://app.terraform.io"
```

`TFE_ADDRESS` defaults to `https://app.terraform.io`, so HCP Terraform users
usually only need `TFE_TOKEN`. Terraform Enterprise users should set
`TFE_ADDRESS` to the base URL of their self-hosted instance, for example
`https://tfe.example.com`. Do not include `/api/v2`; pyTFE adds API paths.

For HCP Terraform Europe, use the address shown for your organization, commonly
`https://app.eu.terraform.io`.

## Create a client

With environment variables:

```python
from pytfe import TFEClient

client = TFEClient()
```

With explicit configuration:

```python
from pytfe import TFEClient, TFEConfig

config = TFEConfig(
    address="https://app.terraform.io",
    token="your-api-token",
    timeout=30.0,
)
client = TFEClient(config)
```

Explicit `TFEConfig(...)` values are useful in applications that manage more
than one HCP Terraform or Terraform Enterprise instance.

## First API call

List the organizations visible to the token:

```python
from pytfe import TFEClient

client = TFEClient()

for organization in client.organizations.list():
    print(organization.name)
```

List workspaces in an organization:

```python
from pytfe import TFEClient

client = TFEClient()

for workspace in client.workspaces.list("my-organization"):
    print(workspace.id, workspace.name)
```

All methods named `list` or `list_*` return iterators. Use `list(...)` when you
need a concrete Python list:

```python
workspaces = list(client.workspaces.list("my-organization"))
print(f"found {len(workspaces)} workspaces")
```

See [pagination.md](pagination.md) for details.

## Common next steps

- [authentication.md](authentication.md) documents supported environment
  variables, token types, TLS settings, and explicit `TFEConfig` fields.
- [pagination.md](pagination.md) explains list iterators and page-size options.
- [api/index.md](api/index.md) maps `TFEClient` attributes to pyTFE resources,
  examples, and upstream HCP Terraform API docs.
- [scenarios/api-driven-run.md](scenarios/api-driven-run.md) walks through a
  full API-driven run from configuration upload to final status.
- [troubleshooting.md](troubleshooting.md) covers auth, permissions,
  pagination, TLS, retries, and debug logging.
- [../examples](../examples) contains runnable scripts for common workflows.
