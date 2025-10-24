from __future__ import annotations

import io
import re
import time
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .models.oauth_client import (
        OAuthClientAddProjectsOptions,
        OAuthClientCreateOptions,
        OAuthClientRemoveProjectsOptions,
    )

from urllib.parse import urlparse

try:
    import slug  # type: ignore[import-not-found]
except ImportError:
    slug = None

from .errors import (
    InvalidNameError,
    RequiredAgentModeError,
    RequiredAgentPoolIDError,
    RequiredNameError,
    UnsupportedBothTagsRegexAndFileTriggersEnabledError,
    UnsupportedBothTagsRegexAndTriggerPatternsError,
    UnsupportedBothTagsRegexAndTriggerPrefixesError,
    UnsupportedBothTriggerPatternsAndPrefixesError,
    UnsupportedOperationsError,
)
from .models.workspace import (
    VCSRepo,
    WorkspaceCreateOptions,
    WorkspaceUpdateOptions,
)

_STRING_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{2,}$")
_WS_ID_RE = re.compile(r"^ws-[A-Za-z0-9]+$")
_VERSION_PATTERN = re.compile(
    r"^\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*)?(?:\+[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*)?$"
)


def poll_until(
    fn: Callable[[], bool],
    *,
    interval_s: float = 5.0,
    timeout_s: float | None = 600,
) -> bool:
    start = time.time()
    while True:
        value = fn()
        if value:
            return True
        if timeout_s is not None and (time.time() - start) > timeout_s:
            raise TimeoutError("Timed out")
        time.sleep(interval_s)


def valid_string(v: str | None) -> bool:
    return v is not None and str(v).strip() != ""


def valid_string_id(v: str | None) -> bool:
    return v is not None and _STRING_ID_PATTERN.match(str(v)) is not None


def _safe_str(v: Any, default: str = "") -> str:
    return v if isinstance(v, str) else (str(v) if v is not None else default)


def looks_like_workspace_id(value: Any) -> bool:
    """True if value matches "ws-<alnum>" pattern."""
    return isinstance(value, str) and bool(_WS_ID_RE.match(value))


def encode_query(params: Mapping[str, Any] | None) -> str:
    """
    Best-effort encoder for JSON:API-style query dicts into a query string.
    Keeps keys like "page[number]" intact. Values that are lists/tuples are joined with commas.
    """
    if not params:
        return ""
    parts: list[str] = []
    for k, v in params.items():
        if v is None:
            continue
        if isinstance(v, (list | tuple)):
            sv = ",".join(str(x) for x in v)
        else:
            sv = str(v)
        parts.append(f"{k}={sv}")
    return ("?" + "&".join(parts)) if parts else ""


def valid_version(v: str | None) -> bool:
    """Validate semantic version string."""
    return v is not None and _VERSION_PATTERN.match(str(v)) is not None


def is_valid_workspace_name(name: str | None) -> bool:
    """
    Check if a workspace name is valid.
    Terraform Cloud workspace names must:
    - Be between 1 and 90 characters
    - Only contain letters, numbers, dashes, and underscores
    - Cannot start or end with a dash
    """
    if not valid_string(name):
        return False

    if not name:
        return False

    # Check length
    if len(name) < 1 or len(name) > 90:
        return False

    # Check format: alphanumeric, dashes, underscores, but not starting/ending with dash
    if not re.match(r"^[a-zA-Z0-9_][a-zA-Z0-9_-]*[a-zA-Z0-9_]$|^[a-zA-Z0-9_]$", name):
        return False

    return True


def has_tags_regex_defined(vcs_repo: VCSRepo | None) -> bool:
    """Check if VCS repo has tags regex defined."""
    return vcs_repo is not None and valid_string(vcs_repo.tags_regex)


def validate_workspace_create_options(options: WorkspaceCreateOptions) -> None:
    """
    Validate workspace create options for proper API usage.
    Raises specific validation errors if validation fails.
    """
    # Check required name
    if not valid_string(options.name):
        raise RequiredNameError()

    # Check name format
    if not is_valid_workspace_name(options.name):
        raise InvalidNameError()

    # Check operations and execution mode conflict
    if options.operations is not None and options.execution_mode is not None:
        raise UnsupportedOperationsError()

    # Check agent mode requirements
    if options.agent_pool_id is not None and (
        options.execution_mode is None or options.execution_mode != "agent"
    ):
        raise RequiredAgentModeError()

    if (
        options.agent_pool_id is None
        and options.execution_mode is not None
        and options.execution_mode == "agent"
    ):
        raise RequiredAgentPoolIDError()

    # Check trigger patterns and prefixes conflict
    if len(options.trigger_prefixes) > 0 and len(options.trigger_patterns) > 0:
        raise UnsupportedBothTriggerPatternsAndPrefixesError()

    # Check tags regex conflicts
    if has_tags_regex_defined(options.vcs_repo):
        if len(options.trigger_patterns) > 0:
            raise UnsupportedBothTagsRegexAndTriggerPatternsError()

        if len(options.trigger_prefixes) > 0:
            raise UnsupportedBothTagsRegexAndTriggerPrefixesError()

        if options.file_triggers_enabled is not None and options.file_triggers_enabled:
            raise UnsupportedBothTagsRegexAndFileTriggersEnabledError()


def validate_workspace_update_options(options: WorkspaceUpdateOptions) -> None:
    """
    Validate workspace update options for proper API usage.
    Raises specific validation errors if validation fails.
    """
    # Check name format if provided
    if options.name is not None and not is_valid_workspace_name(options.name):
        raise InvalidNameError()

    # Check operations and execution mode conflict
    if options.operations is not None and options.execution_mode is not None:
        raise UnsupportedOperationsError()

    # Check agent mode requirements
    if (
        options.agent_pool_id is None
        and options.execution_mode is not None
        and options.execution_mode == "agent"
    ):
        raise RequiredAgentPoolIDError()

    # Check trigger patterns and prefixes conflict
    if len(options.trigger_prefixes) > 0 and len(options.trigger_patterns) > 0:
        raise UnsupportedBothTriggerPatternsAndPrefixesError()

    # Check tags regex conflicts
    if has_tags_regex_defined(options.vcs_repo):
        if len(options.trigger_patterns) > 0:
            raise UnsupportedBothTagsRegexAndTriggerPatternsError()

        if len(options.trigger_prefixes) > 0:
            raise UnsupportedBothTagsRegexAndTriggerPrefixesError()

        if options.file_triggers_enabled is not None and options.file_triggers_enabled:
            raise UnsupportedBothTagsRegexAndFileTriggersEnabledError()


def validate_oauth_client_create_options(options: OAuthClientCreateOptions) -> None:
    """
    Validate OAuth client create options for proper API usage.
    Raises specific validation errors if validation fails.
    """
    from .errors import (
        ERR_REQUIRED_API_URL,
        ERR_REQUIRED_HTTP_URL,
        ERR_REQUIRED_OAUTH_TOKEN,
        ERR_REQUIRED_SERVICE_PROVIDER,
        ERR_UNSUPPORTED_PRIVATE_KEY,
    )
    from .models.oauth_client import ServiceProviderType

    if not valid_string(options.api_url):
        raise ValueError(ERR_REQUIRED_API_URL)

    if not valid_string(options.http_url):
        raise ValueError(ERR_REQUIRED_HTTP_URL)

    if options.service_provider is None:
        raise ValueError(ERR_REQUIRED_SERVICE_PROVIDER)

    # OAuth token not required for Bitbucket Server and Data Center
    if (
        not valid_string(options.oauth_token)
        and options.service_provider != ServiceProviderType.BITBUCKET_SERVER
        and options.service_provider != ServiceProviderType.BITBUCKET_DATA_CENTER
    ):
        raise ValueError(ERR_REQUIRED_OAUTH_TOKEN)

    # Private key only supported for Azure DevOps Server
    if (
        valid_string(options.private_key)
        and options.service_provider != ServiceProviderType.AZURE_DEVOPS_SERVER
    ):
        raise ValueError(ERR_UNSUPPORTED_PRIVATE_KEY)


def validate_oauth_client_add_projects_options(
    options: OAuthClientAddProjectsOptions,
) -> None:
    """
    Validate OAuth client add projects options.
    Raises specific validation errors if validation fails.
    """
    from .errors import ERR_PROJECT_MIN_LIMIT, ERR_REQUIRED_PROJECT

    if options.projects is None:
        raise ValueError(ERR_REQUIRED_PROJECT)

    if len(options.projects) == 0:
        raise ValueError(ERR_PROJECT_MIN_LIMIT)


def validate_oauth_client_remove_projects_options(
    options: OAuthClientRemoveProjectsOptions,
) -> None:
    """
    Validate OAuth client remove projects options.
    Raises specific validation errors if validation fails.
    """
    from .errors import ERR_PROJECT_MIN_LIMIT, ERR_REQUIRED_PROJECT

    if options.projects is None:
        raise ValueError(ERR_REQUIRED_PROJECT)

    if len(options.projects) == 0:
        raise ValueError(ERR_PROJECT_MIN_LIMIT)


def valid_project_name(name: str) -> bool:
    """Validate project name format"""
    if not valid_string(name):
        return False
    # Project names can contain letters, numbers, spaces, hyphens, underscores, and periods
    # Must be between 1 and 90 characters
    if len(name) > 90:
        return False
    # Allow most printable characters except some special ones
    # Based on Terraform Cloud API documentation
    pattern = re.compile(r"^[a-zA-Z0-9\s._-]+$")
    return bool(pattern.match(name))


def valid_organization_name(org_name: str) -> bool:
    """Validate organization name format"""
    if not valid_string(org_name):
        return False
    # Organization names must be valid identifiers
    return valid_string_id(org_name)


def validate_project_create_options(
    organization: str, name: str, description: str | None = None
) -> None:
    """Validate project creation parameters"""
    if not valid_organization_name(organization):
        raise ValueError("Organization name is required and must be valid")

    if not valid_string(name):
        raise ValueError("Project name is required")

    if not valid_project_name(name):
        raise ValueError("Project name contains invalid characters or is too long")

    if description is not None and not valid_string(description):
        raise ValueError("Description must be a valid string")


def validate_project_update_options(
    project_id: str, name: str | None = None, description: str | None = None
) -> None:
    """Validate project update parameters"""
    if not valid_string_id(project_id):
        raise ValueError("Project ID is required")

    if name is not None:
        if not valid_string(name):
            raise ValueError("Project name cannot be empty")
        if not valid_project_name(name):
            raise ValueError("Project name contains invalid characters or is too long")

    if description is not None and not valid_string(description):
        raise ValueError("Description must be a valid string")


def validate_project_list_options(
    organization: str, query: str | None = None, name: str | None = None
) -> None:
    """Validate project list options."""
    if not valid_organization_name(organization):
        raise ValueError("Organization name is required and must be valid")

    if query and not valid_string(query):
        raise ValueError("Query must be a valid string")

    if name and not valid_project_name(name):
        raise ValueError("Project name must be valid")


def pack_contents(path: str) -> io.BytesIO:
    """
    Pack directory contents into a tar.gz archive suitable for upload.

    Args:
        path: Path to the directory to pack

    Returns:
        BytesIO buffer containing the tar.gz archive

    Raises:
        ImportError: If go-slug is not available
        ValueError: If path is invalid
    """
    if slug is None:
        raise ImportError(
            "go-slug package is required for packing configuration files. "
            "Install it with: pip install go-slug"
        )

    body = io.BytesIO()

    # Use go-slug to pack the configuration directory
    # This handles .terraformignore and other Terraform-specific behaviors
    packer = slug.Packer()
    _, err = packer.pack(path, body)

    if err:
        raise ValueError(f"Failed to pack directory {path}: {err}")

    # Reset buffer position to beginning for reading
    body.seek(0)
    return body


def validate_log_url(log_url: str) -> None:
    """Validate a log URL for Terraform resources."""
    try:
        parsed_url = urlparse(log_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid log URL format: {log_url}")
    except Exception as e:
        raise ValueError(f"Invalid log URL: {log_url}") from e
