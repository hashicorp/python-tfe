# Unreleased

## Enhancements

### New resources
* Added `client.stack_deployments` — list the deployments that belong to a stack. `list(stack_id, options=None)` (`GET /stacks/{stack_id}/stack-deployments`) returns an `Iterator[StackDeployment]`, with optional pagination (`page_size`) and `?include=` (`latest_deployment_run`, `latest_deployment_run.stack_configuration`) via `StackDeploymentListOptions`. The `stack` relationship is hydrated as a typed field; the `latest-deployment-run` relation is reachable via the lossless raw accessors (`deployment.related("latest-deployment-run")`). New models: `StackDeployment`, `StackDeploymentListOptions`, `StackDeploymentIncludeOpt`.
* Added `client.stack_deployment_groups` — list, read, approve, and rerun deployment groups within a stack configuration. `list(stack_configuration_id)` (`GET /stack-configurations/{id}/stack-deployment-groups`), `read(group_id)` (`GET /stack-deployment-groups/{id}`), `read_by_name(stack_configuration_id, name)`, `approve_all_plans(group_id)` (`POST .../approve-all-plans`), `rerun(group_id, options)` (`POST .../rerun?deployments=...`). New models: `StackDeploymentGroup`, `DeploymentGroupStatus`, `StackDeploymentGroupListOptions`, `StackDeploymentGroupRerunOptions`.
* Added `client.stack_deployment_runs` — list, read, approve, and cancel individual deployment runs within a deployment group. `list(group_id)` (`GET /stack-deployment-groups/{id}/stack-deployment-runs`), `read(run_id)` (`GET /stack-deployment-runs/{id}`), `approve_all_plans(run_id)` (`POST .../approve-all-plans`), `cancel(run_id)` (`POST .../cancel`). New models: `StackDeploymentRun`, `DeploymentRunStatus`, `StackDeploymentRunListOptions`, `StackDeploymentRunReadOptions`, `StackDeploymentRunIncludeOpt`.
* Added `client.stack_deployment_steps` — list, read, advance, list diagnostics, and download artifacts for individual deployment steps within a deployment run. `list(run_id)` (`GET /stack-deployment-runs/{id}/stack-deployment-steps`), `read(step_id)` (`GET /stack-deployment-steps/{id}`), `advance(step_id)` (`POST .../advance`), `list_diagnostics(step_id)` (`GET .../stack-diagnostics`), `download_artifact(step_id, artifact_type)` (`GET .../artifacts?name=<type>`) returns raw `bytes`. New models: `StackDeploymentStep`, `DeploymentStepStatus`, `StackDeploymentStepArtifactType`, `StackDeploymentStepIncludeOpt`, `StackDeploymentStepListOptions`, `StackDeploymentStepReadOptions`, `StackDiagnostic`, `StackDiagnosticListOptions`.

# Released
# v1.2.0

## Enhancements

### Relationships
Related data is now a complete, first-class part of every response. Before, `?include=` often did not actually fill the related fields it returned, and anything the SDK did not model as a typed field was dropped on the floor. Now the full set of related resources the API hands back is always available to you: typed where pytfe models it, raw where it does not. The practical win is that **you are no longer limited to the relationships pytfe has added typed support for.** You can read any related resource in a response without dropping to manual HTTP or waiting for a new SDK release.
* `?include=` now fills in related data. When the SDK models a relation as a typed field (for example `workspace.outputs`, `policy_set.current_version`, `organization_membership.user`, `run_event.actor`), passing `?include=<relation>` fills that field with the real record instead of an id-only stub.
* Relations the SDK does **not** model are no longer lost. Every top-level resource model now derives from a new `pytfe.models.TFEModel` base and gains read-only accessors for the raw JSON:API data the API returned: `model.relationships`, `model.included`, `model.related(name)`, `model.included_by(type, id)`, and the `model.has_relationships` and `model.has_included` flags. So when a relation has no typed field of its own (for example an organization's `subscription`, or a workspace `readme`), `?include=` still returns it and you reach it with `model.related("subscription")` or `model.included_by(type, id)`. These accessors are read-only extras that never appear in `model_dump()` or affect equality, so this is additive and non-breaking. List endpoints expose the relationship refs but do not yet fill `included`. See [docs/related-resources.md](docs/related-resources.md) for the per-resource table and a "typed field vs raw accessor" guide.
* Added `?include=` support to three reads that previously had no include option, matching the HCP Terraform API:
  * `teams.read(team_id, TeamReadOptions(include=[...]))`: `users`, `organization-memberships`.
  * `task_stages.read(task_stage_id, TaskStageReadOptions(include=[...]))`: `run`, `run.workspace`, `task-results`, `policy-evaluations`.
  * `organizations.read(name, OrganizationReadOptions(include=[...]))`: `subscription`. The new `options` argument is optional, so existing calls are unchanged.

### New resources
* Added `client.subscriptions` — read an organization's subscription (HCP Terraform only). `read_for_organization(org)` (`GET /organizations/{org}/subscription`) and `read(id)` (`GET /subscriptions/{id}`). The linked feature set is hydrated into `.included` and reachable via `subscription.related("feature-set")`. New model: `Subscription`. New error: `InvalidSubscriptionIDError`.
* Added `client.invoices` — read an organization's billing invoices (HCP Terraform only). `list(org)` (cursor-paginated via `meta.continuation`, fixed page size 10) and `read_next(org)` (the upcoming invoice, or `None` when there is no upcoming invoice). New model: `Invoice`.
* Added `client.ip_ranges` — read HCP Terraform / Terraform Enterprise outbound IP ranges via `GET /api/meta/ip-ranges`. `read(modified_since=None)` returns an `IPRange` (CIDR lists for `api`, `notifications`, `sentinel`, `vcs`), or `None` when an `If-Modified-Since` date is supplied and the ranges are unchanged (HTTP 304). New model: `IPRange`.
* Added `client.plan_exports` — export Terraform plan data (Sentinel mock bundles). `create(options)`, `read(id)`, `delete(id)`, and `download(id)` (returns the `.tar.gz` archive bytes, following the temporary presigned-URL redirect). New models: `PlanExport`, `PlanExportCreateOptions`, `PlanExportStatus`, `PlanExportDataType`, `PlanExportStatusTimestamps`. New errors: `InvalidPlanExportIDError`, `RequiredPlanError`.
* Added `client.cost_estimates` — read run cost estimates. `read(id)` returns a `CostEstimate`; `logs(id)` returns the estimate's log output text. `CostEstimate`, `CostEstimateStatus`, and `CostEstimateStatusTimestamps` are now exported from `pytfe.models`. New error: `InvalidCostEstimateIDError`.
* Added IP allowlists (the JSON:API `cidr-range-lists` / `cidr-ranges` resources) as `client.cidr_range_lists` and `client.cidr_ranges`. `cidr_range_lists` supports `list`, `create`, `read`, `update`, `delete`, plus `list_cidr_ranges`, `add_cidr_range`, and `add_agent_pools` / `remove_agent_pools`; `cidr_ranges` supports `read`, `update`, `delete`. New models: `CIDRRangeList`, `CIDRRange`, `EnforcementScope`, and their create/update/list options. New errors: `InvalidCIDRRangeListIDError`, `InvalidCIDRRangeIDError`, `RequiredCIDRBlockError`.
* Added `client.registry` — a client for the **public Terraform Registry** module API (`registry.terraform.io`). This is a new, unauthenticated surface on a different host (the SDK never sends the bearer token to the registry); `base_url` is configurable for other registries implementing the module registry protocol. Methods: `list_modules`, `search_modules`, `list_latest_for_all_providers`, `latest_for_provider`, `get_module`, `list_versions`, `download_url`, `latest_download_url`, and `downloads_summary`. New models are exported under the `PublicRegistry*` prefix (e.g. `PublicRegistryModule`, `PublicRegistryModuleVersions`, `PublicRegistryModuleDownloadsSummary`). New errors: `InvalidModuleNamespaceError`, `InvalidModuleNameError`, `InvalidModuleProviderError`, `InvalidModuleVersionError`.
* Added `client.assessment_results` — read workspace health assessment (drift detection / continuous validation) results. `read(id)` returns an `AssessmentResult`; `json_output(id)` and `json_schema(id)` return the underlying JSON plan / provider schema (following the blob redirect, `None` on 204); `log_output(id)` returns the Terraform JSON log as text. `AssessmentResult` is now a `TFEModel`, so its `workspace`/`source` relationships are reachable via `.relationships` / `.related(...)`. New error: `InvalidAssessmentResultIDError`.
* Added `client.hyok_configurations` — manage HYOK (Hold Your Own Key) configurations. `list(org)`, `create(org, options)`, `read(id)`, `delete(id)`, `test(id)`, and `revoke(id)`. A HYOK configuration ties an OIDC configuration (`client.*_oidc_configurations`) and an agent pool to a customer-controlled KMS key; this is the parent resource for the per-cloud OIDC configs. A configuration must be revoked before it can be deleted. New models: `HYOKConfiguration`, `HYOKConfigurationCreateOptions`, `HYOKConfigurationStatus`, `HYOKKMSOptions`, `OIDCConfigurationType`. New errors: `InvalidHYOKConfigurationIDError`, `RequiredKEKIDError`.

### Discovery for AI agents and tooling
The installed package is now self-describing, so a consumer (including an AI
agent or other tooling working only from `site-packages/pytfe`) can enumerate and
drive the SDK without hardcoding resource names or browsing the GitHub repo.
* `pytfe.describe()` returns a machine-readable manifest of the API surface —
  every resource namespace on `TFEClient`, its public methods, signatures, and
  one-line summaries, with the `admin` namespace nested. It makes no network
  calls (a throwaway client with an empty config is used purely to introspect
  the wiring) and the result is JSON-serializable. Each method's `*Options`
  model still exposes JSON Schema via `model_json_schema()`.
* `pytfe.llms_txt()` returns a concise, agent-oriented orientation guide that
  now ships inside the wheel at `pytfe/llms.txt` (alongside `py.typed`).
* `TFEClient` gained a comprehensive class docstring (resource namespaces,
  quickstart, conventions) so `help(TFEClient)` and IDE hover are useful, and
  it is now a context manager: `with TFEClient(...) as tfe: ...` closes the
  pooled HTTP connection automatically. `close()` is documented and idempotent.
* Every public resource method now ships a Google-style docstring — a one-line
  summary plus `Args`, `Returns`, `Raises`, and a runnable `Example:` block
  (sections included as applicable). These are written for consumers and the AI
  coding assistants (Copilot/Claude/Cursor) that read them via the language
  server from `site-packages`, so completions for pytfe calls are more accurate
  out of the box. Return-shape gotchas (single-use `Iterator`, raw `bytes` for
  blob downloads, `None` for `204`s) and the exact exceptions each method raises
  are now documented in place. Linked from the README's new *AI coding
  assistants* row alongside `llms.txt`.
* `StateVersionIncludeOpt` and `PolicySetOutcomeListOptions` are now exported
  from `pytfe.models`, matching the rest of their model families.

### Packaging
* The source distribution (sdist) now includes `examples/`, `CHANGELOG.md`, and
  `AGENTS.md` so source consumers get the full example and changelog context.
  The wheel is unchanged (examples remain non-importable).


## Bug Fixes

### Relationships
* Fixed `workspaces.read*(include=[WorkspaceIncludeOpt.OUTPUTS])` returning outputs with `None` name, value, and type. Workspace `outputs` is now filled from the `included` data. [#134](https://github.com/hashicorp/python-tfe/issues/134)
* Fixed `policy_set.read*(include=[current_version | newest_version])` returning an id-only stub. `PolicySetVersion` is now exported from `pytfe.models` and fully resolved, so the version's `source`, `created_at`, and `status` are populated.
* Fixed `variable_set.read` inventing placeholder values (such as `name="workspace-<id>"` or `key="var-<id>"`) for `workspaces`, `projects`, and `vars`. These are now id-only stubs by default and fill from `included` when requested.

### Cost estimates
* Fixed `CostEstimate` failing to parse real API responses: `status-timestamps` now treats every timestamp as optional (the API only returns the ones that have occurred) and adds the missing `pending-at`, and `error-message` now accepts `null`. Previously an included `cost-estimate` with a null error or partial timestamps would silently collapse to an id-only stub.

### Transport
* Fixed the shared HTTP client retaining `Set-Cookie` session cookies across requests. The `/api/meta/ip-ranges` endpoint returns an `_atlas_session_data` cookie; once stored, that browser session silently overrode bearer-token auth on every subsequent request, causing spurious `401`/`404` errors. The transport now never persists cookies (this SDK authenticates only with the bearer token). Without this fix, any call to `client.ip_ranges.read()` broke all later authenticated calls on the same client.

### Organizations
* Fixed `organizations.read_entitlements` silently dropping most entitlement flags. The parser surfaced only 15 of the ~47 flags the API returns, so flags such as `hyok`, `assessments`, `stacks`, `terraform-actions`, and `change-requests` were discarded. `Entitlements` now exposes those as typed fields and retains every remaining flag (including the integer `*-limit` flags) under `model_extra` via `extra="allow"`. The change is additive — existing typed fields are unchanged.


# Released
# v1.1.0

## Features

### TFE admin identity (SAML / SCIM)
* Added ``client.admin`` nested namespace exposing three TFE-only services: ``client.admin.saml_settings`` (read, update, revoke_idp_cert), ``client.admin.scim_settings`` (read, update, delete), and ``client.admin.scim_tokens`` (list, create, read, delete). All endpoints return ``pytfe.errors.NotFound`` on HCP Terraform (SaaS) — verified live against ``app.terraform.io``.
* Added models: ``AdminSAMLSettings`` / ``AdminSAMLSettingsUpdateOptions``, ``AdminSCIMSettings`` / ``AdminSCIMSettingsUpdateOptions``, ``AdminSCIMToken`` / ``AdminSCIMTokenCreateOptions``, plus ``SAMLProviderType`` and ``SAMLSignatureMethod`` enums.
* ``AdminSCIMSettingsUpdateOptions`` distinguishes "field unset" from "field explicitly set to None" for ``site_admin_group_scim_id``. Pass ``None`` to send JSON ``null`` (unlinking the SCIM site-admin group); omit the kwarg entirely to leave the server value untouched. The omit-vs-explicit-null distinction is preserved end-to-end via a custom ``to_payload()`` that inspects Pydantic's ``model_fields_set``.
* Added typed exceptions ``InvalidSAMLProviderTypeError``, ``InvalidSCIMTokenIDError``, ``RequiredSCIMTokenDescriptionError``.
* The transport-level redacting logger now redacts the wire-format ``private-key`` field (with hyphen) in addition to the existing ``private_key`` (with underscore), so SAML SP private keys cannot leak via ``PYTFE_LOG=debug``. X.509 certificate fields (``idp-cert``, ``certificate``, ``old-idp-cert``) are intentionally NOT redacted because they're public material by design.

### GitHub App installation discovery
* Added ``client.github_app_installations`` resource with ``list`` (supports ``filter[name]`` and ``filter[installation_id]``) and ``read`` methods for looking up GitHub App installations the authenticated user can see. Returns ``GitHubAppInstallation`` records carrying both the HCP-side ``id`` (``ghain-...``) and the GitHub-side numeric ``installation_id``. The actual GitHub App authorisation flow happens through the HCP Terraform UI; this resource is the discovery surface workspace/stack/registry-module VCS configuration consumes.
* Added model ``GitHubAppInstallation``, ``GitHubAppInstallationListOptions``, ``GitHubAppInstallationType``.
* Added typed exception ``InvalidGitHubAppInstallationIDError``.

### HYOK OIDC Configurations
* Added aws_oidc_configurations, azure_oidc_configurations, gcp_oidc_configurations, and vault_oidc_configurations resources with create, read, update, and delete methods for Hold-Your-Own-Key OIDC configuration records. All four hit a single polymorphic HCP endpoint (POST /organizations/{org}/oidc-configurations for create, /oidc-configurations/{id} for read/update/delete) dispatched by JSON:API data.type, matching the structure used by go-tfe and the terraform-tfe provider.
* Added typed models per provider: AWSOIDCConfiguration / AzureOIDCConfiguration / GCPOIDCConfiguration / VaultOIDCConfiguration plus matching CreateOptions and UpdateOptions for each.
* Azure / GCP / Vault UpdateOptions are fully partial — only supplied fields are sent on the wire. AWSOIDCConfigurationUpdateOptions REQUIRES role_arn because the AWS resource has exactly one updatable attribute, matching go-tfe's AWSOIDCConfigurationUpdateOptions.valid() behaviour (ErrRequiredRoleARN). Constructing AWSOIDCConfigurationUpdateOptions() with no arguments now raises a pydantic ValidationError at construction time instead of silently sending an empty PATCH whose server-side behaviour was never verified.
* AWSOIDCConfigurationCreateOptions and AWSOIDCConfigurationUpdateOptions both reject empty-string role_arn values via a non-empty field validator, mirroring go-tfe's local validation.
* Added InvalidOIDCConfigurationIDError typed exception.
* These resources require HYOK / Premium entitlement on the organization; calls against a non-HYOK org return NotFound. The SDK manages only the HCP-side configuration record — the cloud-side trust resources (IAM role, Azure federated credential, GCP workload identity pool, Vault JWT auth method) still need to be provisioned separately.

## Bug Fixes

### Pagination
* Fixed `list_*` infinite-looping for API call which are non paginated, so they are now fetched with a single request. The generic list helper also treats any response without `meta.pagination` as a single complete page, preventing the same loop on other non-paginated endpoints. [#181](https://github.com/hashicorp/python-tfe/issues/181)

### Relationships
* Unified JSON:API relationship parsing into a single canonical helper, replacing the per-resource hand-rolled logic across runs, workspaces, no-code modules and more. [#180](https://github.com/hashicorp/python-tfe/pull/180)
* `?include=`'d relations are now fully hydrated from the response's `included` block (e.g. `workspace.current_run.status`) instead of being returned as id-only stubs.
* Models retain unknown server attributes in `model_extra` (`extra="allow"`) instead of silently dropping them, keeping output closer to the live API.
* Added missing `Workspace` fields `latest_run`, `latest_change_at`, `last_assessment_result_at`, and `source_module_id`, which previously raised `AttributeError`. [#179](https://github.com/hashicorp/python-tfe/issues/179)


# v1.0.0

## Features

### Teams
* Added Teams resource with full CRUD operations (list, create, read, update, delete) by @isivaselvan [#118](https://github.com/hashicorp/python-tfe/pull/118)
* Added add_users, remove_users, add_organization_memberships, remove_organization_memberships, list_users and list_organization_memberships methods by @iam404 [#171](https://github.com/hashicorp/python-tfe/pull/168)

### Team Project Access
* Added Team Project Access resource with list, add, read, update, and remove methods by @isivaselvan [#127](https://github.com/hashicorp/python-tfe/pull/127)

### Stacks
* Added Stack resource with create, update, list, read, delete, force_delete and fetch_latest_from_vcs methods by @isivaselvan [#128](https://github.com/hashicorp/python-tfe/pull/128)

### Explorer API
* Added Explorer resource support with query, CSV export, list saved view, create saced view, read saved view, update saved view, delete saved view, saved view result query, and saved view CSV export endpoints by @jasodeep [#136](https://github.com/hashicorp/python-tfe/pull/136)

### Organization Tokens
* Added Organization Token resource with full Create, read, delete and create/read/delete with options operations by @NimishaShrivastava-dev [#141](https://github.com/hashicorp/python-tfe/pull/141)

### Users
* Added User resource with read, read_current, and update_current methods by @TanyaSingh369-svg [#144](https://github.com/hashicorp/python-tfe/pull/144)

### Registry Provider Platform
* Added Registry Provider Platform resource with create, list, read, and delete methods by @isivaselvan [#145](https://github.com/hashicorp/python-tfe/pull/145)

### Organization Tags
* Added Organization Tags resource with list, add_workspaces, and delete methods by @NimishaShrivastava-dev [#146](https://github.com/hashicorp/python-tfe/pull/146)

### Stack Configuration
* Added Stack Configuration resource with create, list, and read methods by @isivaselvan [#147](https://github.com/hashicorp/python-tfe/pull/147)

### Organization Audit Configurations
* Added Organization Audit Configuration resource with list, read and update support by @NimishaShrivastava-dev [#154](https://github.com/hashicorp/python-tfe/pull/154)

### Comments
* Added Comment resource with list, read, and create methods by @isivaselvan [#155](https://github.com/hashicorp/python-tfe/pull/155)

### Task Result
* Added Task Result resource with read method, typed models, and unit tests by @TanyaSingh369-svg [#156](https://github.com/hashicorp/python-tfe/pull/156)

### Team Tokens
* Added Team Token resource with list, read, create, and delete methods supporting both legacy and new multi-team token APIs by @isivaselvan [#157](https://github.com/hashicorp/python-tfe/pull/157)

### Run Task Integration
* Added Run Task Integration resource with callback support for sending run task results back to Terraform, including callback payload models and webhook server example by @TanyaSingh369-svg [#160](https://github.com/hashicorp/python-tfe/pull/160)

### State Version Upload
* Added state version upload support with presigned URL flow and improved examples by @NimishaShrivastava-dev [#163](https://github.com/hashicorp/python-tfe/pull/163)

### Workspace Run Task
* Added Workspace Run Task resource CRUD operation with models for managing run tasks associated with a workspace by @isivaselvan [#164](https://github.com/hashicorp/python-tfe/pull/164)

### Task Stage
* Added Task Stage resource and models for interacting with run task stages by @isivaselvan [#165](https://github.com/hashicorp/python-tfe/pull/165)

### Team Workspace Access
* Added Team Workspace Access resource list, read, add, update and remove methods along with models and examples for managing team access to workspaces by @iam404 [#168](https://github.com/hashicorp/python-tfe/pull/168)

### No-Code Provisioning
* Added no_code_modules resource with create, read, update, delete, read_variables, create_workspace, upgrade_workspace, read_workspace_upgrade, and confirm_workspace_upgrade methods.

## Enhancements

### Terraform Actions
* Added invoke action address field to Run and RunCreateOptions models to support Terraform action invocations by @isivaselvan [#158](https://github.com/hashicorp/python-tfe/pull/158)

### Agent Pool
* Updated Agent Pool models to include project_ids and workspace_ids (allowed and excluded) fields by @isivaselvan [#166](https://github.com/hashicorp/python-tfe/pull/166)
* Added assign_to_project method to the Agent Pool resource for associating agent pools with projects by @isivaselvan [#166](https://github.com/hashicorp/python-tfe/pull/166)
* Added typed agent pool error classes (InvalidAgentPoolIDError and related) by @isivaselvan [#166](https://github.com/hashicorp/python-tfe/pull/166)
* Updated AgentPoolListOptions with new filter parameters for list method by @isivaselvan [#166](https://github.com/hashicorp/python-tfe/pull/166)

### Existing Resource Improvements
* Updated Apply resource with errored_state method which uses additional read endpoints and log download support by @iam404 [#168](https://github.com/hashicorp/python-tfe/pull/168)
* Updated Configuration Version resource with ingress_attributes method which uses additional endpoints for uploaded configuration handling by @iam404 [#168](https://github.com/hashicorp/python-tfe/pull/168)
* Updated Plan resource with additional read_for_run, read_json_output_for_run, read_json_schema_for_run and follow_json_output_redirect methods by @iam404 [#168](https://github.com/hashicorp/python-tfe/pull/168)
* Updated Policy Set resource with new add_project_exclusions, remove_project_exclusions methods to support project exclusions by @iam404 [#168](https://github.com/hashicorp/python-tfe/pull/168)
* Updated Projects resource with new move_workspaces (into project) method iterator conversion of list_effective_tag_bindings operations by @iam404 [#168](https://github.com/hashicorp/python-tfe/pull/168)
* Updated Registry Module resource with iterator conversion of list_version method by @iam404 [#168](https://github.com/hashicorp/python-tfe/pull/168)
* Updated State Version resource with new rollback method by @iam404 [#168](https://github.com/hashicorp/python-tfe/pull/168)
* Updated Workspaces resource with additional current_assessment_result and list_applicable_varsets methods by @iam404 [#168](https://github.com/hashicorp/python-tfe/pull/168)

### SDK Logging
* Added pytfe._logging module with structured stdlib-based logging framework by @iam404 [#171](https://github.com/hashicorp/python-tfe/pull/171)
* Added setup_logging() function to configure the pytfe logger namespace with optional level and format control by @iam404 [#171](https://github.com/hashicorp/python-tfe/pull/171)
* Added HTTP transport tracing via RoundTrip formatter with request/response logging, header/body redaction, and configurable truncation by @iam404 [#171](https://github.com/hashicorp/python-tfe/pull/171)
* Added PYTFE_LOG, PYTFE_LOG_HEADERS, and PYTFE_LOG_TRUNCATE_BYTES environment variables for runtime log configuration by @iam404 [#171](https://github.com/hashicorp/python-tfe/pull/171)

## Breaking Changes

### Agent Pool
* Removed allowed_workspace_policy attribute from Agent Pool models and methods by @isivaselvan [#166](https://github.com/hashicorp/python-tfe/pull/166)
* Updated AgentPool relationship model structure — consumers referencing the old relationship fields must update to the new project_ids/workspace_ids shape by @isivaselvan [#166](https://github.com/hashicorp/python-tfe/pull/166)

## Bug Fixes
* Fixed task result relationships to map into typed SDK models instead of raw JSON by @TanyaSingh369-svg [#156](https://github.com/hashicorp/python-tfe/pull/156)
* Fixed task stage relationship mapping in the task result resource by @TanyaSingh369-svg [#156](https://github.com/hashicorp/python-tfe/pull/156)
* Updated variable set models to support **global_** inputs. Since **global** is a Python reserved word, callers previously had to use **model_validate** as a workaround; existing **global** alias usage continues to work unchanged.
* Fixed the workspace JSON:API parser to populate the singular agent_pool field instead of writing to a non-existent agent_pools key. The relationship was previously parsed off the wire but silently dropped because the model field is singular; workspace.agent_pool now returns the related AgentPool stub as documented.


# v0.1.5

* `pytfe.__version__` added in src/pytfe/init.py via importlib.metadata.version("pytfe"). This will resolve to the version from pyproject.toml.
* Updated comments, sshkey, stateversion and cost-estimate models to have id as mandatory attribute by @isivaselvan [#137](https://github.com/hashicorp/python-tfe/pull/137)
* Updated workspace resource to include additional relationship models include AgentPool, Configuration-version, Run, Variables and State-version by @isivaselvan [#138](https://github.com/hashicorp/python-tfe/pull/138)

## Bug Fixes
* Run.read / Run.create fail with pydantic ValidationError when response has a `cost-estimate` and  `comments` relationship.

# v0.1.4

## Enhancements
* Standardize Notification Configuration option models on Pydantic [#132](https://github.com/hashicorp/python-tfe/pull/132)

# v0.1.3

## Enhancements

### Iterator Pattern Migration
* Migrated Run resource list operations to iterator pattern by @NimishaShrivastava-dev [#91](https://github.com/hashicorp/python-tfe/pull/91)
* Migrated Policy resource list operations to iterator pattern by @TanyaSingh369-svg [#92](https://github.com/hashicorp/python-tfe/pull/92)
* Migrated Policy Set resource list operations to iterator pattern by @TanyaSingh369-svg [#95](https://github.com/hashicorp/python-tfe/pull/95)
* Migrated Run Event resource list operations to iterator pattern by @NimishaShrivastava-dev [#97](https://github.com/hashicorp/python-tfe/pull/97)
* Migrated SSH Keys resource list operations to iterator pattern by @NimishaShrivastava-dev [#101](https://github.com/hashicorp/python-tfe/pull/101)
* Migrated Notification Configuration resource list operations to iterator pattern by @TanyaSingh369-svg [#109](https://github.com/hashicorp/python-tfe/pull/109)
* Migrated Variable Set list operations to iterator pattern by @isivaselvan [#113](https://github.com/hashicorp/python-tfe/pull/113)
* Migrated Variable Set Variables list operations to iterator pattern by @isivaselvan [#113](https://github.com/hashicorp/python-tfe/pull/113)
* Migrated State Version list operations to iterator pattern by @isivaselvan [#113](https://github.com/hashicorp/python-tfe/pull/113)
* Migrated State Version Output list operations to iterator pattern by @isivaselvan [#113](https://github.com/hashicorp/python-tfe/pull/113)
* Migrated Policy Check list operations to iterator pattern by @isivaselvan [#113](https://github.com/hashicorp/python-tfe/pull/113)
* Refreshed examples and unit tests to align with iterator pattern updates by @NimishaShrivastava-dev, @TanyaSingh369-svg, @isivaselvan [#91](https://github.com/hashicorp/python-tfe/pull/91) [#92](https://github.com/hashicorp/python-tfe/pull/92) [#95](https://github.com/hashicorp/python-tfe/pull/95) [#97](https://github.com/hashicorp/python-tfe/pull/97) [#101](https://github.com/hashicorp/python-tfe/pull/101) [#109](https://github.com/hashicorp/python-tfe/pull/109) [#113](https://github.com/hashicorp/python-tfe/pull/113)

### Project and Workspace Management
* Updated Project create and update models, including Project model refinements by @isivaselvan [#120](https://github.com/hashicorp/python-tfe/pull/120)
* Updated Project endpoints for list-effective-tag-bindings and delete-tag-bindings by @isivaselvan [#120](https://github.com/hashicorp/python-tfe/pull/120)
* Refactored Workspace models to improve validation with Pydantic by @isivaselvan [#106](https://github.com/hashicorp/python-tfe/pull/106)

## Breaking Change

### List Method Behavior
* Standardized list methods across multiple resources to iterator-based behavior, replacing legacy list response patterns by @NimishaShrivastava-dev, @TanyaSingh369-svg, @isivaselvan [#91](https://github.com/hashicorp/python-tfe/pull/91) [#92](https://github.com/hashicorp/python-tfe/pull/92) [#95](https://github.com/hashicorp/python-tfe/pull/95) [#97](https://github.com/hashicorp/python-tfe/pull/97) [#101](https://github.com/hashicorp/python-tfe/pull/101) [#109](https://github.com/hashicorp/python-tfe/pull/109) [#113](https://github.com/hashicorp/python-tfe/pull/113)

## Bug Fixes
* Fixed pagination parameter handling across iterator-based page traversal by @isivaselvan [#111](https://github.com/hashicorp/python-tfe/pull/111)
* Fixed state version and state version output model import/export registration by @isivaselvan [#105](https://github.com/hashicorp/python-tfe/pull/105)
* Fixed the tag based filtering of workspace in list operation by @isivaselvan [#106](https://github.com/hashicorp/python-tfe/pull/106)
* Fixed the project response of workspace relationship by @isivaselvan [#106](https://github.com/hashicorp/python-tfe/pull/106)
* Fixed configuration version examples and added terraform+cloud support for ConfigurationSource usage by @isivaselvan [#107](https://github.com/hashicorp/python-tfe/pull/107)
* Fixed configuration upload packaging flow (tarfile-based handling) by @isivaselvan [#107](https://github.com/hashicorp/python-tfe/pull/107)
* Updated agent pool workspace assign/remove operations to consistently return AgentPool objects by @KshitijaChoudhari [#110](https://github.com/hashicorp/python-tfe/pull/110)
* Updated Run relationships handling for improved model consistency by @ibm-richard [#119](https://github.com/hashicorp/python-tfe/pull/119)
* Updated additional Run Source attributes by @isivaselvan [#123](https://github.com/hashicorp/python-tfe/pull/123)

# v0.1.2

## Features

### Registry Management
* Added registry provider version resource with full CRUD operations by @isivaselvan [#66](https://github.com/hashicorp/python-tfe/pull/66)
* Added create method for registry provider versions by @isivaselvan [#66](https://github.com/hashicorp/python-tfe/pull/66)
* Added list method with pagination support for registry provider versions by @isivaselvan [#66](https://github.com/hashicorp/python-tfe/pull/66)
* Added read method for fetching specific registry provider version details by @isivaselvan [#66](https://github.com/hashicorp/python-tfe/pull/66)
* Added delete method for removing registry provider versions by @isivaselvan [#66](https://github.com/hashicorp/python-tfe/pull/66)
* Added comprehensive unit tests for registry provider versions by @isivaselvan [#66](https://github.com/hashicorp/python-tfe/pull/66)

## Breaking Change

### Iterator Pattern Migration for List Method
* Migrated Policy Evaluation resource to use iterator pattern for list operations and renamed attribute task_stage to policy_attachable at PolicyEvaluation Model by @isivaselvan [#68](https://github.com/hashicorp/python-tfe/pull/68)
* Migrated Policy Set Outcome resource to use iterator pattern for list operations by @isivaselvan [#68](https://github.com/hashicorp/python-tfe/pull/68)
* Migrated OAuth Token resource to use iterator pattern and removed deprecated Uid attribute by @isivaselvan [#68](https://github.com/hashicorp/python-tfe/pull/68)
* Migrated Reserved Tag Key resource to use iterator pattern, removed read method, and renamed service class by @isivaselvan [#68](https://github.com/hashicorp/python-tfe/pull/68)

### Deprecations
* Models OAuthTokenList, PolicyEvaluationList, PolicySetOutcomeList, ReservedTagKeyList were removed from models as part of initial Iterator pattern conversion of List Method.
* page_number attribute was removed at Models of OAuthTokenListOptions, PolicyEvaluationListOptions, PolicySetOutcomeListFilter and ReservedTagKeyListOptions.
* Removed deprecated Uid attribute at OauthToken Model.

### Enhancements
* Updated query run functions with correct api endpoints, parameters and payload options for improved performance and consistency by @aayushsingh2502 [#69](https://github.com/hashicorp/python-tfe/pull/69)
* Removed ListOptions from model and improved Cancel and Force Cancel option handling by @aayushsingh2502 [#69](https://github.com/hashicorp/python-tfe/pull/69)
* Updated function naming conventions in example files for better clarity by @aayushsingh2502 [#69](https://github.com/hashicorp/python-tfe/pull/69)

## Bug Fixes
* Fixed the issue related to the Regex pattern on string id validation for registry resource by @isivaselvan [#66](https://github.com/hashicorp/python-tfe/pull/66)

# v0.1.1

## Features

### Organization Management
* Added organization membership list functionality with flexible filtering and pagination by @aayushsingh2502 [#54](https://github.com/hashicorp/python-tfe/pull/54)
* Added organization membership read functionality by @aayushsingh2502 [#54](https://github.com/hashicorp/python-tfe/pull/54)
* Added organization membership read with relationship includes by @aayushsingh2502 [#54](https://github.com/hashicorp/python-tfe/pull/54)
* Added organization membership create functionality to invite users via email with optional team assignments by @aayushsingh2502 [#54](https://github.com/hashicorp/python-tfe/pull/54)
* Added organization membership delete functionality by @aayushsingh2502 [#54](https://github.com/hashicorp/python-tfe/pull/54)

### Workspace Management
* Added workspace resources list functionality with pagination support by @KshitijaChoudhari [#58](https://github.com/hashicorp/python-tfe/pull/58)
* Added robust data models with Pydantic validation for workspace resources by @KshitijaChoudhari [#58](https://github.com/hashicorp/python-tfe/pull/58)
* Added comprehensive filtering options for workspace resources by @KshitijaChoudhari [#58](https://github.com/hashicorp/python-tfe/pull/58)

### Policy Management
* Added policy set parameter list functionality by @isivaselvan [#53](https://github.com/hashicorp/python-tfe/pull/53)
* Added policy set parameter create functionality by @isivaselvan [#53](https://github.com/hashicorp/python-tfe/pull/53)
* Added policy set parameter read functionality by @isivaselvan [#53](https://github.com/hashicorp/python-tfe/pull/53)
* Added policy set parameter update functionality by @isivaselvan [#53](https://github.com/hashicorp/python-tfe/pull/53)
* Added policy set parameter delete functionality by @isivaselvan [#53](https://github.com/hashicorp/python-tfe/pull/53)

## Enhancements
* Code cleanup and improvements across example files by @aayushsingh2502 [#54](https://github.com/hashicorp/python-tfe/pull/54)

# v0.1.0

## Features

### Core Infrastructure & Foundation
* Established base client architecture, HTTP transport layer, pagination and response handling with retries by @iam404 [#9](https://github.com/hashicorp/python-tfe/pull/9)
* Implemented configuration management and authentication patterns by @iam404 [#9](https://github.com/hashicorp/python-tfe/pull/9)
* Added comprehensive error handling and logging infrastructure by @iam404 [#9](https://github.com/hashicorp/python-tfe/pull/9)

### Organization Management
* Added full CRUD operations for organizations by @aayushsingh2502
* Added organization membership and user management by @aayushsingh2502
* Added organization settings and feature toggles by @aayushsingh2502

### Workspace Management
* Added comprehensive workspace lifecycle management by @isivaselvan [#16](https://github.com/hashicorp/python-tfe/pull/16)
* Added VCS integration support for GitHub, GitLab, Bitbucket, Azure DevOps by @isivaselvan [#16](https://github.com/hashicorp/python-tfe/pull/16)
* Added workspace settings, tags, and remote state consumers by @isivaselvan [#16](https://github.com/hashicorp/python-tfe/pull/16)
* Added workspace variable management functionality by @aayushsingh2502 [#16](https://github.com/hashicorp/python-tfe/pull/16)
* Added variable sets integration by @aayushsingh2502 [#16](https://github.com/hashicorp/python-tfe/pull/16)
* Added sensitive variable handling with encryption by @aayushsingh2502 [#16](https://github.com/hashicorp/python-tfe/pull/16)

### Project Management
* Added project creation, configuration, and management by @KshitijaChoudhari [#23](https://github.com/hashicorp/python-tfe/pull/23)
* Added project tagging and organization by @KshitijaChoudhari [#25](https://github.com/hashicorp/python-tfe/pull/25)
* Added tag binding functionality for improved project organization by @KshitijaChoudhari [#25](https://github.com/hashicorp/python-tfe/pull/25)

### State Management
* Added state version listing, downloading, and rollback capabilities by @iam404 [#22](https://github.com/hashicorp/python-tfe/pull/22)
* Added state output retrieval and management by @iam404 [#22](https://github.com/hashicorp/python-tfe/pull/22)
* Added secure state file operations with locking mechanisms by @iam404 [#22](https://github.com/hashicorp/python-tfe/pull/22)

### Variable Sets
* Added variable set creation and management by @KshitijaChoudhari [#27](https://github.com/hashicorp/python-tfe/pull/27)
* Added workspace association and inheritance by @KshitijaChoudhari [#27](https://github.com/hashicorp/python-tfe/pull/27)
* Added global and workspace-specific variable sets by @KshitijaChoudhari [#27](https://github.com/hashicorp/python-tfe/pull/27)

### Registry Management
* Added private module registry implementation by @aayushsingh2502 [#24](https://github.com/hashicorp/python-tfe/pull/24)
* Added module publishing and version management by @aayushsingh2502 [#24](https://github.com/hashicorp/python-tfe/pull/24)
* Added VCS integration for automated module updates by @aayushsingh2502 [#24](https://github.com/hashicorp/python-tfe/pull/24)
* Added dependency management and semantic versioning by @aayushsingh2502 [#24](https://github.com/hashicorp/python-tfe/pull/24)
* Added custom and community provider management by @aayushsingh2502 [#28](https://github.com/hashicorp/python-tfe/pull/28)
* Added provider version publishing and distribution by @aayushsingh2502 [#28](https://github.com/hashicorp/python-tfe/pull/28)
* Added GPG signature verification support by @aayushsingh2502 [#28](https://github.com/hashicorp/python-tfe/pull/28)

### Run Management
* Added run creation, execution, and monitoring by @isivaselvan [#30](https://github.com/hashicorp/python-tfe/pull/30)
* Added run status tracking with real-time updates by @isivaselvan [#30](https://github.com/hashicorp/python-tfe/pull/30)
* Added run cancellation and force-cancellation capabilities by @isivaselvan [#30](https://github.com/hashicorp/python-tfe/pull/30)
* Added detailed plan analysis and review by @isivaselvan [#33](https://github.com/hashicorp/python-tfe/pull/33)
* Added apply operations with confirmation workflows by @isivaselvan [#33](https://github.com/hashicorp/python-tfe/pull/33)
* Added plan output parsing and visualization by @isivaselvan [#33](https://github.com/hashicorp/python-tfe/pull/33)
* Added run task creation and execution by @isivaselvan [#26](https://github.com/hashicorp/python-tfe/pull/26)
* Added trigger-based automated runs by @isivaselvan [#26](https://github.com/hashicorp/python-tfe/pull/26)
* Added webhook integration for external triggers by @isivaselvan [#26](https://github.com/hashicorp/python-tfe/pull/26)
* Added comprehensive run event logging by @isivaselvan [#36](https://github.com/hashicorp/python-tfe/pull/36)
* Added event filtering and querying capabilities by @isivaselvan [#36](https://github.com/hashicorp/python-tfe/pull/36)
* Added real-time event streaming support by @isivaselvan [#36](https://github.com/hashicorp/python-tfe/pull/36)

### Configuration Management
* Added configuration version creation and upload by @aayushsingh2502 [#32](https://github.com/hashicorp/python-tfe/pull/32)
* Added tar.gz archive support for configuration bundles by @aayushsingh2502 [#32](https://github.com/hashicorp/python-tfe/pull/32)
* Added VCS-triggered configuration updates by @aayushsingh2502 [#32](https://github.com/hashicorp/python-tfe/pull/32)

### Query and Search
* Added complex run filtering and search by @KshitijaChoudhari [#35](https://github.com/hashicorp/python-tfe/pull/35)
* Added historical run data analysis by @KshitijaChoudhari [#35](https://github.com/hashicorp/python-tfe/pull/35)
* Added performance metrics and statistics by @KshitijaChoudhari [#35](https://github.com/hashicorp/python-tfe/pull/35)

### Agent Management
* Added agent pool creation and configuration by @KshitijaChoudhari [#31](https://github.com/hashicorp/python-tfe/pull/31)
* Added agent registration and lifecycle management by @KshitijaChoudhari [#31](https://github.com/hashicorp/python-tfe/pull/31)
* Added health monitoring and capacity management by @KshitijaChoudhari [#31](https://github.com/hashicorp/python-tfe/pull/31)

### Authentication & Security
* Added OAuth client creation and configuration by @aayushsingh2502 [#37](https://github.com/hashicorp/python-tfe/pull/37)
* Added VCS provider authentication setup by @aayushsingh2502 [#37](https://github.com/hashicorp/python-tfe/pull/37)
* Added OAuth token refresh and management by @aayushsingh2502 [#37](https://github.com/hashicorp/python-tfe/pull/37)
* Added OAuth token creation and renewal by @aayushsingh2502 [#40](https://github.com/hashicorp/python-tfe/pull/40)
* Added secure token storage and retrieval by @aayushsingh2502 [#40](https://github.com/hashicorp/python-tfe/pull/40)
* Added token scope and permission management by @aayushsingh2502 [#40](https://github.com/hashicorp/python-tfe/pull/40)
* Added SSH key upload and management by @KshitijaChoudhari [#38](https://github.com/hashicorp/python-tfe/pull/38)
* Added key validation and security checks by @KshitijaChoudhari [#38](https://github.com/hashicorp/python-tfe/pull/38)
* Added repository access configuration by @KshitijaChoudhari [#38](https://github.com/hashicorp/python-tfe/pull/38)

### Tagging & Organization
* Added reserved tag key creation and enforcement by @KshitijaChoudhari [#39](https://github.com/hashicorp/python-tfe/pull/39)
* Added tag validation and naming conventions by @KshitijaChoudhari [#39](https://github.com/hashicorp/python-tfe/pull/39)
* Added organizational tag policies by @KshitijaChoudhari [#39](https://github.com/hashicorp/python-tfe/pull/39)

### Policy Management
* Added Sentinel policy creation and enforcement by @isivaselvan [#41](https://github.com/hashicorp/python-tfe/pull/41)
* Added policy version management by @isivaselvan [#41](https://github.com/hashicorp/python-tfe/pull/41)
* Added policy evaluation and reporting by @isivaselvan [#41](https://github.com/hashicorp/python-tfe/pull/41)
* Added policy check execution and results by @isivaselvan [#42](https://github.com/hashicorp/python-tfe/pull/42)
* Added override capabilities for policy failures by @isivaselvan [#42](https://github.com/hashicorp/python-tfe/pull/42)
* Added detailed policy violation reporting by @isivaselvan [#42](https://github.com/hashicorp/python-tfe/pull/42)
* Added policy set creation and configuration by @isivaselvan [#45](https://github.com/hashicorp/python-tfe/pull/45)
* Added workspace and organization policy assignment by @isivaselvan [#45](https://github.com/hashicorp/python-tfe/pull/45)
* Added policy set versioning and rollback by @isivaselvan [#45](https://github.com/hashicorp/python-tfe/pull/45)
* Added policy set version management by @isivaselvan [#46](https://github.com/hashicorp/python-tfe/pull/46)
* Added policy set outcome tracking by @isivaselvan [#46](https://github.com/hashicorp/python-tfe/pull/46)
* Added comprehensive evaluation reporting by @isivaselvan [#46](https://github.com/hashicorp/python-tfe/pull/46)

### Notification Management
* Added notification configuration and management by @KshitijaChoudhari [#43](https://github.com/hashicorp/python-tfe/pull/43)
* Added multi-channel notification support for Slack, email, and webhooks by @KshitijaChoudhari [#43](https://github.com/hashicorp/python-tfe/pull/43)
* Added event-driven notification triggers by @KshitijaChoudhari [#43](https://github.com/hashicorp/python-tfe/pull/43)
* Added custom notification templates and formatting by @KshitijaChoudhari [#43](https://github.com/hashicorp/python-tfe/pull/43)

## Notes
* Requires Python 3.10 or higher
* Compatible with HCP Terraform and Terraform Enterprise v2 and later
