# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ServiceProviderType(str, Enum):
    """VCS service provider types."""

    AZURE_DEVOPS_SERVER = "ado_server"
    AZURE_DEVOPS_SERVICES = "ado_services"
    BITBUCKET_DATA_CENTER = "bitbucket_data_center"
    BITBUCKET_HOSTED = "bitbucket_hosted"
    BITBUCKET_SERVER = "bitbucket_server"
    BITBUCKET_SERVER_LEGACY = "bitbucket_server_legacy"
    GITHUB = "github"
    GITHUB_EE = "github_enterprise"
    GITLAB_HOSTED = "gitlab_hosted"
    GITLAB_CE = "gitlab_community_edition"
    GITLAB_EE = "gitlab_enterprise_edition"


class OAuthClientIncludeOpt(str, Enum):
    """Include options for OAuth client queries."""

    OAUTH_TOKENS = "oauth_tokens"
    PROJECTS = "projects"


class OAuthClient(BaseModel):
    """OAuth client represents a connection between an organization and a VCS provider."""

    id: str | None = None
    api_url: str | None = Field(None, alias="api-url")
    callback_url: str | None = Field(None, alias="callback-url")
    connect_path: str | None = Field(None, alias="connect-path")
    created_at: datetime | None = Field(None, alias="created-at")
    http_url: str | None = Field(None, alias="http-url")
    key: str | None = None
    rsa_public_key: str | None = Field(None, alias="rsa-public-key")
    name: str | None = None
    secret: str | None = None
    service_provider: ServiceProviderType | None = Field(None, alias="service-provider")
    service_provider_name: str | None = Field(
        None, alias="service-provider-display-name"
    )
    organization_scoped: bool | None = Field(None, alias="organization-scoped")

    # Relations
    organization: dict | None = None
    oauth_tokens: list[dict] | None = Field(None, alias="oauth-tokens")
    agent_pool: dict | None = Field(None, alias="agent-pool")
    projects: list[dict] | None = None

    model_config = ConfigDict(populate_by_name=True)


class OAuthClientList(BaseModel):
    """List of OAuth clients with pagination."""

    data: list[OAuthClient] = []
    pagination: dict | None = None


class OAuthClientListOptions(BaseModel):
    """Options for listing OAuth clients."""

    # Pagination options
    page_number: int | None = Field(None, alias="page[number]")
    page_size: int | None = Field(None, alias="page[size]")

    # Include options
    include: list[OAuthClientIncludeOpt] | None = None

    model_config = ConfigDict(populate_by_name=True)


class OAuthClientReadOptions(BaseModel):
    """Options for reading an OAuth client."""

    include: list[OAuthClientIncludeOpt] | None = None

    model_config = ConfigDict(populate_by_name=True)


class OAuthClientCreateOptions(BaseModel):
    """Options for creating an OAuth client."""

    # Display name for the OAuth Client
    name: str | None = None

    # Required: The base URL of your VCS provider's API
    api_url: str | None = Field(None, alias="api-url")

    # Required: The homepage of your VCS provider
    http_url: str | None = Field(None, alias="http-url")

    # Optional: The OAuth Client key
    key: str | None = None

    # Optional: The token string you were given by your VCS provider
    oauth_token: str | None = Field(None, alias="oauth-token-string")

    # Optional: The initial list of projects for which the oauth client should be associated with
    projects: list[dict] | None = None

    # Optional: Private key associated with this vcs provider - only available for ado_server
    private_key: str | None = Field(None, alias="private-key")

    # Optional: Secret key associated with this vcs provider - only available for ado_server
    secret: str | None = None

    # Optional: RSAPublicKey the text of the SSH public key associated with your
    # BitBucket Data Center Application Link
    rsa_public_key: str | None = Field(None, alias="rsa-public-key")

    # Required: The VCS provider being connected with
    service_provider: ServiceProviderType | None = Field(None, alias="service-provider")

    # Optional: AgentPool to associate the VCS Provider with, for PrivateVCS support
    agent_pool: dict | None = Field(None, alias="agent-pool")

    # Optional: Whether the OAuthClient is available to all workspaces in the organization
    organization_scoped: bool | None = Field(None, alias="organization-scoped")

    model_config = ConfigDict(populate_by_name=True)


class OAuthClientUpdateOptions(BaseModel):
    """Options for updating an OAuth client."""

    # Optional: A display name for the OAuth Client
    name: str | None = None

    # Optional: The OAuth Client key
    key: str | None = None

    # Optional: Secret key associated with this vcs provider - only available for ado_server
    secret: str | None = None

    # Optional: RSAPublicKey the text of the SSH public key associated with your BitBucket
    # Server Application Link
    rsa_public_key: str | None = Field(None, alias="rsa-public-key")

    # Optional: The token string you were given by your VCS provider
    oauth_token: str | None = Field(None, alias="oauth-token-string")

    # Optional: AgentPool to associate the VCS Provider with, for PrivateVCS support
    agent_pool: dict | None = Field(None, alias="agent-pool")

    # Optional: Whether the OAuthClient is available to all workspaces in the organization
    organization_scoped: bool | None = Field(None, alias="organization-scoped")

    model_config = ConfigDict(populate_by_name=True)


class OAuthClientAddProjectsOptions(BaseModel):
    """Options for adding projects to an OAuth client."""

    # The projects to add to an OAuth client
    projects: list[dict]

    model_config = ConfigDict(populate_by_name=True)


class OAuthClientRemoveProjectsOptions(BaseModel):
    """Options for removing projects from an OAuth client."""

    # The projects to remove from an OAuth client
    projects: list[dict]

    model_config = ConfigDict(populate_by_name=True)
