# pytfe API Coverage

This document tracks which HCP Terraform / Terraform Enterprise API resources are
implemented in pytfe. Each implemented resource is exposed on the client as
`client.<namespace>`. This doc is updated in contrast to v1.1.0 release, and the
resource list is reconciled against the public
[HCP Terraform API documentation](https://developer.hashicorp.com/terraform/cloud-docs/api-docs).

**Legend:** ✅ Covered &nbsp;·&nbsp; 🟡 Partial &nbsp;·&nbsp; ❌ Not yet implemented

pytfe implements **71 resource namespaces**. The resources still missing or
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
| Stack configuration summary | Builds on the existing stack_configuration resource |
| Stack deployment | Core Stacks deployment lifecycle |
| Stack deployment groups | Extends stack_deployment |
| Stack deployment groups summary | Extends stack_deployment_groups |
| Stack deployment runs | Exposes deployment run details |
| Stack deployment steps | Granular deployment step tracking |
| Stack diagnostic | Diagnostics companion to stack_deployment |
| Stack state | State surface for deployed stacks |
| Terraform actions | Only the Run `invoke_action_addrs` field today; no dedicated resource. |
| User tokens | Personal (user) API tokens. |
| VCS events | — |

> Note: the TFE site-admin API (`/api/v2/admin/*`, TFE-only — not part of the
> public HCP Terraform API) **is** implemented under `client.admin` (see the
> Admin rows above).
>
> Note: **team membership** is covered by `client.teams`
> (`add_users` / `remove_users` / `list_users` and the `*_organization_memberships`
> variants), and **audit-trail tokens** are covered by `client.organization_tokens`
> via `token_type=TokenType.AUDIT_TRAILS` — neither is a separate namespace.
