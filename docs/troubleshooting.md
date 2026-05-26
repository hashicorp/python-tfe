# Troubleshooting

This page covers common pyTFE issues and the first checks to run.

## Turn on transport logs

```bash
PYTFE_LOG=debug python your_script.py
```

`PYTFE_LOG=debug` prints request/response traces through the `pytfe.transport`
logger. Tokens and common secret keys are redacted before logging.

For retry-only visibility:

```bash
PYTFE_LOG=info python your_script.py
```

See [LOGGING.md](LOGGING.md) for the full logging reference.

## Authentication failures

Symptoms:

- `AuthError`
- HTTP `401`
- HTTP `403`

Checks:

- Confirm `TFE_TOKEN` is set in the process running the code.
- Confirm `TFE_ADDRESS` points to the right HCP Terraform or Terraform
  Enterprise instance.
- Confirm the token type is accepted by the endpoint. Some endpoints require a
  user, team, or group token rather than an organization token.
- Confirm the token has permission on the target organization, project, or
  workspace.

## `404` can mean missing resource or missing permission

HCP Terraform may return `404` when the resource does not exist or when the
token cannot see it. Check:

- Does the ID belong to the same organization or instance?
- Is the resource deleted or archived?
- Does the token have permission to read the parent workspace/project/org?
- Are you using a workspace name where the SDK method expects a workspace ID?

## Pagination surprises

All `list` and `list_*` methods return iterators:

```python
items = client.workspaces.list("my-org")
print(items)        # iterator object
print(list(items))  # actual results
```

Iterators are single-use. If you need to traverse results twice, materialize
them once:

```python
workspaces = list(client.workspaces.list("my-org"))
```

See [pagination.md](pagination.md).

## Terraform Enterprise with self-signed or private CAs

If TLS verification fails for Terraform Enterprise, prefer a CA bundle:

```bash
export SSL_CERT_FILE="/path/to/internal-ca-bundle.pem"
```

Or:

```python
from pytfe import TFEConfig

config = TFEConfig(ca_bundle="/path/to/internal-ca-bundle.pem")
```

Avoid `TFE_VERIFY_TLS=false` outside local testing.

## Retries and transient failures

pyTFE retries transient failures in the transport layer. Configure the maximum
retry count with:

```bash
export TFE_MAX_RETRIES=5
```

For noisy CI environments, enabling retry logs can help:

```bash
PYTFE_LOG=info python your_script.py
```

## Signed upload and download URLs

Some endpoints return hosted upload/download URLs for configuration versions,
state versions, plan JSON, or errored state. Prefer the high-level pyTFE helper
methods such as:

- `client.configuration_versions.upload(...)`
- `client.state_versions.upload(...)`
- `client.state_versions.download(...)`
- `client.plans.read_json_output_for_run(...)`
- `client.applies.errored_state(...)`

These methods handle the non-standard response shapes for you.

## Getting help from the upstream API docs

When an endpoint behaves unexpectedly, compare your code with:

- HCP Terraform API docs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs
- Terraform Enterprise API docs: https://developer.hashicorp.com/terraform/enterprise/api-docs
- go-tfe implementation: https://github.com/hashicorp/go-tfe

