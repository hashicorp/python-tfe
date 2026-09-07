# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Workflows that fan out across many workspaces.

Two rules make concurrency safe here, and both are load-bearing:

1. **Listings are materialized on the calling thread first.** ``list_*`` methods
   return single-use, lazily-paginating iterators; handing one to a thread pool
   would drive pagination requests from worker threads against one shared
   generator. Every fan-out below resolves its work list before submitting any
   task.
2. **One failure never aborts the fleet.** Each item's error is captured via
   ``TFEError.to_dict()`` and reported alongside the successes.

Sharing a single client across threads is safe: ``httpx.Client`` is thread-safe,
and the transport's cookie jar - the one piece of shared mutable state it had -
now refuses to store anything rather than being cleared per response. Retry
backoff is jittered, so pooled workers that hit the same rate limit no longer
wake in lockstep.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any, TypedDict

from ..client import TFEClient
from ..errors import TFEError
from .models import (
    EnsureVariablesResult,
    FleetItem,
    FleetResult,
    OrgInventory,
    ResourceInventory,
    VariableSpec,
    WorkspaceSpec,
    WorkspaceSummary,
)
from .workspaces import ensure_variables, ensure_workspace, find_workspaces
from .workspaces import workspace_status as _workspace_status

logger = logging.getLogger("pytfe.workflows")

__all__ = [
    "WorkspaceFilter",
    "bulk_speculative_plan",
    "bulk_update",
    "bulk_variable_rotate",
    "org_inventory",
    "resource_inventory",
]


class WorkspaceFilter(TypedDict, total=False):
    """Selection criteria, mirroring :func:`find_workspaces` keyword arguments."""

    name_pattern: str
    tags: list[str]
    exclude_tags: list[str]
    project_id: str
    terraform_version: str
    execution_mode: str
    limit: int


def _select(
    client: TFEClient, organization: str, selector: WorkspaceFilter | None
) -> list[WorkspaceSummary]:
    """Resolve the work list on the calling thread."""
    return find_workspaces(client, organization, **(selector or {})).items


def _fan_out(
    workspaces: list[WorkspaceSummary],
    work: Callable[[WorkspaceSummary], Any],
    *,
    concurrency: int,
) -> FleetResult:
    """Run ``work`` over each workspace, collecting failures rather than raising."""
    result = FleetResult()
    if not workspaces:
        return result

    def run_one(summary: WorkspaceSummary) -> FleetItem:
        try:
            return FleetItem(workspace=summary, result=work(summary))
        except TFEError as exc:
            logger.info("fleet item %s failed: %s", summary.name, exc)
            return FleetItem(workspace=summary, error=exc.to_dict())

    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        result.items = list(pool.map(run_one, workspaces))

    result.succeeded = sum(1 for item in result.items if item.ok)
    result.failed = len(result.items) - result.succeeded
    result.ok = result.failed == 0
    return result


def bulk_speculative_plan(
    client: TFEClient,
    organization: str,
    directory: str,
    *,
    filter: WorkspaceFilter | None = None,
    concurrency: int = 4,
    timeout: float = 1800,
) -> FleetResult:
    """Plan one configuration directory against many workspaces.

    Never applies anything. Useful for answering "which of these workspaces
    would this change break?" before a rollout.

    Note:
        The *same* directory is planned against every matched workspace. That is
        the point for a shared module, and wrong for per-workspace configs.

    Args:
        client: The client to act through.
        organization: Organization to search.
        directory: Local configuration directory to plan.
        filter: Which workspaces to select.
        concurrency: Worker threads.
        timeout: Per-workspace seconds to wait.

    Returns:
        A :class:`~pytfe.workflows.models.FleetResult` of
        :class:`~pytfe.workflows.models.RunResult` values.

    Raises:
        TFEError: If the workspace listing itself fails.

    Example:
        >>> fleet = bulk_speculative_plan(client, "acme", "./terraform",
        ...                               filter={"name_pattern": "prod-*"})
        >>> fleet.summary()["failed"]
        0
    """
    from .runs import speculative_plan

    workspaces = _select(client, organization, filter)
    result = _fan_out(
        workspaces,
        lambda ws: speculative_plan(
            client, directory, workspace_id=ws.id, timeout=timeout
        ),
        concurrency=concurrency,
    )
    result.kind = "read"
    destructive = [
        item.workspace.name
        for item in result.items
        if item.ok
        and getattr(item.result, "plan", None) is not None
        and item.result.plan.is_destructive
    ]
    if destructive:
        result.warnings.append(
            "plan is destructive in: " + ", ".join(sorted(destructive))
        )
    return result


def bulk_update(
    client: TFEClient,
    organization: str,
    *,
    spec: WorkspaceSpec,
    filter: WorkspaceFilter | None = None,
    dry_run: bool = False,
    confirmed: bool = False,
    concurrency: int = 4,
) -> FleetResult:
    """Converge many workspaces onto one spec.

    Gated even though single-workspace ``ensure_workspace`` is not: a
    fleet-wide write is a different order of risk. Pass ``dry_run=True`` to
    preview, or ``confirmed=True`` to proceed.

    Args:
        client: The client to act through.
        organization: Organization to search.
        spec: Settings to converge onto. Unset fields stay unmanaged.
        filter: Which workspaces to select.
        dry_run: Read only; report what would change.
        confirmed: Required to actually write.
        concurrency: Worker threads.

    Returns:
        A :class:`~pytfe.workflows.models.FleetResult` of
        :class:`~pytfe.workflows._result.EnsureResult` values.

    Raises:
        TFEError: If the workspace listing itself fails.

    Example:
        >>> bulk_update(client, "acme", spec=WorkspaceSpec(terraform_version="1.9.5"),
        ...             filter={"name_pattern": "prod-*"}, dry_run=True)
    """
    workspaces = _select(client, organization, filter)
    if not dry_run and not confirmed:
        result = FleetResult(
            skipped=len(workspaces),
            warnings=[
                f"would update {len(workspaces)} workspace(s); pass confirmed=True "
                "to proceed, or dry_run=True to preview the changes"
            ],
        )
        return result
    return _fan_out(
        workspaces,
        lambda ws: ensure_workspace(
            client, organization, ws.name, spec=spec, dry_run=dry_run
        ),
        concurrency=concurrency,
    )


def bulk_variable_rotate(
    client: TFEClient,
    organization: str,
    *,
    variable: VariableSpec,
    filter: WorkspaceFilter | None = None,
    dry_run: bool = False,
    confirmed: bool = False,
    concurrency: int = 4,
) -> FleetResult:
    """Set one variable across many workspaces.

    Built for credential rotation, so it is gated like :func:`bulk_update`.
    A sensitive value is written to every matched workspace and never appears in
    any result or log line.

    Args:
        client: The client to act through.
        organization: Organization to search.
        variable: The variable to set everywhere.
        filter: Which workspaces to select.
        dry_run: Read only; report what would change.
        confirmed: Required to actually write.
        concurrency: Worker threads.

    Returns:
        A :class:`~pytfe.workflows.models.FleetResult` of
        :class:`~pytfe.workflows.models.EnsureVariablesResult` values.

    Raises:
        TFEError: If the workspace listing itself fails.

    Example:
        >>> bulk_variable_rotate(
        ...     client, "acme",
        ...     variable=VariableSpec(key="AWS_SECRET_ACCESS_KEY", value="...",
        ...                           category="env", sensitive=True),
        ...     filter={"tags": ["aws"]}, confirmed=True)
    """
    workspaces = _select(client, organization, filter)
    if not dry_run and not confirmed:
        return FleetResult(
            skipped=len(workspaces),
            warnings=[
                f"would set {variable.key!r} on {len(workspaces)} workspace(s); "
                "pass confirmed=True to proceed"
            ],
        )

    def rotate(ws: WorkspaceSummary) -> EnsureVariablesResult:
        return ensure_variables(client, ws.id, [variable], dry_run=dry_run)

    return _fan_out(workspaces, rotate, concurrency=concurrency)


def org_inventory(
    client: TFEClient,
    organization: str,
    *,
    filter: WorkspaceFilter | None = None,
    concurrency: int = 4,
) -> OrgInventory:
    """Report the health of every workspace in an organization.

    Args:
        client: The client to read through.
        organization: Organization to inventory.
        filter: Restrict to a subset of workspaces.
        concurrency: Worker threads.

    Returns:
        An :class:`~pytfe.workflows.models.OrgInventory`, which also renders as
        CSV via ``to_csv()``.

    Raises:
        TFEError: If the workspace listing itself fails.

    Example:
        >>> inventory = org_inventory(client, "acme")
        >>> print(inventory.to_csv())
    """
    workspaces = _select(client, organization, filter)
    fleet = _fan_out(
        workspaces,
        lambda ws: _workspace_status(client, ws.id),
        concurrency=concurrency,
    )

    result = OrgInventory(organization=organization)
    for item in fleet.items:
        if not item.ok:
            result.warnings.append(
                f"{item.workspace.name}: {(item.error or {}).get('message')}"
            )
            continue
        status = item.result
        result.rows.append(status)
        version = status.terraform_version or "unknown"
        result.by_terraform_version[version] = (
            result.by_terraform_version.get(version, 0) + 1
        )
        mode = status.execution_mode or "unknown"
        result.by_execution_mode[mode] = result.by_execution_mode.get(mode, 0) + 1
        if status.health == "drifted":
            result.drifted.append(status.name)
        elif status.health == "locked":
            result.locked.append(status.name)
        elif status.health == "errored":
            result.errored.append(status.name)
    return result


def resource_inventory(
    client: TFEClient,
    organization: str,
    *,
    resource_type: str | None = None,
    provider: str | None = None,
    filter: WorkspaceFilter | None = None,
    concurrency: int = 4,
    max_rows: int = 5000,
) -> ResourceInventory:
    """List managed resources across an organization.

    Answers "where is this resource type deployed?" without downloading every
    state file - the workspace-resources endpoint is used where available.

    Args:
        client: The client to read through.
        organization: Organization to inventory.
        resource_type: Only rows whose type matches exactly.
        provider: Only rows whose provider matches exactly.
        filter: Restrict to a subset of workspaces.
        concurrency: Worker threads.
        max_rows: Stop collecting after this many rows.

    Returns:
        A :class:`~pytfe.workflows.models.ResourceInventory`.

    Raises:
        TFEError: If the workspace listing itself fails.

    Example:
        >>> inventory = resource_inventory(client, "acme", resource_type="aws_s3_bucket")
        >>> inventory.by_workspace
        {'prod-web': 3}
    """
    from .state import state_inventory

    workspaces = _select(client, organization, filter)
    fleet = _fan_out(
        workspaces,
        lambda ws: state_inventory(client, ws.id),
        concurrency=concurrency,
    )

    result = ResourceInventory(organization=organization)
    for item in fleet.items:
        if not item.ok:
            result.warnings.append(
                f"{item.workspace.name}: {(item.error or {}).get('message')}"
            )
            continue
        for row in item.result.resources:
            if resource_type and row.type != resource_type:
                continue
            if provider and row.provider != provider:
                continue
            if len(result.rows) >= max_rows:
                result.truncated = True
                break
            row.workspace_name = row.workspace_name or item.workspace.name
            result.rows.append(row)

    for row in result.rows:
        if row.type:
            result.by_type[row.type] = result.by_type.get(row.type, 0) + 1
        if row.provider:
            result.by_provider[row.provider] = (
                result.by_provider.get(row.provider, 0) + 1
            )
        name = row.workspace_name or row.workspace_id or "unknown"
        result.by_workspace[name] = result.by_workspace.get(name, 0) + 1
    return result
