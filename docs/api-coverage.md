# pytfe API Coverage

This document tracks which HCP Terraform / Terraform Enterprise API resources are
implemented in pytfe. Each implemented resource is exposed on the client as
`client.<namespace>`.

**Legend:** ✅ Covered &nbsp;·&nbsp; 🟡 Partial &nbsp;·&nbsp; ❌ Not yet implemented

pytfe implements **61 resource namespaces**. The resources still missing or
partially covered are listed at the bottom of this page.

## Covered resources

| Domain | Resource | Client namespace | Status |
|---|---|---|---|
| Organizations & access | Organizations | `client.organizations` | ✅ |
| | Organization memberships | `client.organization_memberships` | ✅ |
| | Organization tags | `client.organization_tags` | ✅ |
| | Organization tokens | `client.organization_tokens` | ✅ |
| | Organization token TTL policies | `client.organization_token_ttl_policies` | ✅ |
| | Organization audit configuration | `client.organization_audit_configurations` | ✅ |
| | Teams | `client.teams` | ✅ |
| | Team tokens | `client.team_tokens` | ✅ |
| | Team project access | `client.team_project_accesses` | ✅ |
| | Team workspace access | `client.team_workspace_accesses` | ✅ |
| | Users | `client.users` | ✅ |
| | SSH keys | `client.ssh_keys` | ✅ |
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
| | Applies | `client.applies` | ✅ |
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
| Admin | SAML / SCIM / SMTP / token-TTL settings | `client.admin` | ✅ |

## Partial coverage

| Resource | What's covered | What's missing |
|---|---|---|
| Account | 🟡 `client.users.read_current()` returns the authenticated account | Dedicated account-details / update endpoints |
| VCS | 🟡 VCS connections via `client.oauth_clients` / `client.oauth_tokens` | VCS events |
| Audit trails | 🟡 Audit streaming **configuration** via `client.organization_audit_configurations` | Reading audit-trail log entries |

## Not yet implemented

| Resource | Notes |
|---|---|
| Assessment results | Health-assessment reads. Model exists (`models/assessment_result.py`); no resource yet. Surfaced indirectly via `workspace.current_assessment_result`. |
| Plan exports | Sentinel mock / plan export download. Model exists (`models/plan_export.py`); no resource yet. |
| Cost estimates | Run cost-estimation reads. Model exists (`models/cost_estimate.py`); no resource yet. |
| Change requests | ❌ |
| Workspace transfers | Relocating a workspace between organizations. ❌ |
| Recoverable items | Trash / restore of soft-deleted resources. ❌ |
| Subscriptions | Organization subscription management. ❌ |
| Feature sets | ❌ |
| Billing invoices | ❌ |
| Email recipient statuses | Notification email delivery statuses. ❌ |
| VCS events | ❌ |
| TFE site-admin | Site-admin API for self-hosted TFE (admin organizations, users, runs, workspaces, Terraform versions). ❌ |
| GPG keys | Registry provider signing keys. ❌ |
| IP ranges | `/api/meta/ip-ranges`. ❌ |
