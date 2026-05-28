# HYOK OIDC configurations

Hold-Your-Own-Key (HYOK) OIDC configurations let HCP Terraform federate to
AWS, Azure, GCP, or Vault without storing a static credential. pyTFE exposes
one service per provider:

- `client.aws_oidc_configurations`
- `client.azure_oidc_configurations`
- `client.gcp_oidc_configurations`
- `client.vault_oidc_configurations`

Upstream docs:

- AWS: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/hold-your-own-key/oidc-configurations/aws
- Azure: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/hold-your-own-key/oidc-configurations/azure
- GCP: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/hold-your-own-key/oidc-configurations/gcp
- Vault: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/hold-your-own-key/oidc-configurations/vault

Example: [oidc_configurations.py](../../examples/oidc_configurations.py)

## What these resources do (and do not) manage

These services manage the **HCP Terraform-side configuration record** only.
They do **not** provision the cloud-side trust resources:

| The SDK creates | You still need to provision separately |
|---|---|
| AWS OIDC configuration record (role ARN, organization) | IAM OIDC provider for HCP Terraform; IAM role and trust policy |
| Azure OIDC configuration record (client/subscription/tenant IDs) | Azure AD app registration; service principal; federated credential |
| GCP OIDC configuration record (SA email, project number, workload provider name) | Workload Identity Federation pool/provider; service account IAM bindings |
| Vault OIDC configuration record (address, role, auth path, namespace) | Vault JWT auth method; role; policies |

These configurations require **HYOK / Premium entitlement** on the
organization. Calls against a non-HYOK org return `404` or `403`.

For per-workspace dynamic credentials (not HYOK), see
[scenarios/oidc-dynamic-credentials.md](../scenarios/oidc-dynamic-credentials.md)
— that's still done via `client.variables` or `client.variable_sets`.

## Shared HTTP shape

All four providers hit the same endpoints; the provider is determined by the
JSON:API `data.type` string in the body, not the URL:

| Operation | Method | Path |
|---|---|---|
| Create | `POST` | `/api/v2/organizations/{org}/oidc-configurations` |
| Read | `GET` | `/api/v2/oidc-configurations/{id}` |
| Update | `PATCH` | `/api/v2/oidc-configurations/{id}` |
| Delete | `DELETE` | `/api/v2/oidc-configurations/{id}` |

`data.type` values per provider:

| Provider | `data.type` |
|---|---|
| AWS | `aws-oidc-configurations` |
| Azure | `azure-oidc-configurations` |
| GCP | `gcp-oidc-configurations` |
| Vault | `vault-oidc-configurations` |

## AWS

| Method | Purpose |
|---|---|
| `client.aws_oidc_configurations.create(organization, options)` | Register an IAM role ARN for OIDC federation. |
| `client.aws_oidc_configurations.read(oidc_configuration_id)` | Read configuration. |
| `client.aws_oidc_configurations.update(oidc_configuration_id, options)` | Update role ARN. |
| `client.aws_oidc_configurations.delete(oidc_configuration_id)` | Delete the configuration. |

```python
from pytfe import TFEClient
from pytfe.models import AWSOIDCConfigurationCreateOptions

client = TFEClient()

aws = client.aws_oidc_configurations.create(
    "my-organization",
    AWSOIDCConfigurationCreateOptions(
        role_arn="arn:aws:iam::123456789012:role/hcp-terraform",
    ),
)
print(aws.id, aws.role_arn)
```

## Azure

| Method | Purpose |
|---|---|
| `client.azure_oidc_configurations.create(organization, options)` | Register Azure AD app/subscription/tenant. |
| `client.azure_oidc_configurations.read(oidc_configuration_id)` | Read configuration. |
| `client.azure_oidc_configurations.update(oidc_configuration_id, options)` | Update one or more IDs. |
| `client.azure_oidc_configurations.delete(oidc_configuration_id)` | Delete the configuration. |

```python
from pytfe.models import AzureOIDCConfigurationCreateOptions

azure = client.azure_oidc_configurations.create(
    "my-organization",
    AzureOIDCConfigurationCreateOptions(
        client_id="00000000-0000-0000-0000-000000000000",
        subscription_id="11111111-1111-1111-1111-111111111111",
        tenant_id="22222222-2222-2222-2222-222222222222",
    ),
)
```

All three of `client_id`, `subscription_id`, `tenant_id` are required on
create. Update accepts any subset; unset fields are not touched.

## GCP

| Method | Purpose |
|---|---|
| `client.gcp_oidc_configurations.create(organization, options)` | Register the service account + workload provider. |
| `client.gcp_oidc_configurations.read(oidc_configuration_id)` | Read configuration. |
| `client.gcp_oidc_configurations.update(oidc_configuration_id, options)` | Update SA email, project number, or provider name. |
| `client.gcp_oidc_configurations.delete(oidc_configuration_id)` | Delete the configuration. |

```python
from pytfe.models import GCPOIDCConfigurationCreateOptions

gcp = client.gcp_oidc_configurations.create(
    "my-organization",
    GCPOIDCConfigurationCreateOptions(
        service_account_email="tfc@my-project.iam.gserviceaccount.com",
        project_number="123456789012",
        workload_provider_name=(
            "projects/123456789012/locations/global/"
            "workloadIdentityPools/hcp/providers/hcp-terraform"
        ),
    ),
)
```

## Vault

Vault has the most non-obvious field mappings — the Python names differ from
the wire names:

| Python field | Wire name | Required on create |
|---|---|---|
| `address` | `address` | yes |
| `role_name` | `role` | yes |
| `namespace` | `namespace` | no |
| `jwt_auth_path` | `auth-path` | no |
| `tls_ca_certificate` | `encoded-cacert` | no |

| Method | Purpose |
|---|---|
| `client.vault_oidc_configurations.create(organization, options)` | Register Vault address + role. |
| `client.vault_oidc_configurations.read(oidc_configuration_id)` | Read configuration. |
| `client.vault_oidc_configurations.update(oidc_configuration_id, options)` | Update any field. |
| `client.vault_oidc_configurations.delete(oidc_configuration_id)` | Delete the configuration. |

```python
from pytfe.models import VaultOIDCConfigurationCreateOptions

vault = client.vault_oidc_configurations.create(
    "my-organization",
    VaultOIDCConfigurationCreateOptions(
        address="https://vault.example.com",
        role_name="hcp-terraform",
        namespace="admin",
        jwt_auth_path="jwt",
        tls_ca_certificate="-----BEGIN CERTIFICATE-----\n...",
    ),
)
```

## Token requirements

Write endpoints require an organization, owner, or HYOK admin token. See
HCP's HYOK docs for the exact permission model. Read endpoints follow the
same permission rules as other organization-scoped reads.

## Operational notes

- **Update is partial.** Pass only the fields you want to change. Unset
  fields are not sent on the wire, so the server keeps the existing value.
- **Plan rotations carefully.** Updating the IAM role ARN or service account
  email mid-flight will interrupt any in-progress runs that rely on the
  federated credential.
- **Configurations are per-organization.** If you have multiple HCP
  Terraform organizations sharing a cloud account, each needs its own
  configuration record (and a distinct trust policy/federated credential on
  the cloud side).
- **HYOK is required.** Without the entitlement these endpoints return
  `404`. The SDK will surface that as `pytfe.errors.NotFound`.
