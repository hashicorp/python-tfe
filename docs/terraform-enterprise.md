# Terraform Enterprise

pyTFE supports both HCP Terraform and Terraform Enterprise. Most SDK calls use
the same API paths, but Terraform Enterprise installations often need extra
connection and compatibility setup.

## Address

Set `TFE_ADDRESS` to the base URL of your Terraform Enterprise installation:

```bash
export TFE_ADDRESS="https://tfe.example.com"
export TFE_TOKEN="your-api-token"
```

Do not include `/api/v2`; pyTFE adds API paths internally.

Equivalent explicit configuration:

```python
from pytfe import TFEClient, TFEConfig

client = TFEClient(
    TFEConfig(
        address="https://tfe.example.com",
        token="your-api-token",
    )
)
```

## TLS and private CAs

Use `SSL_CERT_FILE` for private or internal certificate authorities:

```bash
export SSL_CERT_FILE="/etc/ssl/certs/tfe-ca-bundle.pem"
```

Or:

```python
from pytfe import TFEConfig

config = TFEConfig(
    address="https://tfe.example.com",
    token="your-api-token",
    ca_bundle="/etc/ssl/certs/tfe-ca-bundle.pem",
)
```

Disable TLS verification only for controlled local testing:

```bash
export TFE_VERIFY_TLS=false
```

## Private network access

Terraform Enterprise instances are often only reachable from a private network.
If pyTFE works locally but fails in CI, check:

- CI runner network access to the Terraform Enterprise hostname.
- DNS resolution from the runner.
- Corporate proxy rules.
- Firewall rules and allow lists.
- TLS interception and CA trust.

## Older server feature gaps

Some pyTFE methods wrap newer API endpoints. Older Terraform Enterprise
versions may not support every feature exposed by the SDK.

Common signs:

- `404` for an endpoint that exists in current HCP Terraform docs.
- `422` validation errors for newer request attributes.
- Missing response fields or relationships.
- Hosted upload/download URLs not returned by older endpoints.

When adding new automation, test it against the oldest Terraform Enterprise
version you support.

## Enterprise-only and Cloud-only endpoints

Some endpoints are only available in Terraform Enterprise. Others are only
available in HCP Terraform. pyTFE exposes typed errors such as
`UnsupportedInEnterprise` and `UnsupportedInCloud` where the SDK can identify
that distinction.

For behavior questions, compare:

- Terraform Enterprise API docs: https://developer.hashicorp.com/terraform/enterprise/api-docs
- HCP Terraform API docs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs
- go-tfe: https://github.com/hashicorp/go-tfe

