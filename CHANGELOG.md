# Unreleased

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
