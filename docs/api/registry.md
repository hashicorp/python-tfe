# Public Terraform Registry (`client.registry`)

`client.registry` is a client for the **public Terraform Registry** module API
at [`registry.terraform.io`](https://registry.terraform.io). It implements the
[module registry protocol](https://developer.hashicorp.com/terraform/internals/module-registry-protocol)
plus HashiCorp's documented discovery extensions — searching modules across the
whole registry, retrieving module documentation/schemas, listing versions,
resolving download sources, and reading download metrics.

Upstream API reference:
[Registry API](https://developer.hashicorp.com/terraform/registry/api-docs).

> In HashiCorp's words: *"The public Terraform Registry and the private registry
> included in HCP Terraform and Terraform Enterprise implement a superset of
> [the minimal module registry] API to support additional use-cases such as
> searching for modules across the whole registry, retrieving documentation and
> schemas for modules, and so on."*

## Public registry vs. private registry — which resource do I want?

The SDK exposes **two different registry surfaces**. They are different APIs, on
different hosts, with different authentication. Pick based on what you are doing:

| | `client.registry` (this guide) | `client.registry_modules` / `client.registry_providers` / … |
|---|---|---|
| What it is | The **public Terraform Registry** module API | The **private registry** included in HCP Terraform / Terraform Enterprise |
| Host | `registry.terraform.io` (configurable) | Your HCP Terraform / TFE address (`/api/v2/…`) |
| Purpose | **Discover & read** public modules (list, search, versions, download source, metrics) | **Manage** your organization's private modules/providers (publish, update, delete, add versions) |
| Auth | **None** — unauthenticated; the SDK never sends your bearer token | **Bearer token** required (your HCP TF / TFE API token) |
| Wire format | Plain JSON, `offset`/`limit` pagination | JSON:API, `page[number]`/`page[size]` pagination |
| Upstream docs | [Registry API](https://developer.hashicorp.com/terraform/registry/api-docs) | [Private registry — modules](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/private-registry/modules) / [providers](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/private-registry/providers) |

In short: use `client.registry` to **browse the public registry**; use
`client.registry_modules` (and friends) to **publish to and manage your own
private registry**.

## Authentication

The public Registry API does not require authentication, so a token is optional:

```python
from pytfe import TFEClient, TFEConfig

# No token needed for the public registry.
client = TFEClient(TFEConfig(address="https://app.terraform.io", token=""))
```

The SDK sends requests to the registry host **without** the `Authorization`
header even when a token is configured, so your HCP TF / TFE credentials are
never exposed to the registry.

## Targeting another registry

By default `client.registry` points at `registry.terraform.io`. To talk to
another host that implements the module registry protocol, set `base_url`:

```python
from pytfe.resources.registry import Registry

registry = Registry(client._transport, base_url="https://modules.example.com")
```

## Methods

| Method | Returns | Endpoint |
|---|---|---|
| `list_modules(namespace=None, options=None)` | `Iterator[PublicRegistryModule]` | `GET /v1/modules[/:namespace]` |
| `search_modules(query, options=None)` | `Iterator[PublicRegistryModule]` | `GET /v1/modules/search?q=…` |
| `list_latest_for_all_providers(namespace, name, options=None)` | `Iterator[PublicRegistryModule]` | `GET /v1/modules/:namespace/:name` |
| `latest_for_provider(namespace, name, provider)` | `PublicRegistryModule` | `GET /v1/modules/:namespace/:name/:provider` |
| `get_module(namespace, name, provider, version)` | `PublicRegistryModule` | `GET /v1/modules/:namespace/:name/:provider/:version` |
| `list_versions(namespace, name, provider)` | `PublicRegistryModuleVersions` | `GET /v1/modules/:namespace/:name/:provider/versions` |
| `download_url(namespace, name, provider, version)` | `str` | `GET …/:version/download` |
| `latest_download_url(namespace, name, provider)` | `str` | `GET …/:provider/download` |
| `downloads_summary(namespace, name, provider)` | `PublicRegistryModuleDownloadsSummary` | `GET /v2/modules/…/downloads/summary` |

`list_*` and `search_*` return single-use `Iterator`s and page transparently
using the registry's `offset`/`limit` scheme (see [Pagination](../pagination.md)).
Use `itertools.islice(...)` or a `for ... break` loop to take just the first few
results without walking the entire registry.

The two `*download_url` methods return the module's source location — the value
of the registry's `X-Terraform-Get` response header (a
[go-getter](https://github.com/hashicorp/go-getter) URL string), **not** the
archive bytes.

## Quick start

```python
import itertools
from pytfe import TFEClient, TFEConfig
from pytfe.models import PublicRegistrySearchOptions

client = TFEClient(TFEConfig(address="https://app.terraform.io", token=""))

# Search (take just the first few — the iterator pages lazily).
for m in itertools.islice(
    client.registry.search_modules("vpc", PublicRegistrySearchOptions(provider="aws")),
    5,
):
    print(m.id, m.downloads, m.verified)

# Read a specific module and its inputs.
module = client.registry.latest_for_provider("terraform-aws-modules", "vpc", "aws")
print(module.version, len(module.root.inputs or []))

# List versions and resolve a download source.
versions = client.registry.list_versions("terraform-aws-modules", "vpc", "aws")
print([v.version for v in versions.versions][:3])
print(client.registry.latest_download_url("terraform-aws-modules", "vpc", "aws"))

# Download metrics.
summary = client.registry.downloads_summary("terraform-aws-modules", "vpc", "aws")
print(summary.total)
```

See the runnable [`examples/registry.py`](../../examples/registry.py).

## Models

Public-registry models are exported from `pytfe.models` under the
`PublicRegistry*` prefix (e.g. `PublicRegistryModule`,
`PublicRegistryModuleVersions`, `PublicRegistryModuleDownloadsSummary`,
`PublicRegistrySearchOptions`). The prefix avoids any confusion with the
private-registry models such as `RegistryModule`.
