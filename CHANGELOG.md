# Unreleased

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


# Released
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
