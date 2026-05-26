# Authentication

pyTFE authenticates to HCP Terraform and Terraform Enterprise with an API token.
The SDK sends the token as a bearer token on API requests.

HashiCorp's API overview documents bearer-token authentication, and HashiCorp's
API token guide explains user, team, group, and organization token behavior:

- HCP Terraform API overview: https://developer.hashicorp.com/terraform/cloud-docs/api-docs
- API token guide: https://developer.hashicorp.com/terraform/cloud-docs/users-teams-organizations/api-tokens

## Default environment-based configuration

`TFEClient()` with no arguments calls `TFEConfig.from_env()`, which reads the
same defaults as `TFEConfig()`.

```python
from pytfe import TFEClient

client = TFEClient()
```

Supported SDK configuration environment variables:

| Environment variable | `TFEConfig` field | Default | Notes |
|---|---|---|---|
| `TFE_TOKEN` | `token` | `""` | API token used for bearer authentication. Most real calls require this to be set. |
| `TFE_ADDRESS` | `address` | `https://app.terraform.io` | Base URL for HCP Terraform or Terraform Enterprise. Do not include `/api/v2`. |
| `TFE_TIMEOUT` | `timeout` | `30` | Request timeout in seconds. Parsed as a float. |
| `TFE_VERIFY_TLS` | `verify_tls` | `true` | Set to `0`, `false`, or `no` to disable TLS verification. Use this only for controlled local testing. |
| `TFE_MAX_RETRIES` | `max_retries` | `5` | Maximum retry attempts for transient transport/server failures. Parsed as an integer. |
| `SSL_CERT_FILE` | `ca_bundle` | unset | Path to a custom CA bundle, useful for Terraform Enterprise installations using an internal CA. |

Example:

```bash
export TFE_TOKEN="your-api-token"
export TFE_ADDRESS="https://app.terraform.io"
export TFE_TIMEOUT="60"
export TFE_MAX_RETRIES="5"
```

Then:

```python
from pytfe import TFEClient

client = TFEClient()
```

## Explicit configuration

Explicit `TFEConfig(...)` values override environment fallback for the fields
you set:

```python
from pytfe import TFEClient, TFEConfig

config = TFEConfig(
    address="https://tfe.example.com",
    token="your-api-token",
    timeout=60.0,
    verify_tls=True,
    max_retries=3,
    ca_bundle="/etc/ssl/certs/internal-ca.pem",
    user_agent_suffix="my-automation/1.0",
)

client = TFEClient(config)
```

Use explicit configuration when a process needs multiple clients, when tests
need isolated config, or when credentials come from a secret manager instead of
process environment variables.

## Token type guidance

Choose the narrowest token type that can perform the workflow:

| Token type | Typical use |
|---|---|
| User token | Interactive or user-owned automation. Most flexible because permissions follow the user. |
| Team token | Workspace automation owned by a team. Good for routine run, state, and workspace workflows where team permissions are already scoped. |
| Group token | HCP Europe equivalent for group-based access. |
| Organization token | Organization setup and administration, such as creating workspaces and teams. Avoid using it as a general-purpose automation token. |

Some endpoints cannot be used with organization tokens. HashiCorp marks those
endpoints in the upstream API docs. For example, API-driven runs, configuration
version uploads, and state-version writes often need a user, team, or group
token with workspace permissions.

Never commit tokens to source control. Prefer environment variables, CI secret
stores, or a secret manager.

## HCP Terraform vs Terraform Enterprise addresses

| Platform | Address value |
|---|---|
| HCP Terraform | `https://app.terraform.io` |
| HCP Terraform Europe | Use the organization URL, commonly `https://app.eu.terraform.io` |
| Terraform Enterprise | Your installation base URL, for example `https://tfe.example.com` |

The SDK appends `/api/v2/...` paths internally.

## TLS and custom CAs

For Terraform Enterprise with an internal CA:

```bash
export SSL_CERT_FILE="/path/to/internal-ca-bundle.pem"
```

Or explicitly:

```python
from pytfe import TFEConfig

config = TFEConfig(ca_bundle="/path/to/internal-ca-bundle.pem")
```

Disabling verification is supported for local testing:

```bash
export TFE_VERIFY_TLS=false
```

Do not disable TLS verification for production automation.

## `TFE_ORG` and `TFE_ORGANIZATION`

`TFE_ORG` and `TFE_ORGANIZATION` are not SDK configuration fields. Some example
scripts read them as convenient defaults for an organization name:

```bash
export TFE_ORG="my-organization"
python examples/workspace.py
```

Application code should pass organization names to resource methods directly:

```python
for workspace in client.workspaces.list("my-organization"):
    print(workspace.name)
```

