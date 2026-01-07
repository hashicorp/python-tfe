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

orgs = client.organizations.list()
for org in orgs.items:
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
orgs = client.organizations.list()
for org in orgs.items:
    print(org.name)
```

#### When host or token is empty
```python
from pytfe import TFEClient, TFEConfig

config = TFEConfig(address="", token="")
client = TFEClient(config)

orgs = client.organizations.list()
for org in orgs.items:
    print(org.name)
```

## Documentation

- API reference and guides (SDK): **coming soon**  
- Terraform Enterprise API: https://developer.hashicorp.com/terraform/enterprise/api-docs

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
