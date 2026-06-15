# Scenario: TFE identity bootstrap (SAML + SCIM)

Bringing up identity federation on a fresh Terraform Enterprise
installation involves three orthogonal pieces of state:

1. **SAML** — how users authenticate. Configured on
   `client.admin.saml_settings`.
2. **SCIM** — how user/group provisioning is automated. Configured on
   `client.admin.scim_settings`.
3. **SCIM tokens** — the bearer tokens an IdP uses to make SCIM API
   calls into TFE. Managed via `client.admin.scim_tokens`.

This scenario walks the typical end-to-end bootstrap. All operations
require a TFE **site-admin** token. None of these endpoints are
available on HCP Terraform (SaaS) — they return `404` there.

Upstream concept docs:

- SAML SSO on TFE: https://developer.hashicorp.com/terraform/enterprise/saml
- SCIM on TFE: https://developer.hashicorp.com/terraform/enterprise/admin/scim

API references in this repo:

- [`api/admin-identity.md`](../api/admin-identity.md)

## Prerequisites

```bash
export TFE_TOKEN="<site-admin token>"
export TFE_ADDRESS="https://tfe.example.com"
```

You also need:

- The IdP's SSO/SLO endpoint URLs and signing certificate (for SAML).
- The IdP's SCIM ID of the group you want to grant TFE site-admin to
  (for SCIM, optional).
- A clear rotation plan — both SAML certs and SCIM tokens are
  long-lived credentials that need eventual replacement.

## Step 1: Configure SAML

```python
from pytfe import TFEClient
from pytfe.models import (
    AdminSAMLSettingsUpdateOptions,
    SAMLProviderType,
    SAMLSignatureMethod,
)

client = TFEClient()

# Plug in the IdP cert + endpoints. Enabling can be a separate step if
# you want to validate metadata first.
client.admin.saml_settings.update(
    AdminSAMLSettingsUpdateOptions(
        idp_cert="-----BEGIN CERTIFICATE-----\n...",
        sso_endpoint_url="https://idp.example.com/sso",
        slo_endpoint_url="https://idp.example.com/slo",
        provider_type=SAMLProviderType.OKTA,
        attr_username="Username",
        attr_site_admin="SiteAdmin",
        attr_groups="MemberOf",
        site_admin_role="site-admins",
        team_management_enabled=True,
        authn_requests_signed=True,
        signature_signing_method=SAMLSignatureMethod.SHA256,
        signature_digest_method=SAMLSignatureMethod.SHA256,
    )
)

# Once you've smoke-tested the IdP round-trip, enable it.
client.admin.saml_settings.update(
    AdminSAMLSettingsUpdateOptions(enabled=True)
)
```

`provider_type` is a hint TFE uses to apply provider-specific quirks.
`SAMLProviderType.UNKNOWN` is the safe default; pick `OKTA`, `ENTRA`,
or `SAML` when you know the IdP.

The ACS consumer and metadata URLs are computed by TFE; read them from
`client.admin.saml_settings.read()` and hand them to the IdP team.

```python
saml = client.admin.saml_settings.read()
print("ACS consumer URL:", saml.acs_consumer_url)
print("SP metadata URL:", saml.metadata_url)
```

### Rotating the IdP certificate

Two-step dance to avoid breaking in-flight SSO sessions:

```python
# 1. Push the new cert. The old cert stays valid while users drain.
client.admin.saml_settings.update(
    AdminSAMLSettingsUpdateOptions(
        idp_cert="-----BEGIN CERTIFICATE-----\nNEW...",
    )
)

# 2. After the rotation window — explicitly revoke the old cert.
client.admin.saml_settings.revoke_idp_cert()
```

## Step 2: Enable SCIM and bind a site-admin group

```python
from pytfe.models import AdminSCIMSettingsUpdateOptions

client.admin.scim_settings.update(
    AdminSCIMSettingsUpdateOptions(
        enabled=True,
        paused=False,
        site_admin_group_scim_id="<group-scim-id-from-idp>",
    )
)
```

The `site_admin_group_scim_id` field has unusual wire semantics. Three
caller intents map to three wire payloads:

- Don't pass the kwarg at all → the field is omitted from the request
  → server keeps the current value untouched.
- `site_admin_group_scim_id="g-1"` → sent as a string → mapping is set
  to that group.
- `site_admin_group_scim_id=None` (explicit) → sent as JSON `null` →
  mapping is removed and SCIM-granted site-admin access is revoked.

The SDK's `AdminSCIMSettingsUpdateOptions.to_payload()` handles this
distinction by inspecting Pydantic's `model_fields_set` instead of
relying on `exclude_none`. You don't need to do anything special — just
pass the value you mean.

```python
# Pause provisioning without disabling
client.admin.scim_settings.update(AdminSCIMSettingsUpdateOptions(paused=True))

# Unlink the SCIM site-admin group (explicit null)
client.admin.scim_settings.update(
    AdminSCIMSettingsUpdateOptions(site_admin_group_scim_id=None)
)

# Fully disable SCIM (PATCH cannot do this — use delete)
client.admin.scim_settings.delete()
```

`delete()` disables provisioning. It does **not** revoke site-admin
access that SCIM previously granted to existing users — that has to be
revoked separately if needed.

## Step 3: Mint a SCIM token for the IdP

```python
from pytfe.models import AdminSCIMTokenCreateOptions

token = client.admin.scim_tokens.create(
    AdminSCIMTokenCreateOptions(description="okta-scim-bot-2026-Q2")
)
print("Token ID:", token.id)
print("Token value:", token.token)  # capture now — never returned again
```

Operational rules:

- The plaintext value of the token is **only** returned on this single
  `create()` response. Every subsequent `list()` or `read()` returns
  `None` for that field. Store the value in your secret manager
  immediately.
- The SDK requires a non-empty `description`. Use something the SCIM
  audit logs will be readable with — IdP name + rotation date is a
  good pattern.
- Delete the previous token after the IdP is reconfigured to the new
  one. Multiple SCIM tokens can coexist; that's how zero-downtime
  rotation works.

```python
# List existing tokens to find one to revoke
for tok in client.admin.scim_tokens.list():
    print(tok.id, tok.description, tok.created_at, tok.last_used_at)

# Revoke
client.admin.scim_tokens.delete("at-...")
```

## Token rotation summary

| Credential | Rotation method |
|---|---|
| SAML IdP cert | `update(idp_cert=...)` then `revoke_idp_cert()` after rotation window |
| SAML SP private key | `update(private_key=...)` — overwrites in place |
| SCIM token | `create()` new, switch IdP over, `delete()` old |

## Operational notes

- **TFE-only.** All endpoints in `client.admin.*` return `404` on HCP
  Terraform. Don't write code that assumes both paths exist.
- **Site-admin scope.** All mutations require site-admin permission. A
  workspace owner token will receive 403.
- **Read carefully before update.** SAML settings are a singleton —
  `update()` is partial (only fields you set are sent), but a mistaken
  `enabled=False` will lock everyone out of the SSO flow.
- **Treat SCIM tokens like SCIM passwords.** They grant the ability to
  create and remove users; rotate them on the same cadence as any
  long-lived API credential.
