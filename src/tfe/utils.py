from __future__ import annotations

import re
import time
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import urlparse

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
from .types import (
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
    Validate workspace create options similar to Go implementation.
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
    Validate workspace update options similar to Go implementation.
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


def validate_log_url(log_url: str) -> None:
    """Validate a log URL for Terraform resources."""
    try:
        parsed_url = urlparse(log_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid log URL format: {log_url}")
    except Exception as e:
        raise ValueError(f"Invalid log URL: {log_url}") from e
