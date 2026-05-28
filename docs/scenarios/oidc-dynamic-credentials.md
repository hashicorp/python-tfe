# Scenario: OIDC dynamic credentials

There are **two distinct ways** HCP Terraform federates to cloud providers
via OIDC. They're often confused because they share the same trust model
(OIDC token exchange) but are configured through different APIs.

| Approach | Scope | Configured via | When to use |
|---|---|---|---|
| **HYOK OIDC configurations** | Organization-wide; one trust record per provider | `client.aws_oidc_configurations`, `client.azure_oidc_configurations`, `client.gcp_oidc_configurations`, `client.vault_oidc_configurations` | You have HYOK / Premium entitlement and want one shared org-level trust |
| **Per-workspace dynamic provider credentials** | Per workspace (or variable set) | `client.variables` or `client.variable_sets` with `TFC_*_PROVIDER_AUTH` env vars | Standard HCP Terraform tier; per-workspace or per-environment isolation |

This scenario walks both paths. Pick the one that matches your tier and your
trust model.

Upstream concept docs:

- HYOK OIDC configurations: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/hold-your-own-key/oidc-configurations
- Dynamic provider credentials (per-workspace): https://developer.hashicorp.com/terraform/cloud-docs/dynamic-provider-credentials

API references in this repo:

- [api/oidc-configurations.md](../api/oidc-configurations.md)
- [api/variables-and-variable-sets.md](../api/variables-and-variable-sets.md)

## Prerequisites

```bash
export TFE_TOKEN="your-api-token"
export TFE_ADDRESS="https://app.terraform.io"
export TFE_ORG="my-organization"
```

For the **HYOK path**: you must have HYOK / Premium enabled on the
organization. Otherwise the OIDC configuration endpoints return `404`.

For the **per-workspace path**: standard HCP Terraform is sufficient.

## Path A — HYOK org-level OIDC configuration

A single record per provider per organization. All workspaces in the org
share it.

### AWS

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
print("oidc id:", aws.id)
```

The HCP-side record is now in place. You still need on the AWS side:

- An IAM OIDC identity provider for HCP Terraform's issuer URL.
- An IAM role with a trust policy that lets that OIDC provider assume it.
- The IAM role's permissions for whatever Terraform will manage.

Use the AWS CLI, Terraform AWS provider, or CDK — not this SDK — to
provision those. The SDK only stores the ARN.

### Azure / GCP / Vault

Same shape, different fields. See
[api/oidc-configurations.md](../api/oidc-configurations.md) for the per-
provider field list.

```python
from pytfe.models import (
    AzureOIDCConfigurationCreateOptions,
    GCPOIDCConfigurationCreateOptions,
    VaultOIDCConfigurationCreateOptions,
)

azure = client.azure_oidc_configurations.create(
    "my-organization",
    AzureOIDCConfigurationCreateOptions(
        client_id="00000000-0000-0000-0000-000000000000",
        subscription_id="11111111-1111-1111-1111-111111111111",
        tenant_id="22222222-2222-2222-2222-222222222222",
    ),
)

gcp = client.gcp_oidc_configurations.create(
    "my-organization",
    GCPOIDCConfigurationCreateOptions(
        service_account_email="tfc@my-project.iam.gserviceaccount.com",
        project_number="123456789012",
        workload_provider_name="projects/123456789012/locations/global/workloadIdentityPools/hcp/providers/hcp-terraform",
    ),
)

vault = client.vault_oidc_configurations.create(
    "my-organization",
    VaultOIDCConfigurationCreateOptions(
        address="https://vault.example.com",
        role_name="hcp-terraform",
    ),
)
```

### Updating

Updates are partial — pass only the fields you want to change. Unset
fields are left untouched on the server.

```python
from pytfe.models import AWSOIDCConfigurationUpdateOptions

client.aws_oidc_configurations.update(
    aws.id,
    AWSOIDCConfigurationUpdateOptions(
        role_arn="arn:aws:iam::123456789012:role/hcp-terraform-v2",
    ),
)
```

### Rotation pattern

Rotating the underlying cloud-side role/principal is a two-step dance to
avoid breaking in-progress runs:

1. Create the new IAM role / app registration / SA / Vault role on the
   cloud side. Wait until it's healthy.
2. `update(...)` the HCP OIDC configuration to point at the new identity.
3. Once existing runs have drained, delete the old cloud-side identity.

If you delete the cloud-side identity before step 2 completes, queued runs
will fail with auth errors. Drift the changes in that order.

## Path B — per-workspace dynamic provider credentials

For standard HCP Terraform tiers (no HYOK), or when you want per-workspace
isolation, configure dynamic credentials via **environment variables** on
the workspace or a shared variable set. The exact env var names are
documented per-provider in HCP's dynamic provider credentials docs.

### Example: AWS dynamic credentials on a workspace

```python
from pytfe.models import CategoryType, VariableCreateOptions

workspace_id = "ws-abc123"

# Tells HCP Terraform to mint an OIDC token and assume this role for
# AWS provider calls in this workspace.
client.variables.create(
    workspace_id,
    VariableCreateOptions(
        key="TFC_AWS_PROVIDER_AUTH",
        value="true",
        category=CategoryType.ENV,
    ),
)
client.variables.create(
    workspace_id,
    VariableCreateOptions(
        key="TFC_AWS_RUN_ROLE_ARN",
        value="arn:aws:iam::123456789012:role/hcp-terraform-workspace",
        category=CategoryType.ENV,
    ),
)
```

### Verified-working AWS trust policy + IAM policy

The pyTFE side above (setting `TFC_AWS_PROVIDER_AUTH` + `TFC_AWS_RUN_ROLE_ARN`)
was end-to-end verified against the live AWS + HCP Terraform APIs: a t3.micro
was created and destroyed in ap-south-1 using a federated session derived
from these exact two env vars. The AWS-side trust policy and minimum IAM
policy that worked are shown below — drop these into your AWS account
(via Terraform, CLI, or boto3) and the SDK code above will work as-is.

**OIDC provider** (one per AWS account per HCP issuer):

```
URL:        https://app.terraform.io
Audience:   aws.workload.identity
```

**Trust policy on the IAM role** (`AssumeRolePolicyDocument`):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/app.terraform.io"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "app.terraform.io:aud": "aws.workload.identity"
      },
      "StringLike": {
        "app.terraform.io:sub":
          "organization:<ORG>:project:*:workspace:<WORKSPACE_NAME>:run_phase:*"
      }
    }
  }]
}
```

The `sub` claim format HCP issues is
`organization:<ORG>:project:<PROJECT>:workspace:<WS>:run_phase:<PHASE>`.
Using `StringLike` with `project:*` and `run_phase:*` lets the role be
assumed during plan, apply, or refresh phases without pinning the project
slug; `workspace:<WORKSPACE_NAME>` stays exact so only the intended
workspace can assume the role.

**Minimum EC2 policy** to provision a single instance in a default VPC
(the read permissions look excessive but the Terraform AWS provider
hydrates several VPC/network data sources on every plan):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "ec2:DescribeImages",
      "ec2:DescribeVpcs",
      "ec2:DescribeVpcAttribute",
      "ec2:DescribeVpcClassicLink",
      "ec2:DescribeVpcClassicLinkDnsSupport",
      "ec2:DescribeSubnets",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DescribeNetworkAcls",
      "ec2:DescribeRouteTables",
      "ec2:DescribeSecurityGroups",
      "ec2:DescribeAvailabilityZones",
      "ec2:DescribeAccountAttributes",
      "ec2:DescribeDhcpOptions",
      "ec2:DescribeInstances",
      "ec2:DescribeInstanceAttribute",
      "ec2:DescribeInstanceStatus",
      "ec2:DescribeInstanceTypes",
      "ec2:DescribeInstanceCreditSpecifications",
      "ec2:DescribeVolumes",
      "ec2:DescribeTags",
      "ec2:RunInstances",
      "ec2:TerminateInstances",
      "ec2:CreateTags",
      "ec2:DeleteTags"
    ],
    "Resource": "*"
  }]
}
```

**Gotcha worth calling out:** an obvious-looking minimum policy with just
`ec2:DescribeVpcs`, `RunInstances`, `TerminateInstances`, `CreateTags`
will fail during plan with `UnauthorizedOperation: ec2:DescribeVpcAttribute`
when the `aws_vpc.default` data source tries to read `enableDnsHostnames`.
The provider also reads `DescribeNetworkInterfaces`/`DescribeSecurityGroups`
when planning even a bare `aws_instance` resource. Include the full
`Describe*` set above and the first run will succeed cleanly.

This setup mirrors the
[HashiCorp blog](https://www.hashicorp.com/en/blog/access-aws-from-hcp-terraform-with-oidc-federation)
end-to-end. The blog walks through the AWS-side trust resources using the
Terraform AWS provider; the policies above are the literal JSON
equivalents.

### Example: same setup via a variable set across many workspaces

```python
from pytfe.models import (
    CategoryType,
    VariableSetCreateOptions,
    VariableSetVariableCreateOptions,
)

varset = client.variable_sets.create(
    "my-organization",
    VariableSetCreateOptions(
        name="aws-dynamic-creds",
        description="Shared AWS OIDC dynamic credentials",
        global_=False,
    ),
)

for key, value in [
    ("TFC_AWS_PROVIDER_AUTH", "true"),
    ("TFC_AWS_RUN_ROLE_ARN", "arn:aws:iam::123456789012:role/hcp-terraform-shared"),
]:
    client.variable_set_variables.create(
        varset.id,
        VariableSetVariableCreateOptions(
            key=key,
            value=value,
            category=CategoryType.ENV,
        ),
    )

# Then apply to specific workspaces — see scenarios/manage-workspace-variables.md
```

The env var names differ per provider:

- AWS: `TFC_AWS_PROVIDER_AUTH`, `TFC_AWS_RUN_ROLE_ARN`, etc.
- Azure: `TFC_AZURE_PROVIDER_AUTH`, `TFC_AZURE_RUN_CLIENT_ID`, etc.
- GCP: `TFC_GCP_PROVIDER_AUTH`, `TFC_GCP_RUN_SERVICE_ACCOUNT_EMAIL`, etc.
- Vault: `TFC_VAULT_PROVIDER_AUTH`, `TFC_VAULT_RUN_ROLE`, etc.

See the upstream dynamic-credentials docs for the full per-provider env
var list — it changes occasionally as new auth modes ship.

## Choosing between A and B

- **Use A (HYOK)** when:
  - You have Premium / HYOK entitlement.
  - You want a single auditable record of "what role/principal HCP
    Terraform federates to" per provider per organization.
  - You're standardising on org-wide trust.

- **Use B (per-workspace)** when:
  - You're on standard HCP Terraform.
  - You need different roles per workspace (e.g. dev/staging/prod isolation).
  - You want per-team or per-project trust scopes via variable sets.

It's common to use **B** even with HYOK available, to scope individual
workspaces to least-privilege roles while keeping HYOK as the broader
fallback.

## Operational notes

- Neither approach provisions the cloud-side trust resources. Use the
  cloud provider's SDK or Terraform itself for that.
- Test OIDC trust end-to-end with a no-op plan before relying on it. A
  misconfigured trust policy on the cloud side will fail every run.
- Treat the cloud-side role / app / SA as security-critical. Audit who
  can change its trust policy.
