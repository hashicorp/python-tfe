# API index

This page maps `TFEClient` attributes to pyTFE resource services, examples, and
upstream HCP Terraform or Terraform Enterprise API docs. It is intentionally a
high-signal map, not a duplicate of every method signature.

For complete wire-level behavior, use the upstream API docs linked in the last
column.

## Core organization and workspace resources

| Client attribute | Resource class | Common methods | Example | Upstream API docs |
|---|---|---|---|---|
| `client.organizations` | `Organizations` | `list`, `read`, `create`, `update`, `delete`, capacity, entitlements, data retention | [org.py](../../examples/org.py) | [Organizations](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/organizations) |
| `client.projects` | `Projects` | `list`, `read`, `create`, `update`, `delete`, `move_workspaces`, tag bindings | [project.py](../../examples/project.py) | [Projects](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/projects) |
| `client.workspaces` | `Workspaces` | `list`, `read`, `create`, `update`, `delete`, lock/unlock, tags, remote state consumers, data retention | [workspace.py](../../examples/workspace.py) | [Workspaces](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/workspaces) |
| `client.workspace_resources` | `WorkspaceResourcesService` | `list` | [workspace_resources.py](../../examples/workspace_resources.py) | [Workspace resources](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/workspace-resources) |
| `client.ssh_keys` | `SSHKeys` | `list`, `read`, `create`, `update`, `delete` | [ssh_keys.py](../../examples/ssh_keys.py) | [SSH keys](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/ssh-keys) |
| `client.reserved_tag_key` | `ReservedTagKeys` | `list`, `create`, `update`, `delete` | [reserved_tag_key.py](../../examples/reserved_tag_key.py) | [Reserved tag keys](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/reserved-tag-keys) |

## Runs, plans, applies, and state

| Client attribute | Resource class | Common methods | Example | Upstream API docs |
|---|---|---|---|---|
| `client.configuration_versions` | `ConfigurationVersions` | `list`, `read`, `create`, `upload`, `download`, backing-data actions | [configuration_version.py](../../examples/configuration_version.py) | [Configuration versions](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/configuration-versions) |
| `client.runs` | `Runs` | `list`, `list_for_organization`, `read`, `create`, `apply`, `cancel`, `force_cancel`, `force_execute`, `discard` | [run.py](../../examples/run.py) | [Runs](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run) |
| `client.plans` | `Plans` | `read`, `read_for_run`, `logs`, `read_json_output`, `read_json_output_for_run`, `read_json_schema_for_run` | [plan.py](../../examples/plan.py) | [Plans](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/plans) |
| `client.applies` | `Applies` | `read`, `logs`, `errored_state` | [apply.py](../../examples/apply.py) | [Applies](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/applies) |
| `client.assessment_results` | `AssessmentResults` | `read`, `json_output`, `json_schema`, `log_output` | [assessment_result.py](../../examples/assessment_result.py) | [Assessment results](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/assessment-results) |
| `client.run_events` | `RunEvents` | `list`, `read`, `read_with_options` | [run_events.py](../../examples/run_events.py) | [Runs](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run) |
| `client.query_runs` | `QueryRuns` | `list`, `read`, `create`, `logs`, `cancel`, `force_cancel` | [query_run.py](../../examples/query_run.py) | [Query runs](https://developer.hashicorp.com/terraform/enterprise/api-docs/queries) |
| `client.state_versions` | `StateVersions` | `list`, `read`, `read_current`, `create`, `upload`, `download`, `rollback`, backing-data actions | [state_versions.py](../../examples/state_versions.py) | [State versions](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/state-versions) |
| `client.state_version_outputs` | `StateVersionOutputs` | `read`, `read_current` | [state_versions.py](../../examples/state_versions.py) | [State version outputs](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/state-version-outputs) |

## Variables and variable sets

| Client attribute | Resource class | Common methods | Example | Upstream API docs |
|---|---|---|---|---|
| `client.variables` | `Variables` | `list`, `list_all`, `read`, `create`, `update`, `delete` | [variables.py](../../examples/variables.py) | [Workspace variables](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/workspace-variables) |
| `client.variable_sets` | `VariableSets` | `list`, `list_for_workspace`, `list_for_project`, `read`, `create`, `update`, `delete`, apply/remove relationships | [variable_sets.py](../../examples/variable_sets.py) | [Variable sets](https://developer.hashicorp.com/terraform/enterprise/api-docs/variable-sets) |
| `client.variable_set_variables` | `VariableSetVariables` | `list`, `read`, `create`, `update`, `delete` | [variable_sets.py](../../examples/variable_sets.py) | [Variable sets](https://developer.hashicorp.com/terraform/enterprise/api-docs/variable-sets) |

## Teams, users, and access

| Client attribute | Resource class | Common methods | Example | Upstream API docs |
|---|---|---|---|---|
| `client.users` | `Users` | `read`, `read_current`, `update_current` | [user.py](../../examples/user.py) | [Users](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/users) |
| `client.teams` | `Teams` | `list`, `read`, `create`, `update`, `delete`, membership helpers | [team.py](../../examples/team.py) | [Teams](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/teams) |
| `client.team_workspace_accesses` | `TeamWorkspaceAccesses` | `list`, `read`, `add`, `update`, `remove` | [team_workspace_access.py](../../examples/team_workspace_access.py) | [Team access](https://developer.hashicorp.com/terraform/enterprise/api-docs/team-access) |
| `client.team_project_accesses` | `TeamProjectAccesses` | `list`, `read`, `add`, `update`, `remove` | [team_project_access.py](../../examples/team_project_access.py) | [Project team access](https://developer.hashicorp.com/terraform/enterprise/api-docs/project-team-access) |
| `client.team_tokens` | `TeamTokens` | `list`, `read`, `create`, `delete` | [team_token.py](../../examples/team_token.py) | [Team tokens](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/team-tokens) |
| `client.organization_memberships` | `OrganizationMemberships` | `list`, `read`, `create`, `delete` | [organization_membership.py](../../examples/organization_membership.py) | [Organization memberships](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/organization-memberships) |
| `client.organization_tokens` | `OrganizationTokens` | `read`, `create`, `delete` | [organization_token.py](../../examples/organization_token.py) | [Organization tokens](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/organization-tokens) |

## Policies and policy results

| Client attribute | Resource class | Common methods | Example | Upstream API docs |
|---|---|---|---|---|
| `client.policies` | `Policies` | `list`, `read`, `create`, `update`, `delete`, `upload`, `download` | [policy.py](../../examples/policy.py) | [Policies](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policies) |
| `client.policy_sets` | `PolicySets` | `list`, `read`, `create`, `update`, `delete`, add/remove policies, projects, workspaces, exclusions | [policy_set.py](../../examples/policy_set.py) | [Policy sets](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-sets) |
| `client.policy_set_parameters` | `PolicySetParameters` | `list`, `read`, `create`, `update`, `delete` | [policy_set_parameter.py](../../examples/policy_set_parameter.py) | [Policy sets](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-sets) |
| `client.policy_set_versions` | `PolicySetVersions` | `create`, `read`, `upload` | [policy_set.py](../../examples/policy_set.py) | [Policy set versions](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-sets) |
| `client.policy_set_outcomes` | `PolicySetOutcomes` | `list`, `read` | [policy_set.py](../../examples/policy_set.py) | [Policy evaluations](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-evaluations) |
| `client.policy_checks` | `PolicyChecks` | `list`, `read`, `override`, `logs` | [policy_check.py](../../examples/policy_check.py) | [Policy checks](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-checks) |
| `client.policy_evaluations` | `PolicyEvaluations` | `list` | [policy_evaluation.py](../../examples/policy_evaluation.py) | [Policy evaluations](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/policy-evaluations) |

## Run tasks

| Client attribute | Resource class | Common methods | Example | Upstream API docs |
|---|---|---|---|---|
| `client.run_tasks` | `RunTasks` | `list`, `read`, `create`, `update`, `delete` | [run_task.py](../../examples/run_task.py) | [Run tasks](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run-tasks/run-tasks) |
| `client.workspace_run_tasks` | `WorkspaceRunTasks` | `list`, `read`, `create`, `update`, `delete` | [workspace_run_task.py](../../examples/workspace_run_task.py) | [Run tasks](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run-tasks/run-tasks) |
| `client.run_task_integrations` | `RunTaskIntegrations` | `callback` | [run_task_integration.py](../../examples/run_task_integration.py) | [Run task integration](https://developer.hashicorp.com/terraform/enterprise/api-docs/run-tasks/run-tasks-integration) |
| `client.task_stages` | `TaskStages` | `list`, `read`, `override` | [task_stage_example.py](../../examples/task_stage_example.py) | [Run task stages and results](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run-tasks/run-task-stages-and-results) |
| `client.task_results` | `TaskResults` | `read` | [task_result.py](../../examples/task_result.py) | [Run task stages and results](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/run-tasks/run-task-stages-and-results) |

## Agents, registry, integrations, and other resources

> Two registry surfaces: `client.registry` reads the **public** Terraform
> Registry (`registry.terraform.io`, unauthenticated), while
> `client.registry_modules` / `client.registry_providers` (and their version /
> platform sub-resources) manage your organization's **private** registry on
> HCP Terraform / TFE. See [registry.md](registry.md).

| Client attribute | Resource class | Common methods | Example | Upstream API docs |
|---|---|---|---|---|
| `client.agent_pools` | `AgentPools` | `list`, `read`, `create`, `update`, `delete`, assign/remove workspaces/projects | [agent_pool.py](../../examples/agent_pool.py) | [Agents](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/agents) |
| `client.agents` | `Agents` | `list`, `read`, `delete` | [agent.py](../../examples/agent.py) | [Agents](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/agents) |
| `client.agent_tokens` | `AgentTokens` | `list`, `read`, `create`, `delete` | [agent.py](../../examples/agent.py) | [Agent tokens](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/agent-tokens) |
| `client.registry` | `Registry` | `list_modules`, `search_modules`, `list_latest_for_all_providers`, `latest_for_provider`, `get_module`, `list_versions`, `download_url`, `latest_download_url`, `downloads_summary` | [registry.py](../../examples/registry.py) | [Registry API (public, unauthenticated)](https://developer.hashicorp.com/terraform/registry/api-docs) |
| `client.registry_modules` | `RegistryModules` | `list`, `read`, `create`, `update`, `delete`, version and upload helpers | [registry_module.py](../../examples/registry_module.py) | [Registry modules (private)](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/private-registry/modules) |
| `client.no_code_modules` | `NoCodeModules` | `create`, `read`, `update`, `delete`, `read_variables`, `create_workspace`, `upgrade_workspace`, `read_workspace_upgrade`, `confirm_workspace_upgrade` | [no_code_provisioning.py](../../examples/no_code_provisioning.py) | [No-code provisioning](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/no-code-provisioning) |
| `client.aws_oidc_configurations` | `AWSOIDCConfigurations` | `create`, `read`, `update`, `delete` | [oidc_configurations.py](../../examples/oidc_configurations.py) | [AWS OIDC](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/hold-your-own-key/oidc-configurations/aws) |
| `client.azure_oidc_configurations` | `AzureOIDCConfigurations` | `create`, `read`, `update`, `delete` | [oidc_configurations.py](../../examples/oidc_configurations.py) | [Azure OIDC](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/hold-your-own-key/oidc-configurations/azure) |
| `client.gcp_oidc_configurations` | `GCPOIDCConfigurations` | `create`, `read`, `update`, `delete` | [oidc_configurations.py](../../examples/oidc_configurations.py) | [GCP OIDC](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/hold-your-own-key/oidc-configurations/gcp) |
| `client.vault_oidc_configurations` | `VaultOIDCConfigurations` | `create`, `read`, `update`, `delete` | [oidc_configurations.py](../../examples/oidc_configurations.py) | [Vault OIDC](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/hold-your-own-key/oidc-configurations/vault) |
| `client.hyok_configurations` | `HYOKConfigurations` | `list`, `create`, `read`, `delete`, `test`, `revoke` | [hyok_configuration.py](../../examples/hyok_configuration.py) | [HYOK configurations](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/hold-your-own-key/configurations) |
| `client.registry_providers` | `RegistryProviders` | `list`, `read`, `create`, `delete` | [registry_provider.py](../../examples/registry_provider.py) | [Registry providers](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/private-registry/providers) |
| `client.registry_provider_versions` | `RegistryProviderVersions` | `list`, `read`, `create`, `delete` | [registry_provider_version.py](../../examples/registry_provider_version.py) | [Registry providers](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/private-registry/providers) |
| `client.registry_provider_platforms` | `RegistryProviderPlatforms` | `list`, `read`, `create`, `delete` | [registry_provider_platform.py](../../examples/registry_provider_platform.py) | [Registry providers](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/private-registry/providers) |
| `client.oauth_clients` | `OAuthClients` | `list`, `read`, `create`, `update`, `delete`, project relationships | [oauth_client.py](../../examples/oauth_client.py) | [OAuth clients](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/oauth-clients) |
| `client.oauth_tokens` | `OAuthTokens` | `list`, `read`, `update`, `delete` | [oauth_token.py](../../examples/oauth_token.py) | [OAuth tokens](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/oauth-tokens) |
| `client.notification_configurations` | `NotificationConfigurations` | `list`, `read`, `create`, `update`, `delete`, `verify` | [notification_configuration.py](../../examples/notification_configuration.py) | [Notification configurations](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/notification-configurations) |
| `client.organization_audit_configurations` | `OrganizationAuditConfigurations` | `read`, `test`, `update` | [organization_audit_configuration.py](../../examples/organization_audit_configuration.py) | [Audit trail](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/audit-trails) |
| `client.organization_tags` | `OrganizationTags` | `list`, `delete`, `add_workspaces` | [organization_tags.py](../../examples/organization_tags.py) | [Organization tags](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/organization-tags) |
| `client.comments` | `Comments` | `list`, `read`, `create` | [comment.py](../../examples/comment.py) | [Comments](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/comments) |
| `client.explorer` | `Explorer` | query and saved-view helpers | [explorer.py](../../examples/explorer.py) | [Explorer](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/explorer) |
| `client.stacks` | `Stacks` | `list`, `read`, `create`, `update`, `delete`, `force_delete`, VCS fetch | [stack.py](../../examples/stack.py) | [Stacks](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/stacks) |
| `client.stack_configurations` | `StackConfigurations` | `list`, `read`, `create` | [stack_configuration.py](../../examples/stack_configuration.py) | [Stacks](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/stacks) |
| `client.github_app_installations` | `GitHubAppInstallations` | `list`, `read` | [github_app_installations.py](../../examples/github_app_installations.py) | [GitHub App installations](https://developer.hashicorp.com/terraform/enterprise/api-docs/github-app-installations) |
| `client.organization_token_ttl_policies` | `OrganizationTokenTTLPolicies` | `list`, `update`, `reset_to_defaults` | [org_token_ttl.py](../../examples/org_token_ttl.py) | [Org token TTL settings](https://developer.hashicorp.com/terraform/cloud-docs/users-teams-organizations/organizations/settings#api-tokens) |

## TFE admin (site-admin only)

These endpoints require TFE site-admin permission and return `404` on
HCP Terraform (SaaS).

| Client attribute | Resource class | Common methods | Example | Upstream API docs |
|---|---|---|---|---|
| `client.admin.saml_settings` | `_AdminSAMLSettings` | `read`, `update`, `revoke_idp_cert` | [admin_identity.py](../../examples/admin_identity.py) | [SAML settings](https://developer.hashicorp.com/terraform/enterprise/api-docs/admin/settings) |
| `client.admin.scim_settings` | `_AdminSCIMSettings` | `read`, `update`, `delete` | [admin_identity.py](../../examples/admin_identity.py) | [SCIM settings](https://developer.hashicorp.com/terraform/enterprise/api-docs/admin/scim-settings) |
| `client.admin.scim_tokens` | `_AdminSCIMTokens` | `list`, `create`, `read`, `delete` | [admin_identity.py](../../examples/admin_identity.py) | [SCIM tokens](https://developer.hashicorp.com/terraform/enterprise/api-docs/admin/scim-tokens) |
| `client.admin.smtp_settings` | `_AdminSMTPSettings` | `read`, `update` | [admin_smtp.py](../../examples/admin_smtp.py) | [SMTP settings](https://developer.hashicorp.com/terraform/enterprise/api-docs/admin/settings) |

## Focused guides

- [workspaces.md](workspaces.md)
- [runs-plans-applies.md](runs-plans-applies.md)
- [state-versions.md](state-versions.md)
- [variables-and-variable-sets.md](variables-and-variable-sets.md)
- [teams-and-access.md](teams-and-access.md)
- [policies.md](policies.md)
- [run-tasks.md](run-tasks.md)
- [no-code-provisioning.md](no-code-provisioning.md)
- [registry.md](registry.md) — public Terraform Registry vs. the private registry
- [oidc-configurations.md](oidc-configurations.md)
- [admin-identity.md](admin-identity.md)
- [organization-defaults-and-token-ttl.md](organization-defaults-and-token-ttl.md)
