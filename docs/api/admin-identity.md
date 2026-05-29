# Admin identity (SAML / SCIM) and GitHub App installations

pyTFE exposes the Terraform Enterprise admin identity APIs (SAML
settings, SCIM settings, SCIM tokens) under a nested namespace,
`client.admin.*`, and the read-only GitHub App installation discovery
API as a top-level `client.github_app_installations` resource.

| Service | TFE-only | Purpose |
|---|---|---|
| `client.admin.saml_settings` | yes | Read / update the org's SAML config; revoke previous IdP cert |
| `client.admin.scim_settings` | yes | Enable / pause SCIM, manage site-admin group mapping |
| `client.admin.scim_tokens` | yes | List / create / read / delete SCIM provisioning tokens |
| `client.github_app_installations` | no | Look up GitHub App installations visible to the caller |

Upstream docs:

- SAML settings: https://developer.hashicorp.com/terraform/enterprise/api-docs/admin/settings
- SCIM settings: https://developer.hashicorp.com/terraform/enterprise/api-docs/admin/scim-settings
- SCIM tokens: https://developer.hashicorp.com/terraform/enterprise/api-docs/admin/scim-tokens
- GitHub App installations: https://developer.hashicorp.com/terraform/enterprise/api-docs/github-app-installations

Examples:

- [`admin_identity.py`](../../examples/admin_identity.py)
- [`github_app_installations.py`](../../examples/github_app_installations.py)

## Why the nested namespace

The TFE admin APIs require **site-admin** permission, are not available
on HCP Terraform (SaaS), and live under a distinct `/api/v2/admin/...`
URL prefix. Grouping them under `client.admin.*` makes that boundary
visible at the call site — when you see `client.admin.foo()` you know
this is admin work, not a regular organisation operation. Calls against
HCP Terraform return `404`, surfaced as `pytfe.errors.NotFound`.

## SAML settings

Singleton resource: the organisation has exactly one SAML config.

| Method | Purpose |
|---|---|
| `client.admin.saml_settings.read()` | Read current SAML config. |
| `client.admin.saml_settings.update(options)` | Partial update — only fields you set are sent. |
| `client.admin.saml_settings.revoke_idp_cert()` | Promote the new IdP cert and clear the old one. |

```python
from pytfe import TFEClient
from pytfe.models import (
    AdminSAMLSettingsUpdateOptions,
    SAMLProviderType,
    SAMLSignatureMethod,
)

client = TFEClient()

# Read
saml = client.admin.saml_settings.read()
print(saml.enabled, saml.provider_type, saml.sso_endpoint_url)

# Update (partial — only the listed fields are sent)
saml = client.admin.saml_settings.update(
    AdminSAMLSettingsUpdateOptions(
        enabled=True,
        idp_cert="-----BEGIN CERTIFICATE-----\n...",
        sso_endpoint_url="https://idp.example.com/sso",
        slo_endpoint_url="https://idp.example.com/slo",
        provider_type=SAMLProviderType.OKTA,
        authn_requests_signed=True,
        signature_signing_method=SAMLSignatureMethod.SHA256,
    )
)
```

### Rotating the IdP certificate

```python
# 1. Push the new cert via update. The old cert stays in place during
#    the rotation window so in-flight sessions keep working.
client.admin.saml_settings.update(
    AdminSAMLSettingsUpdateOptions(
        idp_cert="-----BEGIN CERTIFICATE-----\nNEW...",
    )
)

# 2. Drain in-flight SSO sessions / verify the new cert works.

# 3. Revoke the old cert.
client.admin.saml_settings.revoke_idp_cert()
```

### Sensitive fields

`private_key` (wire name: `private-key`) is sensitive. The transport-
level debug logger redacts that key in both `snake_case` and
hyphenated forms before anything reaches the log. Certificate material
(`idp-cert`, `certificate`, `old-idp-cert`) is **not** redacted —
those are public X.509 blobs by design.

## SCIM settings

Singleton resource. Three operations: read, update (PATCH), delete.

| Method | Purpose |
|---|---|
| `client.admin.scim_settings.read()` | Read current SCIM config. |
| `client.admin.scim_settings.update(options)` | Partial update; see omit-vs-null note below. |
| `client.admin.scim_settings.delete()` | Disable SCIM. PATCH cannot set `enabled=False`; use this instead. |

```python
from pytfe.models import AdminSCIMSettingsUpdateOptions

scim = client.admin.scim_settings.read()
print(scim.enabled, scim.paused, scim.site_admin_group_display_name)

# Pause SCIM provisioning without disabling it
client.admin.scim_settings.update(AdminSCIMSettingsUpdateOptions(paused=True))

# Disable SCIM entirely (note: does NOT revoke site-admin access
# already granted by SCIM to existing users)
client.admin.scim_settings.delete()
```

### The omit-vs-explicit-null rule for `site_admin_group_scim_id`

This field has three meaningful states the SDK preserves end-to-end:

| Caller intent | How to express it | What goes on the wire |
|---|---|---|
| Don't touch the server value | Omit the kwarg entirely | Field is not in the request body |
| Set the mapping to a specific group | `site_admin_group_scim_id="g-1"` | `{"site-admin-group-scim-id": "g-1"}` |
| Unlink the SCIM site-admin group | `site_admin_group_scim_id=None` | `{"site-admin-group-scim-id": null}` |

Pydantic's normal `exclude_none=True` flattens "omit" and "explicit
None" together. To preserve the distinction this update options model
overrides serialization via `to_payload()`, which inspects
`model_fields_set` to tell the two cases apart. You call the resource
method the same way; the distinction is handled internally.

```python
# Omit — server keeps existing mapping
client.admin.scim_settings.update(
    AdminSCIMSettingsUpdateOptions(paused=False)
)

# Explicit None — unlink the SCIM group from site-admin
client.admin.scim_settings.update(
    AdminSCIMSettingsUpdateOptions(site_admin_group_scim_id=None)
)
```

## SCIM tokens

| Method | Purpose |
|---|---|
| `client.admin.scim_tokens.list()` | Iterate existing SCIM tokens (without their plaintext values). |
| `client.admin.scim_tokens.create(options)` | Mint a new SCIM token. The plaintext value is on the response — capture it now. |
| `client.admin.scim_tokens.read(scim_token_id)` | Read a single token's metadata. |
| `client.admin.scim_tokens.delete(scim_token_id)` | Revoke a SCIM token. |

```python
from pytfe.models import AdminSCIMTokenCreateOptions

# Mint a token — capture .token from the response, you won't see it again
new = client.admin.scim_tokens.create(
    AdminSCIMTokenCreateOptions(description="okta-scim-bot")
)
print(new.id, new.token)  # token is None on every subsequent read

for tok in client.admin.scim_tokens.list():
    print(tok.id, tok.description, tok.last_used_at)

client.admin.scim_tokens.delete("at-...")
```

Two operational notes worth knowing:

- The `description` field is technically optional in the upstream API,
  but the SDK rejects an empty description at the resource layer
  (raises `RequiredSCIMTokenDescriptionError`). Audit logs are
  unreadable without one.
- The DELETE path is `/api/v2/admin/scim-tokens/{id}` (the admin
  namespace), not the generic `/api/v2/authentication-tokens/{id}`
  path used by other token types.

## GitHub App installations

Read-only lookup. Use these endpoints to discover the
`github-app-installation-id` value that workspace, stack, and
registry-module VCS configuration takes.

| Method | Purpose |
|---|---|
| `client.github_app_installations.list(options=None)` | Iterate installations visible to the caller. |
| `client.github_app_installations.read(github_app_installation_id)` | Read one by HCP-side ID. |

```python
from pytfe.models import GitHubAppInstallationListOptions

# Find all installations
for app in client.github_app_installations.list():
    print(app.id, app.name, app.installation_id, app.installation_type)

# Filter by GitHub org / login name
for app in client.github_app_installations.list(
    GitHubAppInstallationListOptions(name="my-org")
):
    print(app.id, app.installation_url)

# Filter by GitHub-side numeric installation ID (NOT the HCP `id`)
for app in client.github_app_installations.list(
    GitHubAppInstallationListOptions(installation_id=54810170)
):
    print(app.id)

# Read a specific installation by its HCP-side ID
app = client.github_app_installations.read("ghain-abc123")
```

Two things worth pinning explicitly:

- The read URL uses the singular path segment: `/api/v2/github-app/installation/{id}`,
  not the plural `installations`. The list URL uses the plural. This
  is the upstream contract — the SDK mirrors it.
- `installation_id` (the GitHub-side numeric ID) is distinct from `id`
  (HCP Terraform's internal string ID, e.g. `ghain-...`). VCS-config
  fields like `github-app-installation-id` use the HCP-side `id`, not
  the numeric GitHub-side installation ID.

## Token requirements

- SAML / SCIM / SCIM tokens: TFE site-admin user token.
- GitHub App installations: any user token; the response is scoped to
  what that user can see.
