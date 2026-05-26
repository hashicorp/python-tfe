# Scenario: Notification configurations

Notification configurations send run-lifecycle events from a workspace (or
team) to an external destination. HCP Terraform supports four destination
types:

- `email` — sends to a list of organization users.
- `slack` — posts to an incoming-webhook URL.
- `microsoft-teams` — posts to a Microsoft Teams incoming webhook.
- `generic` — POSTs a JSON payload to a URL you control, signed with an HMAC
  token.

This scenario shows how to create each type, verify delivery, and update or
delete configurations later.

Upstream docs:

- Notification configurations: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/notification-configurations
- Notification payload reference: https://developer.hashicorp.com/terraform/cloud-docs/workspaces/settings/notifications

Example: [notification_configuration.py](../../examples/notification_configuration.py)

## Prerequisites

```bash
export TFE_TOKEN="your-api-token"
export TFE_ADDRESS="https://app.terraform.io"
```

The token needs write access on the workspace (or team) that owns the
configuration.

## Create a Slack notification

```python
from pytfe import TFEClient
from pytfe.models import (
    NotificationConfigurationCreateOptions,
    NotificationDestinationType,
    NotificationTriggerType,
)


client = TFEClient()
workspace_id = "ws-abc123"

slack = client.notification_configurations.create(
    workspace_id,
    NotificationConfigurationCreateOptions(
        name="slack-run-events",
        destination_type=NotificationDestinationType.SLACK,
        enabled=True,
        url="https://hooks.slack.com/services/T000/B000/XXXX",
        triggers=[
            NotificationTriggerType.NEEDS_ATTENTION,
            NotificationTriggerType.ERRORED,
            NotificationTriggerType.COMPLETED,
        ],
    ),
)

print(slack.id)
```

Slack and Microsoft Teams configurations need a `url`. The SDK validates this
locally and raises `ValidationError` if the URL is missing for a destination
type that requires it.

## Create a Microsoft Teams notification

```python
teams = client.notification_configurations.create(
    workspace_id,
    NotificationConfigurationCreateOptions(
        name="teams-run-events",
        destination_type=NotificationDestinationType.MICROSOFT_TEAMS,
        enabled=True,
        url="https://outlook.office.com/webhook/...",
        triggers=[
            NotificationTriggerType.ERRORED,
            NotificationTriggerType.NEEDS_ATTENTION,
        ],
    ),
)
```

## Create a generic webhook notification

`generic` posts a JSON payload to your own service. Use the `token` field to
share an HMAC signing secret; HCP Terraform sends `X-TFE-Notification-Signature`
on each delivery so your service can verify authenticity.

```python
import secrets

hmac_secret = secrets.token_urlsafe(32)

webhook = client.notification_configurations.create(
    workspace_id,
    NotificationConfigurationCreateOptions(
        name="generic-webhook",
        destination_type=NotificationDestinationType.GENERIC,
        enabled=True,
        url="https://example.com/tfe-notifications",
        token=hmac_secret,
        triggers=[NotificationTriggerType.COMPLETED],
    ),
)

# Persist hmac_secret in your secret manager — it is not returned again.
```

Store the HMAC secret in a secret manager. The API does not return the token
value on subsequent reads.

## Create an email notification

Email notifications go to organization users, identified either by email
address or by user ID:

```python
email = client.notification_configurations.create(
    workspace_id,
    NotificationConfigurationCreateOptions(
        name="ops-email",
        destination_type=NotificationDestinationType.EMAIL,
        enabled=True,
        triggers=[NotificationTriggerType.ERRORED],
        email_addresses=["oncall@example.com"],
    ),
)
```

`email` configurations do not use `url`. They use `email_addresses` and/or
`email_users` (user objects with an `id`).

## Verify the configuration

`verify()` asks HCP Terraform to deliver a test payload to the configured
destination and records the response on the configuration:

```python
verified = client.notification_configurations.verify(webhook.id)

for delivery in verified.delivery_responses:
    print(delivery.code, delivery.successful, delivery.sent_at)
```

A `successful` value of `"true"` confirms the destination accepted the test
payload. A `code` outside the 2xx range or `successful="false"` indicates the
destination URL is unreachable, returns a non-2xx status, or rejects the
payload format.

Verification works for `slack`, `microsoft-teams`, and `generic`. Email
verification is implicit when the user receives the test message.

## Update an existing configuration

```python
from pytfe.models import NotificationConfigurationUpdateOptions

client.notification_configurations.update(
    slack.id,
    NotificationConfigurationUpdateOptions(
        enabled=False,
    ),
)
```

Disable a configuration with `enabled=False` instead of deleting it when you
want to keep its history of deliveries.

## List and delete

```python
for config in client.notification_configurations.list(workspace_id):
    print(config.id, config.name, config.destination_type, config.enabled)

client.notification_configurations.delete(webhook.id)
```

## Operational notes

- Treat the generic `token` like an HMAC signing key. Rotate it by creating a
  new configuration with a new token, switching consumers to it, then deleting
  the old configuration.
- Verify every new generic webhook before relying on it in production. The API
  will silently drop deliveries to a misconfigured URL.
- Scope triggers narrowly. `NEEDS_ATTENTION` plus `ERRORED` covers most
  on-call needs without paging on every successful apply.
- Slack/Teams incoming-webhook URLs grant posting rights to their channel.
  Store them in a secret manager and rotate them when team membership changes.
