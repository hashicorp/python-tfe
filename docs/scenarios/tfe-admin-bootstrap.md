# Scenario: TFE admin bootstrap (SMTP + org defaults + token TTL)

This scenario covers the operational setup the first time a Terraform
Enterprise installation is brought into service — or the equivalent
HCP Terraform org-owner setup for the per-org pieces. Three orthogonal
pieces of state get touched:

| Piece | Resource | TFE-only? |
|---|---|---|
| SMTP relay for verification emails / notifications | `client.admin.smtp_settings` | **yes** |
| Default execution mode + default agent pool for new workspaces | `client.organizations.{read,update,reset}_default_settings` | no |
| API-token max TTL per token type | `client.organization_token_ttl_policies` | no |

The SMTP half requires a TFE **site-admin** token. The other two work
on either HCP Terraform or TFE with an org-owner token.

Upstream references:

- SAML/SCIM/SMTP admin docs: see [`tfe-identity-bootstrap.md`](tfe-identity-bootstrap.md) for the other admin pieces
- Org-defaults + token-TTL API reference: [`api/organization-defaults-and-token-ttl.md`](../api/organization-defaults-and-token-ttl.md)

## Prerequisites

```bash
# For SMTP (TFE-only):
export TFE_TOKEN="<site-admin token>"
export TFE_ADDRESS="https://tfe.example.com"

# For org defaults + token TTL (HCP or TFE):
export TFE_TOKEN="<org-owner token>"
export TFE_ORG="my-org"
```

## Step 1: configure SMTP (TFE only)

Email-based notifications, SCIM verification, and admin reset flows all
depend on a working SMTP relay. Set it up once at install time:

```python
from pytfe import TFEClient
from pytfe.models import AdminSMTPSettingsUpdateOptions, SMTPAuthType

client = TFEClient()

client.admin.smtp_settings.update(
    AdminSMTPSettingsUpdateOptions(
        enabled=True,
        host="smtp.example.com",
        port=587,
        sender="noreply@example.com",
        auth=SMTPAuthType.LOGIN,
        username="smtp-bot",
        password="<from secret manager>",
        test_email_address="ops@example.com",
    )
)
```

Setting `test_email_address` triggers TFE to send a verification email
to that address as a side effect of the PATCH. The field is write-only
— subsequent reads won't surface it.

The `password` field is sensitive. The transport-level debug logger
(`PYTFE_LOG=debug`) redacts it before output. Read [`docs/LOGGING.md`](../LOGGING.md)
for the full redaction list.

## Step 2: choose a default execution mode for new workspaces

If most workspaces in the org should use the same execution mode
(`remote`, `local`, or `agent`), set it as the org default so new
workspaces inherit it without explicit per-workspace configuration:

```python
from pytfe.models import OrganizationDefaultSettingsUpdateOptions

# Switch to agent execution as the default, pin a default pool
client.organizations.update_default_settings(
    "my-org",
    OrganizationDefaultSettingsUpdateOptions(
        default_execution_mode="agent",
        default_agent_pool_id="apool-abc123",
    ),
)
```

Two important rules the SDK enforces locally (before any HTTP call):

- `default_agent_pool_id` is only valid when `default_execution_mode="agent"`.
  Setting a pool while asking for `remote` or `local` raises
  `pydantic.ValidationError` at construction time.
- Omitting a field leaves the server value alone. Passing
  `default_agent_pool_id=None` explicitly sends wire `null`, which
  clears the pool. The two are distinguished by inspecting Pydantic's
  `model_fields_set`.

Read current defaults at any time:

```python
defaults = client.organizations.read_default_settings("my-org")
print(defaults.default_execution_mode, defaults.default_agent_pool_id)
```

Reset to the safe baseline:

```python
client.organizations.reset_default_settings("my-org")
# -> default_execution_mode="remote", default_agent_pool_id cleared
```

## Step 3: cap API-token lifetimes

When you flip `max_ttl_enabled=True` on the organisation, TFE/HCP
enforces a per-token-type maximum lifetime. The default is 2 years for
all four token types; lower it to match your rotation policy.

```python
from pytfe.models import (
    OrganizationUpdateOptions,
    OrgTokenTTLPolicyUpdateOptions,
)

# 1. Enable enforcement on the org
client.organizations.update(
    "my-org", OrganizationUpdateOptions(max_ttl_enabled=True)
)

# 2. Set per-token-type TTLs
client.organization_token_ttl_policies.update(
    "my-org",
    OrgTokenTTLPolicyUpdateOptions(
        organization="1y",      # org tokens: 1 year
        team="90d",             # team tokens: 90 days
        user="30d",             # user tokens: 30 days
        audit_trails="2y",      # audit-trails: 2 years
    ),
)
```

The duration strings (`"1y"`, `"90d"`, `"30d"`, etc.) are parsed by the
SDK's `parse_ttl_to_ms()` helper. You can also pass integers (raw
milliseconds) if you prefer exact control.

**Critical: the audit-trails token type uses an UNDERSCORE in the TTL
policy API.** The field is named `audit_trails`, not `audit-trails`.
This differs from the audit-trails token *creation* surface (which uses
the hyphen). The `TokenPolicyType.AUDIT_TRAILS` enum encodes the right
spelling so callers don't need to remember the distinction.

Read current policies:

```python
for policy in client.organization_token_ttl_policies.list("my-org"):
    print(policy.token_type, policy.max_ttl_ms)
```

Reset all four token types back to the documented 2-year default:

```python
client.organization_token_ttl_policies.reset_to_defaults("my-org")
```

## Operational notes

- **Reducing TTL doesn't invalidate existing tokens.** Tokens issued
  before a policy change keep their original `expired-at`. Plan a
  rotation window when tightening limits.
- **Org-owner permission is sufficient** for steps 2 and 3. Only the
  SMTP step (step 1) requires site-admin.
- **HCP vs TFE.** Steps 2 and 3 work the same on both platforms. Step 1
  is TFE-only — on HCP the request returns 404, surfaced as
  `pytfe.errors.NotFound`.
- **Pair the empty-update guard with a confident dry run.** Building
  `OrgTokenTTLPolicyUpdateOptions()` with no fields and calling
  `update()` raises `RequiredFieldMissing` *before* any HTTP request.
  Use that as a safety net in automation that constructs partial
  updates conditionally.
