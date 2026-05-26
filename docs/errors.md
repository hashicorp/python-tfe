# Errors

pyTFE raises Python exceptions for local validation failures, transport errors,
and API errors returned by HCP Terraform or Terraform Enterprise.

## Base exception

All SDK-owned API/transport errors inherit from `pytfe.errors.TFEError`:

```python
from pytfe.errors import TFEError

try:
    workspace = client.workspaces.read_by_id("ws-abc123")
except TFEError as exc:
    print(exc)
    print(exc.status)
    print(exc.errors)
```

`TFEError` exposes:

- `status`: HTTP status code when available.
- `errors`: parsed JSON:API error objects when available.

## Common typed errors

| Error | Typical cause |
|---|---|
| `AuthError` | Unauthorized or forbidden request. |
| `NotFound` | Resource not found or not visible to the token. |
| `RateLimited` | Server asked the client to slow down. Includes `retry_after` when available. |
| `ValidationError` | API validation failure. |
| `ServerError` | Server-side or transport failure. |
| `UnsupportedInCloud` | Endpoint only supported in Terraform Enterprise. |
| `UnsupportedInEnterprise` | Endpoint only supported in HCP Terraform. |

Resource-specific errors, such as `InvalidWorkspaceIDError` or
`InvalidRunIDError`, also live in `pytfe.errors`.

## Local validation errors

Some existing public methods raise `ValueError` for invalid local input. This is
kept for backward compatibility. Newer APIs generally prefer typed `TFEError`
subclasses, but callers should be prepared for both in older resource surfaces.

```python
from pytfe.errors import TFEError

try:
    runs = list(client.runs.list(""))
except TFEError as exc:
    handle_sdk_error(exc)
except ValueError as exc:
    handle_local_validation_error(exc)
```

## Downstream tools and Ansible modules

Downstream tools should catch narrow errors when they can produce a useful
message, then catch `TFEError` for general API failures:

```python
from pytfe.errors import AuthError, NotFound, TFEError

try:
    workspace = client.workspaces.read_by_id(workspace_id)
except AuthError as exc:
    module.fail_json(msg=f"authentication failed: {exc}")
except NotFound as exc:
    module.fail_json(msg=f"workspace not found or not visible: {exc}")
except TFEError as exc:
    module.fail_json(
        msg=str(exc),
        status=exc.status,
        errors=exc.errors,
    )
except ValueError as exc:
    module.fail_json(msg=f"invalid module input: {exc}")
```

Avoid string-matching error messages when a typed exception, HTTP status, or
JSON:API error pointer is available.

## Inspecting API error details

When the server returns JSON:API errors, `exc.errors` may contain structured
entries:

```python
try:
    make_request()
except TFEError as exc:
    for error in exc.errors:
        print(error)
```

Use these details for logs and diagnostics, but keep user-facing messages short
and avoid printing secrets.
