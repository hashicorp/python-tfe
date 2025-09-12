"""Workspace validation functions similar to Go implementation."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import VCSRepo, WorkspaceCreateOptions, WorkspaceUpdateOptions

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

# Regular expression used to validate common string ID patterns
# Matches strings that don't contain '/' or whitespace characters
STRING_ID_PATTERN = re.compile(r"^[^/\s]+$")


def is_valid_string(value: str | None) -> bool:
    """Check if a string value is valid (not None and not empty)."""
    return value is not None and value.strip() != ""


def is_valid_string_id(value: str | None) -> bool:
    """
    Check if a string is a valid ID (similar to Go's validStringID).
    Returns True if the string is non-null and contains a typical string identifier
    (no slashes or whitespace).
    """
    return value is not None and STRING_ID_PATTERN.match(value) is not None


def is_valid_workspace_name(name: str | None) -> bool:
    """
    Check if a workspace name is valid.
    Terraform Cloud workspace names must:
    - Be between 1 and 90 characters
    - Only contain letters, numbers, dashes, and underscores
    - Cannot start or end with a dash
    """
    if not is_valid_string(name):
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
    return vcs_repo is not None and is_valid_string(vcs_repo.tags_regex)


def validate_workspace_create_options(options: WorkspaceCreateOptions) -> None:
    """
    Validate workspace create options similar to Go implementation.
    Raises specific validation errors if validation fails.
    """
    # Check required name
    if not is_valid_string(options.name):
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
