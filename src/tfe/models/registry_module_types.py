from __future__ import annotations

import importlib.util
import os
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# Load the main types.py file to get Organization and other main types
# Path: from /src/tfe/types/registry_module_types.py to /src/tfe/types.py
types_py_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "types.py")
spec = importlib.util.spec_from_file_location("main_types", types_py_path)
if spec is not None and spec.loader is not None:
    main_types = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_types)
else:
    raise ImportError("Could not load main types module")


class RegistryName(str, Enum):
    """Registry name enum for public/private registries."""

    PRIVATE = "private"
    PUBLIC = "public"


class RegistryModuleStatus(str, Enum):
    """Registry module status enum."""

    PENDING = "pending"
    NO_VERSION_TAGS = "no_version_tags"
    SETUP_FAILED = "setup_failed"
    SETUP_COMPLETE = "setup_complete"


class RegistryModuleVersionStatus(str, Enum):
    """Registry module version status enum."""

    PENDING = "pending"
    CLONING = "cloning"
    CLONE_FAILED = "clone_failed"
    REG_INGRESS_REQ_FAILED = "reg_ingress_req_failed"
    REG_INGRESSING = "reg_ingressing"
    REG_INGRESS_FAILED = "reg_ingress_failed"
    OK = "ok"


class PublishingMechanism(str, Enum):
    """Publishing mechanism enum."""

    BRANCH = "branch"
    TAG = "git_tag"
    NON_VCS = "non_vcs"


class AgentExecutionMode(str, Enum):
    """Agent execution mode enum."""

    AGENT = "agent"
    REMOTE = "remote"


class RegistryModuleListIncludeOpt(str, Enum):
    """Registry module list include options."""

    NO_CODE_MODULES = "no-code-modules"


# Data Models
class RegistryModuleID(BaseModel):
    """Registry module identifier."""

    id: str | None = None
    organization: str | None = None
    name: str | None = None
    provider: str | None = None
    namespace: str | None = None
    registry_name: RegistryName | None = None


class RegistryModulePermissions(BaseModel):
    """Registry module permissions."""

    can_delete: bool
    can_resync: bool
    can_retry: bool


class RegistryModuleVCSRepo(BaseModel):
    """VCS repository configuration for registry modules."""

    branch: str | None = None
    display_identifier: str | None = None
    identifier: str | None = None
    ingress_submodules: bool | None = None
    oauth_token_id: str | None = None
    repository_http_url: str | None = None
    service_provider: str | None = None
    webhook_url: str | None = None
    tags: bool | None = None
    source_directory: str | None = None
    tag_prefix: str | None = None
    organization_name: str | None = None


class TestConfig(BaseModel):
    """Test configuration for registry modules."""

    tests_enabled: bool | None = None
    agent_execution_mode: AgentExecutionMode | None = None
    agent_pool_id: str | None = None


class RegistryModuleVersionStatuses(BaseModel):
    """Registry module version status."""

    version: str
    status: RegistryModuleVersionStatus
    error: str | None = None


class RegistryModule(BaseModel):
    """Registry module model."""

    id: str
    name: str
    provider: str
    registry_name: RegistryName
    namespace: str
    no_code: bool = False
    permissions: RegistryModulePermissions | None = None
    publishing_mechanism: PublishingMechanism | None = None
    status: RegistryModuleStatus | None = None
    test_config: TestConfig | None = None
    vcs_repo: RegistryModuleVCSRepo | None = None
    version_statuses: list[RegistryModuleVersionStatuses] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    organization: Any | None = None  # Will be Organization type from main types


class RegistryModuleVersion(BaseModel):
    """Registry module version model."""

    id: str
    source: str | None = None
    status: RegistryModuleVersionStatus | None = None
    version: str
    created_at: str | None = None
    updated_at: str | None = None
    registry_module: RegistryModule | None = None
    links: dict[str, Any] = Field(default_factory=dict)


class Commit(BaseModel):
    """Commit model."""

    id: str
    sha: str
    date: str
    url: str | None = None
    author: str | None = None
    author_avatar_url: str | None = None
    author_html_url: str | None = None
    message: str | None = None


class CommitList(BaseModel):
    """Commit list model."""

    items: list[Commit] = Field(default_factory=list)


class RegistryModuleList(BaseModel):
    """Registry module list model."""

    items: list[RegistryModule] = Field(default_factory=list)


# Terraform Registry Module Models
class Input(BaseModel):
    """Terraform input variable."""

    name: str
    type: str
    description: str | None = None
    default: str | None = None
    required: bool = False


class Output(BaseModel):
    """Terraform output."""

    name: str
    description: str | None = None


class ProviderDependency(BaseModel):
    """Provider dependency."""

    name: str
    namespace: str
    source: str
    version: str


class Resource(BaseModel):
    """Terraform resource."""

    name: str
    type: str


class Root(BaseModel):
    """Root module configuration."""

    path: str | None = None
    name: str
    readme: str | None = None
    empty: bool = False
    inputs: list[Input] = Field(default_factory=list)
    outputs: list[Output] = Field(default_factory=list)
    provider_dependencies: list[ProviderDependency] = Field(default_factory=list)
    resources: list[Resource] = Field(default_factory=list)


class TerraformRegistryModule(BaseModel):
    """Terraform registry module from public/private registry."""

    id: str
    owner: str | None = None
    namespace: str
    name: str
    version: str
    provider: str
    provider_logo_url: str | None = None
    description: str | None = None
    source: str | None = None
    tag: str | None = None
    published_at: str | None = None
    downloads: int = 0
    verified: bool = False
    root: Root | None = None
    providers: list[str] = Field(default_factory=list)
    versions: list[str] = Field(default_factory=list)


# Options Models
class RegistryModuleListOptions(BaseModel):
    """Options for listing registry modules."""

    include: list[RegistryModuleListIncludeOpt] = Field(default_factory=list)
    search: str | None = None
    provider: str | None = None
    registry_name: RegistryName | None = None
    organization_name: str | None = None
    page_number: int | None = None
    page_size: int | None = None


class RegistryModuleCreateOptions(BaseModel):
    """Options for creating a registry module."""

    name: str
    provider: str
    registry_name: RegistryName | None = RegistryName.PRIVATE
    namespace: str | None = None
    no_code: bool | None = None


class RegistryModuleCreateVersionOptions(BaseModel):
    """Options for creating a registry module version."""

    version: str
    commit_sha: str | None = None


class RegistryModuleVCSRepoOptions(BaseModel):
    """VCS repository options for registry modules."""

    # Required fields
    identifier: str = Field(description="VCS repository identifier")
    display_identifier: str = Field(
        alias="display-identifier", description="Display identifier"
    )

    # Optional fields
    oauth_token_id: str | None = Field(alias="oauth-token-id", default=None)
    github_app_installation_id: str | None = Field(
        alias="github-app-installation-id", default=None
    )
    organization_name: str | None = Field(alias="organization-name", default=None)
    branch: str | None = Field(
        default=None, description="Branch for branch-based modules"
    )
    tags: bool | None = Field(default=None, description="Enable tag-based publishing")
    source_directory: str | None = Field(alias="source-directory", default=None)
    tag_prefix: str | None = Field(alias="tag-prefix", default=None)

    model_config = ConfigDict(populate_by_name=True)


class RegistryModuleVCSRepoUpdateOptions(BaseModel):
    """VCS repository update options for registry modules."""

    branch: str | None = None
    tags: bool | None = None
    source_directory: str | None = None
    tag_prefix: str | None = None


class RegistryModuleCreateWithVCSConnectionOptions(BaseModel):
    """Options for creating a registry module with VCS connection."""

    # Required: VCS repository information
    vcs_repo: RegistryModuleVCSRepoOptions = Field(alias="vcs-repo")

    # Optional: Initial version for branch-based modules. Defaults to "0.0.0".
    initial_version: str | None = Field(alias="initial-version", default=None)

    # Optional: Test configuration
    test_config: TestConfig | None = Field(alias="test-config", default=None)

    # Additional fields that might be needed for the API
    name: str | None = Field(
        default=None, description="Module name (derived from repo if not provided)"
    )
    provider: str | None = Field(default=None, description="Provider name")
    registry_name: RegistryName | None = Field(alias="registry-name", default=None)
    namespace: str | None = Field(
        default=None, description="Namespace for public modules"
    )

    model_config = ConfigDict(populate_by_name=True)


class RegistryModuleUpdateOptions(BaseModel):
    """Options for updating a registry module."""

    vcs_repo: RegistryModuleVCSRepoUpdateOptions | None = None
    no_code: bool | None = None
