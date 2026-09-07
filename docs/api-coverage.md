# pytfe API Coverage

This document tracks which HCP Terraform / Terraform Enterprise API resources are
implemented in pytfe. Each implemented resource is exposed on the client as
`client.<namespace>`. This doc is updated in contrast to v1.1.0 release, and the
resource list is reconciled against the public
[HCP Terraform API documentation](https://developer.hashicorp.com/terraform/cloud-docs/api-docs).

**Legend:** ✅ Covered &nbsp;·&nbsp; 🟡 Partial &nbsp;·&nbsp; ❌ Not yet implemented

pytfe implements **81 resource namespaces**. The resources still missing or
partially covered are listed at the bottom of this page.

## Covered resources

| Domain | Resource | Client namespace | Status |
|---|---|---|---|
| Organizations & access | Organizations | `client.organizations` | ✅ |
| | Organization memberships | `client.organization_memberships` | ✅ |
| | Organization tags | `client.organization_tags` | ✅ |
| | Organization tokens | `client.organization_tokens` | ✅ |
| | Subscriptions | `client.subscriptions` | ✅ |
| | Invoices | `client.invoices` | ✅ |
| | Organization token TTL policies | `client.organization_token_ttl_policies` | ✅ |
| | Organization audit configuration | `client.organization_audit_configurations` | ✅ |
| | Teams | `client.teams` | ✅ |
| | Team tokens | `client.team_tokens` | ✅ |
| | Team project access | `client.team_project_accesses` | ✅ |
| | Team workspace access | `client.team_workspace_accesses` | ✅ |
| | Users | `client.users` | ✅ |
| | SSH keys | `client.ssh_keys` | ✅ |
| | IP allowlists (CIDR range lists) | `client.cidr_range_lists` | ✅ |
| | CIDR ranges | `client.cidr_ranges` | ✅ |
| Workspaces & config | Workspaces | `client.workspaces` | ✅ |
| | Workspace resources | `client.workspace_resources` | ✅ |
| | Projects | `client.projects` | ✅ |
| | Variables | `client.variables` | ✅ |
| | Variable sets | `client.variable_sets` | ✅ |
| | Variable set variables | `client.variable_set_variables` | ✅ |
| | Configuration versions | `client.configuration_versions` | ✅ |
| | Reserved tag keys | `client.reserved_tag_key` | ✅ |
| Runs & lifecycle | Runs | `client.runs` | ✅ |
| | Run events | `client.run_events` | ✅ |
| | Run triggers | `client.run_triggers` | ✅ |
| | Plans | `client.plans` | ✅ |
| | Plan exports | `client.plan_exports` | ✅ |
| | Applies | `client.applies` | ✅ |
| | Cost estimates | `client.cost_estimates` | ✅ |
| | Assessment results | `client.assessment_results` | ✅ |
| | Comments | `client.comments` | ✅ |
| | Query runs | `client.query_runs` | ✅ |
| | State versions | `client.state_versions` | ✅ |
| | State version outputs | `client.state_version_outputs` | ✅ |
| Policy | Policies | `client.policies` | ✅ |
| | Policy checks | `client.policy_checks` | ✅ |
| | Policy sets | `client.policy_sets` | ✅ |
| | Policy set parameters | `client.policy_set_parameters` | ✅ |
| | Policy set versions | `client.policy_set_versions` | ✅ |
| | Policy set outcomes | `client.policy_set_outcomes` | ✅ |
| | Policy evaluations | `client.policy_evaluations` | ✅ |
| | tf-policy evaluations | `client.tf_policy_evaluations` | ✅ |
| | tf-policy set outcomes | `client.tf_policy_set_outcomes` | ✅ |
| Run tasks | Run tasks | `client.run_tasks` | ✅ |
| | Run task integrations | `client.run_task_integrations` | ✅ |
| | Workspace run tasks | `client.workspace_run_tasks` | ✅ |
| | Task stages | `client.task_stages` | ✅ |
| | Task results | `client.task_results` | ✅ |
| Registry & modules | Registry modules | `client.registry_modules` | ✅ |
| | Registry providers | `client.registry_providers` | ✅ |
| | Registry provider platforms | `client.registry_provider_platforms` | ✅ |
| | Registry provider versions | `client.registry_provider_versions` | ✅ |
| | No-code modules | `client.no_code_modules` | ✅ |
| | Public Registry module API (registry.terraform.io) | `client.registry` | ✅ |
| Agents | Agent pools | `client.agent_pools` | ✅ |
| | Agents | `client.agents` | ✅ |
| | Agent tokens | `client.agent_tokens` | ✅ |
| VCS & integrations | OAuth clients | `client.oauth_clients` | ✅ |
| | OAuth tokens | `client.oauth_tokens` | ✅ |
| | GitHub App installations | `client.github_app_installations` | ✅ |
| Notifications | Notification configurations | `client.notification_configurations` | ✅ |
| Stacks | Stacks | `client.stacks` | ✅ |
| | Stack configurations | `client.stack_configurations` | ✅ |
| | Stack configuration summaries | `client.stack_configuration_summaries` | ✅ |
| | Stack deployments | `client.stack_deployments` | ✅ |
| | Stack deployment groups | `client.stack_deployment_groups` | ✅ |
| | Stack deployment group summaries | `client.stack_deployment_group_summaries` | ✅ |
| | Stack deployment runs | `client.stack_deployment_runs` | ✅ |
| | Stack deployment steps | `client.stack_deployment_steps` | ✅ |
| | Stack diagnostics | `client.stack_diagnostics` | ✅ |
| | Stack states | `client.stack_states` | ✅ |
| Explorer | Explorer | `client.explorer` | ✅ |
| HYOK OIDC | AWS OIDC configurations | `client.aws_oidc_configurations` | ✅ |
| | Azure OIDC configurations | `client.azure_oidc_configurations` | ✅ |
| | GCP OIDC configurations | `client.gcp_oidc_configurations` | ✅ |
| | Vault OIDC configurations | `client.vault_oidc_configurations` | ✅ |
| | HYOK configurations | `client.hyok_configurations` | ✅ |
| Meta | IP ranges | `client.ip_ranges` | ✅ |
| Admin (TFE site-admin) | Organizations, users, runs, workspaces | `client.admin.organizations` / `.users` / `.runs` / `.workspaces` | ✅ |
| | Terraform / OPA / Sentinel versions | `client.admin.terraform_versions` / `.opa_versions` / `.sentinel_versions` | ✅ |
| | SAML / SCIM / SMTP settings + SCIM tokens | `client.admin.saml_settings` / `.scim_settings` / `.scim_tokens` / `.smtp_settings` | ✅ |

## Partial coverage

| Resource | What's covered | What's missing |
|---|---|---|
| Account | 🟡 `client.users.read_current()` returns the authenticated account | Dedicated account-details / update endpoints |
| VCS | 🟡 VCS connections via `client.oauth_clients` / `client.oauth_tokens` | VCS events |
| Audit trails | 🟡 Audit streaming **configuration** via `client.organization_audit_configurations` | Reading audit-trail log entries |

## Not yet implemented

Public HCP Terraform API resources that do not yet have a pytfe client namespace:

| Resource | Notes |
|---|---|
| Change requests | — |
| Feature sets | Organization feature sets. |
| GPG keys | Private Registry provider signing keys. |
| Group member roles | Team member role assignments. |
| Metrics service tokens | Metrics endpoint service tokens. |
| No-code query | `POST /search/no-code-query` — no-code module search. |
| Provider sets | Organization provider sets and their project/workspace attachments. |
| Recoverable items | Soft-delete recovery (`/organizations/{id}/recoverable-items`). TFE only. |
| Task configs | Organization task configs, distinct from the covered `client.run_tasks`. |
| Terraform actions | Only the Run `invoke_action_addrs` field today; no dedicated resource. |
| User tokens | Personal (user) API tokens. |
| VCS events | — |
| VCS repo browsing | `/organizations/{id}/vcs/repo` and `/vcs/tree`. |
| Workspace transfers | Cross-organization workspace transfer requests. |

> Note: the TFE site-admin API (`/api/v2/admin/*`, TFE-only — not part of the
> public HCP Terraform API) **is** implemented under `client.admin` (see the
> Admin rows above).
>
> Note: **team membership** is covered by `client.teams`
> (`add_users` / `remove_users` / `list_users` and the `*_organization_memberships`
> variants), and **audit-trail tokens** are covered by `client.organization_tokens`
> via `token_type=TokenType.AUDIT_TRAILS` — neither is a separate namespace.

## Endpoint-level gaps

The table above is by *namespace*. This one is by *endpoint*, generated by
diffing every path pytfe issues against HashiCorp's published spec — so it
catches sub-resources that a covered namespace does not reach.

Coverage against the [go-tfe OpenAPI spec](https://github.com/hashicorp/go-tfe/blob/main/v2/openapi/spec.json)
(`HCP Terraform/Terraform Enterprise API v2-Beta`, revision `0b4885e7`): pytfe implements
**194 of 300** documented path shapes.

| Area | Missing endpoints | Notes |
|---|---|---|
| **stacks** (10) | `GET /stack-approvals/{id}`<br>`GET /stack-configurations/{id}/stack-deployment-runs`<br>`GET /stack-configurations/{id}/stack-diagnostics`<br>`GET /stack-configurations/{id}/stack-published-outputs`<br>`GET /stack-configurations/{id}/upload-url`<br>`POST /stack-deployment-steps/{id}/fail`<br>`GET /stacks/{id}/latest-output-summary`<br>`GET /stacks/{id}/stack-deployments/{id}/stack-deployment-runs`<br>`GET /stacks/{id}/stack-output-consumers/downstream`<br>`GET /stacks/{id}/stack-output-consumers/upstream` | Manual stack configuration upload (`upload-url`) is here — adding it would unblock a directory-based stack run. |
| **github-app-installations** (7) | `GET /admin/github-app-installations`<br>`POST /admin/github-app-installations/refresh`<br>`GET /github-app-installations`<br>`GET /github-app-installations/{id}/repos`<br>`GET /organizations/{id}/github-app-installations`<br>`POST /organizations/{id}/github-app-installations/{id}/link-account`<br>`GET /organizations/{id}/github-app-installations/{id}/repos` | Partially covered; the repo/link-account sub-resources are missing. |
| **provider-sets** (7) | `DELETE,GET,POST /organizations/{id}/provider-sets`<br>`GET /organizations/{id}/provider-sets/{id}`<br>`GET /projects/{id}/provider-sets`<br>`DELETE,GET,PATCH /provider-sets/{id}`<br>`DELETE,POST /provider-sets/{id}/relationships/projects`<br>`DELETE,POST /provider-sets/{id}/relationships/workspaces`<br>`GET /workspaces/{id}/provider-sets` | Whole feature absent: no `client.provider_sets`. |
| **configuration-versions** (5) | `POST /configuration-versions/{id}/actions/permanently_delete_backing_data`<br>`POST /configuration-versions/{id}/actions/restore_backing_data`<br>`POST /configuration-versions/{id}/actions/soft_delete_backing_data`<br>`GET /runs/{id}/configuration-version`<br>`GET /runs/{id}/configuration-version/download` | — |
| **hyok** (5) | `GET /hyok-configurations/{id}/hyok-customer-key-versions`<br>`DELETE,GET /hyok-customer-key-versions/{id}`<br>`POST /hyok-customer-key-versions/{id}/actions/revoke`<br>`GET /hyok-encrypted-data-keys/{id}`<br>`POST /organizations/{id}/hyok-configurations/test` | — |
| **plans** (5) | `POST /plans/{id}/actions/permanently-delete-backing-data`<br>`POST /plans/{id}/actions/restore-backing-data`<br>`POST /plans/{id}/actions/soft-delete-backing-data`<br>`GET /plans/{id}/json-output-redacted`<br>`GET /plans/{id}/json-schema` | — |
| **task-stages** (4) | `GET /task-result-outcomes/{id}`<br>`GET /task-results/{id}/body`<br>`PATCH /task-results/{id}/callback`<br>`GET /task-results/{id}/outcomes` | — |
| **tasks** (4) | `GET,POST /organizations/{id}/task-configs`<br>`GET /organizations/{id}/task-configs/for-owner`<br>`GET,PATCH /task-configs/{id}`<br>`GET /tasks/integrations` | Organization task configs, distinct from the covered `run_tasks`. |
| **workspace-transfers** (4) | `GET,POST /workspace-transfers`<br>`GET /workspace-transfers/{id}`<br>`POST /workspace-transfers/{id}/actions/cancel`<br>`POST /workspace-transfers/{id}/actions/resume` | Whole feature absent. |
| **applies** (3) | `POST /applies/{id}/actions/permanently-delete-backing-data`<br>`POST /applies/{id}/actions/restore-backing-data`<br>`POST /applies/{id}/actions/soft-delete-backing-data` | — |
| **assessments** (3) | `POST /assessments/{id}/actions/permanently-delete-backing-data`<br>`POST /assessments/{id}/actions/restore-backing-data`<br>`POST /assessments/{id}/actions/soft-delete-backing-data` | — |
| **change-requests** (3) | `GET /change-requests/{id}`<br>`GET,POST /change-requests/{id}/actions/archive`<br>`GET /workspaces/{id}/change-requests` | — |
| **oauth-tokens** (3) | `GET /oauth-clients/{id}/oauth-tokens`<br>`GET /oauth-tokens/{id}/authorized-repos`<br>`GET /oauth-tokens/{id}/vcs-organizations` | — |
| **recoverable-items** (3) | `GET /organizations/{id}/recoverable-items`<br>`POST /recoverable-items/{id}/actions/permanently-delete`<br>`POST /recoverable-items/{id}/actions/recover` | Soft-delete recovery, TFE only. |
| **saml-idp-certificates** (3) | `GET,POST /admin/saml-settings/idp-certificates`<br>`DELETE,GET,PATCH /admin/saml-settings/idp-certificates/{id}`<br>`GET /admin/saml-settings/idp-certificates/{id}/download` | — |
| **varsets** (3) | `DELETE,POST /varsets/{id}/relationships/stacks`<br>`GET /workspaces/{id}/varsets/{id}/relationships/vars`<br>`GET /workspaces/{id}/varsets/{id}/relationships/vars/{id}` | — |
| **workspaces** (3) | `POST /workspaces/{id}/actions/assess`<br>`GET,PATCH,POST /workspaces/{id}/relationships/tag-bindings`<br>`PATCH /workspaces/{id}/relationships/vars` | — |
| **accounts** (2) | `GET /account/hcp-organizations/{id}`<br>`PATCH /account/password` | — |
| **admin-banners** (2) | `GET,POST /admin/banners`<br>`DELETE,PATCH /admin/banners/{id}` | TFE site-admin banners. |
| **email-recipient-statuses** (2) | `GET,POST /email-recipient-statuses/unsubscribe`<br>`GET,POST /email-recipient-statuses/verify` | — |
| **feature-sets** (2) | `GET /feature-sets`<br>`GET /organizations/{id}/feature-sets` | — |
| **metrics-tokens** (2) | `GET,POST /organizations/{id}/metrics-tokens`<br>`DELETE /organizations/{id}/metrics-tokens/{id}` | Metrics endpoint service tokens. |
| **queries** (2) | `POST /search/no-code-query`<br>`GET /search/no-code-query/{id}` | No-code module search. |
| **registry** (2) | `GET /organizations/{id}/registry-modules/validation`<br>`GET /organizations/{id}/tests/registry-modules/{id}/{id}/{id}/{id}/test-runs/{id}/cleanups/{id}` | — |
| **vcs** (2) | `GET /organizations/{id}/vcs/repo`<br>`GET /organizations/{id}/vcs/tree` | Repository and tree browsing for a connected VCS provider. |
| **Notification Configurations** (1) | `GET,POST /projects/{id}/notification-configurations` | — |
| **admin-customization-settings** (1) | `GET,PATCH /admin/customization-settings` | — |
| **admin-saml-settings** (1) | `POST /admin/saml-settings/actions/cert-validation` | — |
| **assessment-results** (1) | `GET /assessment-results/{id}/sanitized-plan` | — |
| **audit-trails** (1) | `GET /organization/audit-trail` | — |
| **authentication-tokens** (1) | `GET,POST /users/{id}/authentication-tokens` | User (personal) API tokens — the gap `token_audit` reports. |
| **banners** (1) | `GET /banners` | — |
| **notification-configurations** (1) | `POST /notification-configurations/{id}/actions/enable` | — |
| **organizations** (1) | `GET /organizations/{id}/relationships/module-producers` | — |
| **policy-evaluations** (1) | `GET /policy-evaluations/{id}` | — |
| **policy-sets** (1) | `DELETE,POST /policy-sets/{id}/tag-selectors` | — |
| **projects** (1) | `GET,PATCH,POST /projects/{id}/relationships/tag-bindings` | — |
| **run-tasks** (1) | `GET /tasks/{id}/relationships/workspace-tasks` | — |
| **users** (1) | `GET /users/{id}/github-app-oauth-tokens` | — |
| **vcs-events** (1) | `GET /organizations/{id}/vcs-events` | — |

**Reading this table.** A path here means pytfe issues no request to it. A few
are covered by an equivalent route rather than genuinely missing — pytfe reads a
plan's JSON schema at `/runs/{id}/plan/json-schema` rather than
`/plans/{id}/json-schema`, and tag bindings at `/workspaces/{id}/tag-bindings`
rather than `/workspaces/{id}/relationships/tag-bindings`. Check the resource
module before concluding a capability is absent.

Three of these are load-bearing for the workflow layer, and
[`docs/workflows/README.md`](workflows/README.md) documents the consequences:

- `GET /stack-configurations/{id}/upload-url` — without it there is no way to
  upload a stack configuration from a local directory, which is why
  `pytfe.workflows` has no `stack_run_from_directory`.
- `GET /stack-configurations/{id}/stack-diagnostics` — prepare-time stack
  diagnostics are unreachable, so `diagnose_stack_configuration` returns the
  prepare log URL instead.
- `GET,POST /users/{id}/authentication-tokens` — user API tokens cannot be
  enumerated, which `token_audit` reports as a warning.

To regenerate this section, diff the spec against the resource layer as
described in [`AGENTS.md`](../AGENTS.md); the spec revision is recorded above so
a later reader can tell how stale it is.
