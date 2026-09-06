# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Workspace-shaped workflows: find, inspect, converge."""

from __future__ import annotations

import fnmatch
import logging
from datetime import datetime
from typing import Any, Literal

from ..client import TFEClient
from ..errors import NotFound, TFEError
from ..models.common import Tag
from ..models.project import Project
from ..models.variable import (
    Variable,
    VariableCreateOptions,
    VariableUpdateOptions,
)
from ..models.workspace import (
    VCSRepo,
    Workspace,
    WorkspaceAddTagsOptions,
    WorkspaceCreateOptions,
    WorkspaceListOptions,
    WorkspaceRemoveTagsOptions,
    WorkspaceUpdateOptions,
)
from ._resolve import resolve_workspace
from ._result import Change, EnsureResult
from .models import (
    EnsureVariablesResult,
    VariableSpec,
    WorkspaceList,
    WorkspaceSpec,
    WorkspaceStatus,
    WorkspaceSummary,
)

logger = logging.getLogger("pytfe.workflows")

__all__ = [
    "find_workspaces",
    "workspace_status",
    "ensure_workspace",
    "ensure_variables",
]

#: WorkspaceSpec fields that map 1:1 onto the options models by name.
_DIRECT_FIELDS = (
    "description",
    "execution_mode",
    "agent_pool_id",
    "terraform_version",
    "working_directory",
    "auto_apply",
    "queue_all_runs",
    "speculative_enabled",
    "file_triggers_enabled",
    "trigger_prefixes",
    "trigger_patterns",
    "allow_destroy_plan",
    "assessments_enabled",
    "global_remote_state",
)

#: Present on WorkspaceCreateOptions only; silently dropped on update.
_CREATE_ONLY_FIELDS = ("source_name", "source_url")


def _summarize(workspace: Workspace) -> WorkspaceSummary:
    project = getattr(workspace, "project", None)
    vcs = getattr(workspace, "vcs_repo", None)
    return WorkspaceSummary(
        id=workspace.id or "",
        name=workspace.name or "",
        project_id=getattr(project, "id", None),
        terraform_version=workspace.terraform_version,
        execution_mode=getattr(
            workspace.execution_mode, "value", workspace.execution_mode
        ),
        locked=bool(workspace.locked),
        resource_count=workspace.resource_count,
        updated_at=workspace.updated_at,
        tags=list(workspace.tag_names or []),
        vcs_repo_identifier=getattr(vcs, "identifier", None),
    )


def find_workspaces(
    client: TFEClient,
    organization: str,
    *,
    name_pattern: str | None = None,
    tags: list[str] | None = None,
    exclude_tags: list[str] | None = None,
    project_id: str | None = None,
    terraform_version: str | None = None,
    execution_mode: str | None = None,
    limit: int = 200,
) -> WorkspaceList:
    """Find workspaces in an organization by name, tag, project or settings.

    Filters the API supports (``search``, ``tags``, ``exclude_tags``,
    ``project_id``, ``wildcard_name``) are pushed server-side.
    ``terraform_version`` and ``execution_mode`` have no server-side filter and
    are applied locally.

    Args:
        client: The client to read through.
        organization: Organization to search.
        name_pattern: Glob such as ``"prod-*"``.
        tags: Only workspaces carrying all of these tags.
        exclude_tags: Skip workspaces carrying any of these tags.
        project_id: Restrict to one project.
        terraform_version: Exact version match, applied locally.
        execution_mode: Exact mode match, applied locally.
        limit: Stop after this many matches.

    Returns:
        A :class:`~pytfe.workflows.models.WorkspaceList`; ``truncated`` is True
        when more matches existed.

    Raises:
        TFEError: If the organization cannot be listed.

    Example:
        >>> found = find_workspaces(client, "acme", name_pattern="prod-*")
        >>> [w.name for w in found.items]
        ['prod-api', 'prod-web']
    """
    options = WorkspaceListOptions(
        tags=",".join(tags) if tags else None,
        exclude_tags=",".join(exclude_tags) if exclude_tags else None,
        project_id=project_id,
        wildcard_name=name_pattern if name_pattern and "*" in name_pattern else None,
    )

    result = WorkspaceList()
    for workspace in client.workspaces.list(organization, options):
        if name_pattern and not fnmatch.fnmatch(workspace.name or "", name_pattern):
            continue
        if terraform_version and workspace.terraform_version != terraform_version:
            continue
        if execution_mode:
            mode = getattr(workspace.execution_mode, "value", workspace.execution_mode)
            if mode != execution_mode:
                continue
        if len(result.items) >= limit:
            result.truncated = True
            break
        result.items.append(_summarize(workspace))
    return result


def workspace_status(
    client: TFEClient,
    workspace_id: str | None = None,
    *,
    organization: str | None = None,
    workspace_name: str | None = None,
) -> WorkspaceStatus:
    """Report a workspace's current health in one call.

    Collapses the workspace, its latest run, and its current state version into
    a single ``health`` verdict an agent can branch on.

    Args:
        client: The client to read through.
        workspace_id: Target workspace, by ID.
        organization: Organization name, with ``workspace_name``.
        workspace_name: Workspace name, with ``organization``.

    Returns:
        A :class:`~pytfe.workflows.models.WorkspaceStatus`.

    Raises:
        WorkspaceNotFound: If the workspace cannot be resolved.

    Example:
        >>> status = workspace_status(client, organization="acme", workspace_name="web")
        >>> status.health
        'ok'
    """
    workspace = resolve_workspace(
        client, workspace_id, organization=organization, workspace_name=workspace_name
    )
    ws_id = workspace.id or ""
    vcs = getattr(workspace, "vcs_repo", None)
    locked_by = getattr(workspace, "locked_by", None)

    status = WorkspaceStatus(
        id=ws_id,
        name=workspace.name or "",
        terraform_version=workspace.terraform_version,
        execution_mode=getattr(
            workspace.execution_mode, "value", workspace.execution_mode
        ),
        locked=bool(workspace.locked),
        locked_by=getattr(locked_by, "id", None) if locked_by else None,
        resource_count=workspace.resource_count,
        vcs_repo=getattr(vcs, "identifier", None),
        auto_apply=workspace.auto_apply,
    )

    from ..models.run import RunListOptions

    # page_size defaults to 20 on this model, not None, so it is set explicitly.
    runs = list(client.runs.list(ws_id, RunListOptions(page_size=1)))
    if runs:
        latest = runs[0]
        status.latest_run = {
            "id": latest.id,
            "status": getattr(latest.status, "value", latest.status),
            "created_at": (
                latest.created_at.isoformat() if latest.created_at else None
            ),
            "message": latest.message,
        }

    try:
        state_version = client.state_versions.read_current(ws_id)
        status.current_state_version = {
            "id": state_version.id,
            "serial": getattr(state_version, "serial", None),
            "created_at": (
                created.isoformat()
                if isinstance(
                    created := getattr(state_version, "created_at", None), datetime
                )
                else None
            ),
        }
    except TFEError:
        logger.debug("workspace %s has no current state version", ws_id)

    try:
        assessment = client.workspaces.read_by_id(ws_id)
        drifted = getattr(assessment, "drifted", None)
        if drifted is not None:
            status.drift = {"detected": bool(drifted), "checked_at": None}
    except TFEError:
        pass

    latest_status = (status.latest_run or {}).get("status")
    if status.locked:
        status.health = "locked"
    elif latest_status in ("errored", "canceled"):
        status.health = "errored"
    elif status.drift and status.drift.get("detected"):
        status.health = "drifted"
    elif not runs:
        status.health = "never_run"
    else:
        status.health = "ok"
    return status


def _vcs_repo_of(spec: WorkspaceSpec) -> VCSRepo | None:
    if spec.vcs_repo is None:
        return None
    repo = spec.vcs_repo
    if bool(repo.oauth_token_id) == bool(repo.github_app_installation_id):
        raise ValueError(
            "vcs_repo requires exactly one of oauth_token_id or "
            "github_app_installation_id"
        )
    return VCSRepo(
        identifier=repo.identifier,
        branch=repo.branch,
        oauth_token_id=repo.oauth_token_id,
        # The wire/model name is gha_installation_id, not
        # github_app_installation_id.
        gha_installation_id=repo.github_app_installation_id,
        ingress_submodules=repo.ingress_submodules,
    )


def _validate(spec: WorkspaceSpec) -> None:
    managed = spec.model_fields_set
    if "execution_mode" in managed and spec.execution_mode == "agent":
        if not spec.agent_pool_id:
            raise ValueError("execution_mode='agent' requires agent_pool_id")


def _current_value(workspace: Workspace, field: str) -> Any:
    value = getattr(workspace, field, None)
    return getattr(value, "value", value)


def _diff(spec: WorkspaceSpec, workspace: Workspace) -> list[Change]:
    """Compare only the fields the spec actually manages."""
    managed = spec.model_fields_set
    changes: list[Change] = []
    for field in _DIRECT_FIELDS:
        if field not in managed:
            continue
        desired = getattr(spec, field)
        current = _current_value(workspace, field)
        if desired != current:
            changes.append(Change(field=field, before=current, after=desired))
    if "project_id" in managed:
        current_project = getattr(getattr(workspace, "project", None), "id", None)
        if spec.project_id != current_project:
            changes.append(
                Change(field="project", before=current_project, after=spec.project_id)
            )
    if "vcs_repo" in managed:
        current_vcs = getattr(getattr(workspace, "vcs_repo", None), "identifier", None)
        desired_vcs = spec.vcs_repo.identifier if spec.vcs_repo else None
        if current_vcs != desired_vcs:
            changes.append(
                Change(field="vcs_repo", before=current_vcs, after=desired_vcs)
            )
    return changes


def _apply_spec(spec: WorkspaceSpec, target: dict[str, Any], *, creating: bool) -> None:
    managed = spec.model_fields_set
    for field in _DIRECT_FIELDS:
        if field in managed:
            target[field] = getattr(spec, field)
    if "project_id" in managed:
        # The options model takes a Project object, not a project_id string.
        target["project"] = Project(id=spec.project_id) if spec.project_id else None
    if "vcs_repo" in managed:
        target["vcs_repo"] = _vcs_repo_of(spec)
    if creating:
        for field in _CREATE_ONLY_FIELDS:
            if field in managed:
                target[field] = getattr(spec, field)
    else:
        dropped = [f for f in _CREATE_ONLY_FIELDS if f in managed]
        if dropped:
            logger.info("ignoring create-only field(s) on update: %s", dropped)


def _converge_tags(
    client: TFEClient, ws_id: str, desired: set[str], current: set[str]
) -> list[Change]:
    """Add and remove plain name-tags to match ``desired``."""
    changes: list[Change] = []
    to_add = sorted(desired - current)
    to_remove = sorted(current - desired)
    if to_add:
        client.workspaces.add_tags(
            ws_id, WorkspaceAddTagsOptions(tags=[Tag(name=name) for name in to_add])
        )
        changes.append(Change(field="tags.added", before=None, after=to_add))
    if to_remove:
        client.workspaces.remove_tags(
            ws_id,
            WorkspaceRemoveTagsOptions(tags=[Tag(name=name) for name in to_remove]),
        )
        changes.append(Change(field="tags.removed", before=to_remove, after=None))
    return changes


def ensure_workspace(
    client: TFEClient,
    organization: str,
    name: str,
    *,
    spec: WorkspaceSpec | None = None,
    dry_run: bool = False,
) -> EnsureResult:
    """Create a workspace, or converge an existing one onto ``spec``.

    Idempotent: calling twice with the same spec makes no write calls the second
    time and returns ``action="unchanged"``.

    A field left unset on the spec is *unmanaged* and never touched; a field set
    explicitly to ``None`` is cleared. Tags are converged with set semantics
    through ``add_tags``/``remove_tags`` rather than through ``tag_bindings``,
    because the workspaces resource drops any tag binding with an empty value.

    Args:
        client: The client to act through.
        organization: Organization that owns the workspace.
        name: Workspace name.
        spec: Desired settings. ``None`` means "exists, settings unmanaged".
        dry_run: Read only; report what would change.

    Returns:
        An :class:`~pytfe.workflows._result.EnsureResult`.

    Raises:
        ValueError: If the spec is internally inconsistent.
        TFEError: If the API rejects the create or update.

    Example:
        >>> result = ensure_workspace(
        ...     client, "acme", "web",
        ...     spec=WorkspaceSpec(terraform_version="1.9.5", auto_apply=False),
        ... )
        >>> result.action
        'created'
    """
    spec = spec or WorkspaceSpec()
    _validate(spec)

    try:
        workspace: Workspace | None = client.workspaces.read(
            name, organization=organization
        )
    except NotFound:
        workspace = None

    if workspace is None:
        if dry_run:
            return EnsureResult(
                action="would_create",
                resource_type="workspaces",
                changes=[Change(field="name", before=None, after=name)],
            )
        payload: dict[str, Any] = {"name": name}
        _apply_spec(spec, payload, creating=True)
        created = client.workspaces.create(
            organization, WorkspaceCreateOptions(**payload)
        )
        changes = [Change(field="name", before=None, after=name)]
        if spec.tags:
            changes += _converge_tags(client, created.id or "", spec.tags, set())
        return EnsureResult(
            action="created",
            resource_id=created.id,
            resource_type="workspaces",
            changes=changes,
        )

    ws_id = workspace.id or ""
    changes = _diff(spec, workspace)
    tag_changes: list[Change] = []
    desired_tags = spec.tags
    current_tags = set(workspace.tag_names or [])
    tags_differ = desired_tags is not None and desired_tags != current_tags

    if dry_run:
        if tags_differ and desired_tags is not None:
            changes.append(
                Change(
                    field="tags",
                    before=sorted(current_tags),
                    after=sorted(desired_tags),
                )
            )
        return EnsureResult(
            action="would_update" if changes else "unchanged",
            resource_id=ws_id,
            resource_type="workspaces",
            changes=changes,
        )

    if not changes and not tags_differ:
        return EnsureResult(
            action="unchanged", resource_id=ws_id, resource_type="workspaces"
        )

    if changes:
        payload = {}
        _apply_spec(spec, payload, creating=False)
        client.workspaces.update_by_id(ws_id, WorkspaceUpdateOptions(**payload))
    if tags_differ and desired_tags is not None:
        tag_changes = _converge_tags(client, ws_id, desired_tags, current_tags)

    return EnsureResult(
        action="updated",
        resource_id=ws_id,
        resource_type="workspaces",
        changes=changes + tag_changes,
    )


def _variable_differs(spec: VariableSpec, existing: Variable) -> list[Change]:
    changes: list[Change] = []
    if spec.sensitive or existing.sensitive:
        # A sensitive value is never readable, so it cannot be compared.
        return changes
    if existing.value != spec.value:
        changes.append(
            Change(field=f"{spec.key}.value", before=existing.value, after=spec.value)
        )
    if bool(existing.hcl) != spec.hcl:
        changes.append(
            Change(field=f"{spec.key}.hcl", before=existing.hcl, after=spec.hcl)
        )
    if (existing.description or None) != (spec.description or None):
        changes.append(
            Change(
                field=f"{spec.key}.description",
                before=existing.description,
                after=spec.description,
            )
        )
    return changes


def ensure_variables(
    client: TFEClient,
    workspace_id: str,
    variables: list[VariableSpec],
    *,
    prune: bool = False,
    sensitive_policy: Literal["update", "skip_if_present"] = "update",
    confirmed: bool = False,
    dry_run: bool = False,
) -> EnsureVariablesResult:
    """Converge a workspace's variables onto ``variables``.

    Variables are matched on ``(key, category)``. Sensitive values cannot be
    read back, so they cannot be compared: ``sensitive_policy="update"`` writes
    them every time (not idempotent, by design), while ``"skip_if_present"``
    leaves an existing sensitive variable alone.

    Args:
        client: The client to act through.
        workspace_id: Target workspace.
        variables: Desired variables.
        prune: Delete variables not in the desired set. Destructive, so it
            requires ``confirmed=True``.
        sensitive_policy: How to treat existing sensitive variables.
        confirmed: Required for ``prune``.
        dry_run: Read only; report what would change.

    Returns:
        An :class:`~pytfe.workflows.models.EnsureVariablesResult`. Sensitive
        values never appear in ``changes`` or ``summary()``.

    Raises:
        TFEError: If the API rejects a write.

    Example:
        >>> ensure_variables(client, ws.id, [
        ...     VariableSpec(key="region", value="eu-west-1"),
        ...     VariableSpec(key="AWS_ACCESS_KEY_ID", value="...",
        ...                  category="env", sensitive=True),
        ... ])
    """
    result = EnsureVariablesResult()
    # The /vars endpoint ignores page params; the resource handles that, but the
    # iterator is single-use so it is materialized before any branching.
    existing_all = list(client.variables.list(workspace_id))
    existing = {
        (v.key, getattr(v.category, "value", v.category)): v for v in existing_all
    }
    desired_keys = {(spec.key, spec.category) for spec in variables}

    for spec in variables:
        key = (spec.key, spec.category)
        current = existing.get(key)

        if current is None:
            if dry_run:
                result.created.append(spec.key)
                continue
            client.variables.create(
                workspace_id,
                VariableCreateOptions(
                    key=spec.key,
                    value=spec.value,
                    category=spec.category,
                    hcl=spec.hcl,
                    sensitive=spec.sensitive,
                    description=spec.description,
                ),
            )
            result.created.append(spec.key)
            result.changes.append(
                Change.redacted(spec.key)
                if spec.sensitive
                else Change(field=spec.key, before=None, after=spec.value)
            )
            continue

        if current.sensitive and not spec.sensitive:
            result.warnings.append(
                f"{spec.key}: cannot clear the sensitive flag via update; "
                "delete and recreate the variable to change it"
            )

        if spec.sensitive or current.sensitive:
            if sensitive_policy == "skip_if_present":
                result.unchanged.append(spec.key)
                continue
            if dry_run:
                result.updated.append(spec.key)
                result.changes.append(Change.redacted(spec.key))
                continue
            client.variables.update(
                workspace_id,
                current.id or "",
                VariableUpdateOptions(
                    key=spec.key,
                    value=spec.value,
                    category=spec.category,
                    hcl=spec.hcl,
                    sensitive=True,
                    description=spec.description,
                ),
            )
            result.updated.append(spec.key)
            result.changes.append(Change.redacted(spec.key))
            continue

        diffs = _variable_differs(spec, current)
        if not diffs:
            result.unchanged.append(spec.key)
            continue
        if dry_run:
            result.updated.append(spec.key)
            result.changes.extend(diffs)
            continue
        client.variables.update(
            workspace_id,
            current.id or "",
            VariableUpdateOptions(
                key=spec.key,
                value=spec.value,
                category=spec.category,
                hcl=spec.hcl,
                sensitive=spec.sensitive,
                description=spec.description,
            ),
        )
        result.updated.append(spec.key)
        result.changes.extend(diffs)

    if prune:
        extra = [
            v
            for (k, c), v in existing.items()
            if (k, c) not in desired_keys  # noqa: B007
        ]
        names = sorted(v.key or "" for v in extra)
        if names and not confirmed:
            result.action = "awaiting_confirmation"
            result.would_delete = names
            result.ok = True
            return result
        for variable in extra:
            if dry_run:
                result.deleted.append(variable.key or "")
                continue
            client.variables.delete(workspace_id, variable.id or "")
            result.deleted.append(variable.key or "")

    if dry_run:
        result.action = (
            "would_update"
            if (result.created or result.updated or result.deleted)
            else "unchanged"
        )
    elif result.created or result.updated or result.deleted:
        result.action = "updated" if not result.created else "created"
    else:
        result.action = "unchanged"
    return result
