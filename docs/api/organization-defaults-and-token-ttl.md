# Organisation defaults and API-token TTL policy

Two closely-related per-organisation knobs that both live alongside
the existing `client.organizations` resource:

- **Default execution mode + default agent pool** — what new workspaces
  inherit. Exposed via three focused methods on `client.organizations`:
  `read_default_settings`, `update_default_settings`,
  `reset_default_settings`.
- **API-token max TTL** — how long org/team/user/audit tokens minted in
  the organisation are allowed to live. Exposed on a dedicated resource:
  `client.organization_token_ttl_policies`.

Both are available on HCP Terraform and on Terraform Enterprise. Neither
requires site-admin permissions; org-owner permissions are sufficient.

Upstream docs:

- Organisations API: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/organizations
- Organisation settings (max TTL): https://developer.hashicorp.com/terraform/cloud-docs/users-teams-organizations/organizations/settings#api-tokens

Examples:

- [`admin_smtp.py`](../../examples/admin_smtp.py) (SMTP — TFE-only; not relevant here but in the same bootstrap scenario)
- [`org_token_ttl.py`](../../examples/org_token_ttl.py)

## Default execution mode + default agent pool

| Method | Purpose |
|---|---|
| `client.organizations.read_default_settings(org)` | Read default execution mode + default agent pool. |
| `client.organizations.update_default_settings(org, options)` | Partial update — see omit-vs-explicit-null rule below. |
| `client.organizations.reset_default_settings(org)` | Convenience: reset to `remote` execution and clear the default agent pool. |

```python
from pytfe import TFEClient
from pytfe.models import OrganizationDefaultSettingsUpdateOptions

client = TFEClient()

# Read
defaults = client.organizations.read_default_settings("my-org")
print(defaults.default_execution_mode, defaults.default_agent_pool_id)

# Switch to agent execution and pin the default pool
client.organizations.update_default_settings(
    "my-org",
    OrganizationDefaultSettingsUpdateOptions(
        default_execution_mode="agent",
        default_agent_pool_id="apool-abc123",
    ),
)

# Reset to remote, clearing the agent pool
client.organizations.reset_default_settings("my-org")
```

### Cross-field validation

`OrganizationDefaultSettingsUpdateOptions` rejects at construction time
the combination "specify a pool id while explicitly asking for a
non-agent execution mode":

```python
# Raises pydantic.ValidationError immediately — no API call.
OrganizationDefaultSettingsUpdateOptions(
    default_execution_mode="remote",
    default_agent_pool_id="apool-abc123",
)
```

This mirrors the upstream rule and surfaces the mistake locally rather
than as an opaque server-side 422.

### Omit vs explicit `None` for `default_agent_pool_id`

Like SCIM settings, the agent pool field distinguishes three caller
intents end-to-end:

| Caller intent | How to express it | What goes on the wire |
|---|---|---|
| Don't touch the server value | Omit the kwarg entirely | Field is not in the request body |
| Set the pool to a specific id | `default_agent_pool_id="apool-1"` | `{"default-agent-pool-id": "apool-1"}` |
| Clear the pool | `default_agent_pool_id=None` | `{"default-agent-pool-id": null}` |

The `to_payload()` method on the options inspects
`model_fields_set` to preserve this distinction — Pydantic's
`exclude_none=True` would otherwise flatten "omit" and "explicit None"
together.

### What about the broader `client.organizations.update`?

The existing `OrganizationUpdateOptions` has also been fixed (this same
release) so its `default_execution_mode`, `default_agent_pool_id`, and
`max_ttl_enabled` fields now serialise with the correct hyphenated JSON
wire names. Previously they were emitted as snake_case and silently
ignored by the server. If you were calling `client.organizations.update`
with those fields and seeing no effect, this fixes it.

## API-token TTL policy

The org enforces a per-token-type maximum lifetime when
`max_ttl_enabled=True` on the parent organisation. The per-token-type
values live on a separate resource:

| Method | Purpose |
|---|---|
| `client.organization_token_ttl_policies.list(org)` | Iterate current policies. |
| `client.organization_token_ttl_policies.update(org, options)` | PATCH a partial set; at least one field required. |
| `client.organization_token_ttl_policies.reset_to_defaults(org)` | Reset all four token types to the documented 2-year default. |

```python
from pytfe.models import OrgTokenTTLPolicyUpdateOptions, DEFAULT_MAX_TTL_MS

# List
for policy in client.organization_token_ttl_policies.list("my-org"):
    print(policy.token_type, policy.max_ttl_ms)

# Update some token types — accepts integers (raw ms) OR duration strings
client.organization_token_ttl_policies.update(
    "my-org",
    OrgTokenTTLPolicyUpdateOptions(
        organization="2y",          # duration string
        team="30d",                 # duration string
        user=DEFAULT_MAX_TTL_MS,    # raw ms
        # audit_trails omitted -> server keeps existing value
    ),
)

# Reset everything to the 2-year default
client.organization_token_ttl_policies.reset_to_defaults("my-org")
```

### Duration parser

`parse_ttl_to_ms()` accepts the same suffixes the Terraform provider
does:

| Suffix | Meaning |
|---|---|
| `ms` | milliseconds |
| `s` | seconds |
| `m` | minutes |
| `h` | hours |
| `d` | days |
| `w` | weeks (7 days) |
| `mo` | months (approximated as 30 days) |
| `y` | years (365 days) |

```python
from pytfe.models import parse_ttl_to_ms

parse_ttl_to_ms("2y")    # -> 63_072_000_000
parse_ttl_to_ms("30d")   # -> 2_592_000_000
parse_ttl_to_ms("6mo")   # -> 15_552_000_000
parse_ttl_to_ms("1h")    # -> 3_600_000
```

Use exact day counts (e.g. `"90d"`) when you need precision; months are
approximated as 30 days.

### Important: `audit_trails` token type spelling

The TTL policy API uses `audit_trails` (with an UNDERSCORE) for the
audit-trail policy entry. This is **deliberately different** from the
audit-trail token *creation* endpoint elsewhere in the API which uses
`audit-trails` (with a HYPHEN). The `TokenPolicyType.AUDIT_TRAILS` enum
member preserves the TTL-specific spelling exactly:

```python
from pytfe.models import TokenPolicyType
TokenPolicyType.AUDIT_TRAILS.value  # -> "audit_trails"
```

If you copy a token-type string from another part of the API into a TTL
policy call, the server will reject it. The SDK enforces the correct
value at construction time via the enum.

### Empty-update guard

Building an `OrgTokenTTLPolicyUpdateOptions` with no fields and calling
`update()` raises `pytfe.errors.RequiredFieldMissing` **before** any
HTTP request is made:

```python
client.organization_token_ttl_policies.update(
    "my-org",
    OrgTokenTTLPolicyUpdateOptions(),  # no fields
)
# RequiredFieldMissing: OrgTokenTTLPolicyUpdateOptions requires at
# least one of organization, team, user, or audit_trails to be set.
```

This guards against accidental no-op calls that would otherwise hit the
server and either silently succeed (changing nothing) or fail with a
shape error.

## Operational notes

- **Pair `max_ttl_enabled` with policies.** The TTL policy values are
  only enforced when the org's `max_ttl_enabled` is true. Flip that on
  with `client.organizations.update(org, OrganizationUpdateOptions(max_ttl_enabled=True))`.
- **Reducing TTL doesn't invalidate existing tokens.** Tokens issued
  before a policy change keep their original expiration. Plan rotations
  accordingly.
- **HCP Terraform vs TFE.** Both surfaces are available on both
  platforms (this is not a TFE-only feature, unlike the SAML/SCIM/SMTP
  admin endpoints). Documented version gates are not enforced
  client-side; the server returns the authoritative error if a feature
  isn't available.
