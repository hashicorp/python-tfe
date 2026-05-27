# HCP Terraform and Terraform Enterprise **Python** Client (pyTFE)

[![PyPI](https://img.shields.io/pypi/v/pytfe.svg)](https://pypi.org/project/pytfe/)
[![Python Versions](https://img.shields.io/pypi/pyversions/pytfe.svg)](https://pypi.org/project/pytfe/)
[![Test](https://github.com/hashicorp/python-tfe/actions/workflows/test.yml/badge.svg)](https://github.com/hashicorp/python-tfe/actions/workflows/test.yml)
[![License](https://img.shields.io/github/license/hashicorp/python-tfe.svg)](./LICENSE)
[![Issues](https://img.shields.io/github/issues/hashicorp/python-tfe.svg)](https://github.com/hashicorp/python-tfe/issues)

The official **Python** API client for [HCP Terraform and Terraform Enterprise](https://www.hashicorp.com/products/terraform).

This client targets the [HCP Terraform V2 API](https://developer.hashicorp.com/terraform/cloud-docs/api-docs).
As Terraform Enterprise is the self-hosted distribution of HCP Terraform, this client supports both **HCP Terraform** and **Terraform Enterprise** use cases. In this repository and API, we refer to the platform generically as *Terraform Enterprise* unless a feature is explicitly called out as only supported in one or the other (rare).

## Version Information

We follow Semantic Versioning. During the initial alpha period we use `0.y.z`:
- **Minor** (`0.y.z → 0.(y+1).z`): new, backwards-compatible features and enhancements.
- **Patch** (`0.y.z → 0.y.(z+1)`): bug fixes and performance improvements.
- Occasionally, a function signature change that fixes incorrect behavior may appear in a minor version.

## Example Usage

Construct a new **pyTFE** client, then use the resource services on the client to access different parts of the Terraform Enterprise API. The following example lists all organizations.

### (Recommended) Using explicit config

```python
from pytfe import TFEClient, TFEConfig

config = TFEConfig(
    address="https://tfe.local",
    token="insert-your-token-here",
    timeout=30.0,
    user_agent_suffix="example-app/0.1 pytfe/0.1",
)

client = TFEClient(config)

for org in client.organizations.list():
    print(org.name)
```

### Using the default config with environment variables

The default configuration reads the `TFE_ADDRESS` and `TFE_TOKEN` environment variables.

1. `TFE_ADDRESS` — URL of an HCP Terraform or Terraform Enterprise instance. Example: `https://tfe.local`  
2. `TFE_TOKEN` — An [API token](https://developer.hashicorp.com/terraform/cloud-docs/users-teams-organizations/api-tokens) for the HCP Terraform or Terraform Enterprise instance.


Environment variables are used as a fallback when `address` or `token` are not provided explicitly:

#### Using the default configuration
```python
from pytfe import TFEClient, TFEConfig

# Equivalent to providing no values; falls back to env vars if set.
client = TFEClient(TFEConfig())
for org in client.organizations.list():
    print(org.name)
```

#### When host or token is empty
```python
from pytfe import TFEClient, TFEConfig

config = TFEConfig(address="", token="")
client = TFEClient(config)

for org in client.organizations.list():
    print(org.name)
```

## Listing resources

Anything named `list` or `list_*` on a resource service returns an **iterator**, not a Python `list`. Pagination is handled for you under the hood — the iterator keeps fetching pages from the API until there are no more. This mirrors the underlying HCP Terraform API, where every list endpoint is paginated (`page[number]` / `page[size]`), and keeps memory flat even when an organization has thousands of workspaces or runs.

You'll use it one of two ways:

```python
# Stream — handy when you might break early or when results are large
for ws in client.workspaces.list("my-org"):
    if ws.name.startswith("prod-"):
        print(ws.id, ws.name)

# Materialize — when you actually want a list to index, len(), or pass around
workspaces = list(client.workspaces.list("my-org"))
print(f"found {len(workspaces)} workspaces")
```

A couple of things worth knowing:

- The iterator is **single-use**. Once you've walked it, iterating again gives you nothing. Capture it with `list(...)` first if you need to reuse the result.
- Filters and page size live on the `*ListOptions` model for each resource — e.g. `WorkspaceListOptions(search="prod", page_size=50)`. Pagination still happens transparently; `page_size` only controls how big each underlying API page is.

## Logging

pyTFE integrates with Python's standard `logging` module and is **silent by default** — nothing is emitted unless you opt in. The library publishes two loggers:

- `pytfe`           — root namespace; rarely emits directly
- `pytfe.transport` — HTTP request/response and retry trace

### Turn it on with an environment variable

The quickest way is to set `PYTFE_LOG`:

```bash
PYTFE_LOG=debug python my_script.py
```

`setup_logging()` is invoked automatically on package import, so the env var alone is enough — no code change required. Use the programmatic call only when you need to (re)apply env vars set after import (e.g. in a REPL or test):

```python
import pytfe
pytfe.setup_logging()
```

Levels: `debug` shows every request/response, `info` shows retry decisions only.

### Sample output

```
[2026-05-25 14:12:26 pytfe.transport DEBUG]
> GET /api/v2/organizations/acme/workspaces?page[number]=1&page[size]=100
< 200 OK
< {
<   "data": [
<     { "id": "ws-...", "type": "workspaces", ... }
<   ]
< }
```

### Safe by default

Bearer tokens and other credentials are redacted **before** they reach the logger:

- Sensitive headers (`Authorization`, `Cookie`, anything containing `token` / `secret` / `password` / `api-key`) are replaced with `**REDACTED**`. Headers are off by default; even when you turn them on with `PYTFE_LOG_HEADERS=true`, redaction still applies.
- JSON bodies have sensitive keys (`token`, `access_token`, `refresh_token`, `secret`, `password`, `private_key`, `client_secret`) replaced recursively.
- Large bodies are truncated to `PYTFE_LOG_TRUNCATE_BYTES` (default `1024`). Long arrays are clipped with `"... (N additional elements)"`.
- Binary responses (state-version downloads, configuration-version tarballs, etc.) render as `[raw stream]` — the bytes are never decoded into the log.

### Compose with your existing logging

Because pyTFE uses stdlib `logging`, all the standard knobs work:

```python
import logging

# Just the HTTP traffic, at DEBUG
logging.getLogger("pytfe.transport").setLevel(logging.DEBUG)

# Send pyTFE logs to your existing handler instead of stderr
logging.getLogger("pytfe").addHandler(my_json_handler)
```

For full details — environment variables, redaction guarantees, and how to add log statements to new SDK code — see [`docs/LOGGING.md`](./docs/LOGGING.md).

## Documentation

Start with [Getting started](./docs/getting-started.md), then use the
[API index](./docs/api/index.md) to find resource-specific guides, examples,
and upstream HCP Terraform API docs.

| Need | Start here |
|---|---|
| Configure the SDK | [Authentication](./docs/authentication.md), [Pagination](./docs/pagination.md), [Logging](./docs/LOGGING.md) |
| API guides | [API index](./docs/api/index.md), [Workspaces](./docs/api/workspaces.md), [Runs/plans/applies](./docs/api/runs-plans-applies.md), [State versions](./docs/api/state-versions.md) |
| Scenario guides | [API-driven run](./docs/scenarios/api-driven-run.md), [State management](./docs/scenarios/state-management.md), [Migrate workspaces and state](./docs/scenarios/migrate-workspaces-and-state.md), [Team access onboarding](./docs/scenarios/team-access-onboarding.md), [No-code provisioning](./docs/scenarios/no-code-provisioning.md) |
| Operations guides | [Troubleshooting](./docs/troubleshooting.md), [Errors](./docs/errors.md), [Terraform Enterprise](./docs/terraform-enterprise.md) |
| Contribute to the SDK | [CONTRIBUTING](./docs/CONTRIBUTING.md), [ITERATORS](./docs/ITERATORS.md), [MODELS](./docs/MODELS.md), [RESOURCE](./docs/RESOURCE.md) |

Upstream API reference: https://developer.hashicorp.com/terraform/cloud-docs/api-docs

## Examples

See the [`examples/`](./examples) directory for runnable snippets covering common workflows (workspaces, variables, configuration versions, runs/plans/applies, state, agents).

## Running tests

See [`TESTS.md`](./docs/TESTS.md). Typical flow:

```bash
pip install -e .[dev]
make test
```

## Issues and Contributing

See [`CONTRIBUTING.md`](./docs/CONTRIBUTING.md). We welcome issues and pull requests.

## Releases

See [`RELEASES.md`](./docs/RELEASES.md).

## License

This project is licensed under the **MPL-2.0**. See [`LICENSE`](./LICENSE).
