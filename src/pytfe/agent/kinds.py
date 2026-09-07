# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Classify SDK methods by what they do to the world.

An agent harness needs to know, before calling a method, whether it reads,
writes, or destroys. That decision cannot come from the docstring: no method in
the SDK carries a machine-readable marker, and ``describe()`` keeps only the
first docstring line anyway. So classification is a verb-prefix table plus an
explicit override map, and the override map wins.

The default for an unrecognised verb is :data:`Kind.WRITE`, never ``READ`` -
guessing "safe" for something that mutates is the one failure mode that matters.
``tests/units/agent/test_kinds.py`` asserts that no method falls through
unclassified, so a new SDK method fails CI rather than silently defaulting.
"""

from __future__ import annotations

from enum import Enum

__all__ = ["Kind", "classify", "OVERRIDES", "PREFIXES"]


class Kind(str, Enum):
    """What calling a method does."""

    READ = "read"
    """No server state changes."""

    WRITE = "write"
    """Creates or modifies state; recoverable."""

    DESTRUCTIVE = "destructive"
    """Deletes, applies, overrides, cancels or revokes. Gate these."""

    LOCAL = "local"
    """Pure local computation - no HTTP request at all."""


#: Verb prefixes, longest match first. Order within a Kind does not matter.
PREFIXES: dict[Kind, tuple[str, ...]] = {
    Kind.DESTRUCTIVE: (
        "delete",
        "destroy",
        "force_",
        "discard",
        "apply",
        "override",
        "cancel",
        "purge",
        "revoke",
        "rotate",
        "safe_delete",
        "permanently_delete",
        "soft_delete",
        "archive",
        "suspend",
        "rollback",
        # Approving or confirming is what actually triggers an apply.
        "approve",
        "confirm",
    ),
    Kind.WRITE: (
        "create",
        "update",
        "add",
        "upload",
        "lock",
        "unlock",
        "assign",
        "attach",
        "apply_to",
        "move",
        "rename",
        "set_",
        "enable",
        "disable",
        "grant",
        "generate",
        "queue",
        "publish",
        "send",
        "backfill",
        # Relationship changes and reversible operations. Removing a tag or
        # detaching a variable set mutates scope; it destroys nothing.
        "remove",
        "detach",
        "unassign",
        "verify",
        "test",
        "reset",
        "advance",
        "acknowledge",
        "upgrade",
        "rerun",
        "fetch_",
        "callback",
        "restore",
        "unsuspend",
    ),
    Kind.READ: (
        "list",
        "read",
        "get",
        "download",
        "logs",
        "log_",
        "current",
        "search",
        "describe",
        "show",
        "json_",
        "outputs",
        "readme",
        "count",
        "exists",
        "query",
        "export",
        "ingress",
        "latest",
        "errored_state",
        "saved_view",
    ),
}

#: Explicit classifications that the prefix table gets wrong or cannot reach.
#:
#: Seeded from a sweep over every public method on a live client. Two categories
#: matter: verbs a prefix table demotes (``runs.apply`` is the single most
#: destructive call in the SDK but starts with a WRITE-looking verb), and pure
#: local helpers a read-only gate would otherwise block for no reason.
OVERRIDES: dict[tuple[str, str], Kind] = {
    # Applying a run changes real infrastructure.
    ("runs", "apply"): Kind.DESTRUCTIVE,
    # Creating a state version overwrites a workspace's state.
    ("state_versions", "create"): Kind.DESTRUCTIVE,
    ("state_versions", "upload"): Kind.DESTRUCTIVE,
    # Locking is reversible and destroys nothing.
    ("workspaces", "lock"): Kind.WRITE,
    ("workspaces", "unlock"): Kind.WRITE,
    ("workspaces", "force_unlock"): Kind.WRITE,
    # Variable sets are applied to, and removed from, scopes - not destroyed.
    ("variable_sets", "apply_to_workspaces"): Kind.WRITE,
    ("variable_sets", "apply_to_projects"): Kind.WRITE,
    ("variable_sets", "remove_from_workspaces"): Kind.WRITE,
    ("variable_sets", "remove_from_projects"): Kind.WRITE,
    # The Stacks operator gate. `advance` releases a step sitting in
    # `pending-operator` and `rerun` re-executes a deployment group; both cause
    # infrastructure to be applied, exactly like runs.apply. A verb-prefix table
    # reads them as ordinary writes, which would wave the approval straight
    # through a Kind-based gate.
    ("stack_deployment_steps", "advance"): Kind.DESTRUCTIVE,
    ("stack_deployment_groups", "rerun"): Kind.DESTRUCTIVE,
    # Pure local computation: no request is issued.
    ("organizations", "validate"): Kind.LOCAL,
    ("run_triggers", "validate_run_trigger_filter_param"): Kind.LOCAL,
    ("run_triggers", "backfill_deprecated_sourceable"): Kind.LOCAL,
    ("policy_set_outcomes", "build_query_string"): Kind.LOCAL,
}


def classify(resource: str, method: str) -> Kind:
    """Return what calling ``resource.method`` does.

    Resolution order: an explicit :data:`OVERRIDES` entry, then the longest
    matching verb prefix, then :data:`Kind.WRITE` as a fail-safe default.

    Args:
        resource: Namespace name, e.g. ``"workspaces"``. Nested admin
            namespaces use dotted form, e.g. ``"admin.users"``.
        method: Public method name.

    Returns:
        The method's :class:`Kind`.

    Example:
        >>> classify("runs", "apply")
        <Kind.DESTRUCTIVE: 'destructive'>
        >>> classify("workspaces", "list")
        <Kind.READ: 'read'>
    """
    override = OVERRIDES.get((resource, method))
    if override is not None:
        return override

    best: tuple[int, Kind] | None = None
    for kind, prefixes in PREFIXES.items():
        for prefix in prefixes:
            if method.startswith(prefix) and (best is None or len(prefix) > best[0]):
                best = (len(prefix), kind)
    if best is not None:
        return best[1]
    return Kind.WRITE
