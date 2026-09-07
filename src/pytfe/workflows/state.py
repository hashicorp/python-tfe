# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""State-shaped workflows."""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Callable
from typing import Any

from ..client import TFEClient
from ..errors import TFEError, WorkflowError
from ._poll import wait_until
from ._resolve import organization_of, resolve_workspace
from ._result import SENSITIVE
from .models import (
    Outputs,
    PushStateResult,
    ResourceRow,
    StateDownload,
    StateInventory,
)

logger = logging.getLogger("pytfe.workflows")

__all__ = [
    "read_outputs",
    "download_state",
    "state_inventory",
    "push_state",
    "rollback_state",
    "migrate_state",
]


def read_outputs(
    client: TFEClient,
    workspace_id: str | None = None,
    *,
    organization: str | None = None,
    workspace_name: str | None = None,
    include_sensitive: bool = False,
    timeout: float = 300,
) -> Outputs:
    """Read a workspace's current state outputs, waiting for processing.

    A state version is not readable the instant it is created - the API
    processes it asynchronously. This waits for ``resources_processed`` before
    reading, which is the step most hand-written scripts miss.

    Args:
        client: The client to read through.
        workspace_id: Target workspace, by ID.
        organization: Organization name, with ``workspace_name``.
        workspace_name: Workspace name, with ``organization``.
        include_sensitive: Return sensitive values instead of a placeholder.
            ``summary()`` redacts them regardless.
        timeout: Seconds to wait for state processing.

    Returns:
        An :class:`~pytfe.workflows.models.Outputs`.

    Raises:
        WorkspaceNotFound: If the workspace cannot be resolved.
        WorkflowTimeout: If the state version is not processed in time.
        TFEError: If the workspace has no state version yet.

    Example:
        >>> outputs = read_outputs(client, organization="acme", workspace_name="web")
        >>> outputs.values["vpc_id"]
        'vpc-0a1b2c3d'
    """
    workspace = resolve_workspace(
        client, workspace_id, organization=organization, workspace_name=workspace_name
    )
    ws_id = workspace.id or ""

    state_version = wait_until(
        lambda: client.state_versions.read_current(ws_id),
        lambda sv: bool(getattr(sv, "resources_processed", True)),
        timeout=timeout,
        interval=1.0,
        description=f"state version for workspace {ws_id} to be processed",
    )

    result = Outputs(
        state_version_id=state_version.id,
        serial=getattr(state_version, "serial", None),
        terraform_version=getattr(state_version, "terraform_version", None),
    )

    for output in client.state_version_outputs.read_current(ws_id):
        name = getattr(output, "name", None)
        if not name:
            continue
        if getattr(output, "sensitive", False):
            result.sensitive_keys.append(name)
            value = getattr(output, "value", None)
            result.values[name] = value if include_sensitive else SENSITIVE
        else:
            result.values[name] = getattr(output, "value", None)

    return result


def _parse_state(raw: bytes) -> dict[str, Any]:
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkflowError(
            f"state is not valid JSON: {exc}",
            hint="The workspace may have no state yet, or the download was truncated.",
        ) from exc
    return parsed if isinstance(parsed, dict) else {}


def download_state(
    client: TFEClient,
    workspace_id: str | None = None,
    *,
    organization: str | None = None,
    workspace_name: str | None = None,
    state_version_id: str | None = None,
    timeout: float = 300,
) -> StateDownload:
    """Download and parse a workspace's state.

    Waits for the state version to be processed before downloading, which is the
    step most hand-written scripts skip.

    Args:
        client: The client to read through.
        workspace_id: Target workspace, by ID.
        organization: Organization name, with ``workspace_name``.
        workspace_name: Workspace name, with ``organization``.
        state_version_id: A specific version. Defaults to the current one.
        timeout: Seconds to wait for state processing.

    Returns:
        A :class:`~pytfe.workflows.models.StateDownload`. ``summary()`` omits
        the state body, which is large and may contain secrets.

    Raises:
        WorkspaceNotFound: If the workspace cannot be resolved.
        WorkflowTimeout: If the state version is not processed in time.
        WorkflowError: If the downloaded bytes are not valid JSON.

    Example:
        >>> download = download_state(client, "ws-YnyXLq9fy38afEeb")
        >>> download.serial
        42
    """
    ws_id = ""
    if state_version_id is None:
        workspace = resolve_workspace(
            client,
            workspace_id,
            organization=organization,
            workspace_name=workspace_name,
        )
        ws_id = workspace.id or ""
        fetch = lambda: client.state_versions.read_current(ws_id)  # noqa: E731
    else:
        fetch = lambda: client.state_versions.read(state_version_id)  # noqa: E731

    state_version = wait_until(
        fetch,
        lambda sv: bool(getattr(sv, "resources_processed", True)),
        timeout=timeout,
        interval=1.0,
        description="the state version to be processed",
    )

    raw = client.state_versions.download(state_version.id or "")
    parsed = _parse_state(raw)
    return StateDownload(
        workspace_id=ws_id or None,
        state_version_id=state_version.id,
        serial=getattr(state_version, "serial", None) or parsed.get("serial"),
        lineage=parsed.get("lineage"),
        terraform_version=(
            getattr(state_version, "terraform_version", None)
            or parsed.get("terraform_version")
        ),
        size_bytes=len(raw),
        state=parsed,
    )


def _rows_from_state(state: dict[str, Any], max_resources: int) -> list[ResourceRow]:
    rows: list[ResourceRow] = []
    for resource in state.get("resources") or []:
        if len(rows) >= max_resources:
            break
        module = resource.get("module")
        rtype = resource.get("type")
        name = resource.get("name")
        prefix = f"{module}." if module else ""
        rows.append(
            ResourceRow(
                address=f"{prefix}{rtype}.{name}",
                type=rtype,
                provider=(resource.get("provider") or "").split('"')[-2]
                if '"' in (resource.get("provider") or "")
                else resource.get("provider"),
                module=module,
                mode=resource.get("mode"),
            )
        )
    return rows


def state_inventory(
    client: TFEClient,
    workspace_id: str | None = None,
    *,
    organization: str | None = None,
    workspace_name: str | None = None,
    max_resources: int = 500,
    prefer_api: bool = True,
) -> StateInventory:
    """List the resources a workspace manages.

    Prefers the workspace-resources endpoint, which is far cheaper than
    downloading a whole state file. Falls back to parsing state when that
    endpoint is unavailable.

    Args:
        client: The client to read through.
        workspace_id: Target workspace, by ID.
        organization: Organization name, with ``workspace_name``.
        workspace_name: Workspace name, with ``organization``.
        max_resources: Cap on rows collected.
        prefer_api: Try the workspace-resources endpoint first.

    Returns:
        A :class:`~pytfe.workflows.models.StateInventory`.

    Raises:
        WorkspaceNotFound: If the workspace cannot be resolved.

    Example:
        >>> inventory = state_inventory(client, "ws-YnyXLq9fy38afEeb")
        >>> inventory.by_type["aws_s3_bucket"]
        3
    """
    workspace = resolve_workspace(
        client, workspace_id, organization=organization, workspace_name=workspace_name
    )
    ws_id = workspace.id or ""
    result = StateInventory(workspace_id=ws_id)

    rows: list[ResourceRow] = []
    if prefer_api:
        try:
            for resource in client.workspace_resources.list(ws_id):
                if len(rows) >= max_resources:
                    result.truncated = True
                    break
                rows.append(
                    ResourceRow(
                        workspace_id=ws_id,
                        workspace_name=workspace.name,
                        address=getattr(resource, "address", "") or "",
                        type=getattr(resource, "name", None),
                        provider=getattr(resource, "provider_type", None),
                        module=getattr(resource, "module", None),
                        mode=getattr(resource, "mode", None),
                    )
                )
        except TFEError as exc:
            result.warnings.append(f"workspace-resources unavailable: {exc}")
            rows = []

    if not rows:
        download = download_state(client, ws_id)
        rows = _rows_from_state(download.state, max_resources)
        for row in rows:
            row.workspace_id = ws_id
            row.workspace_name = workspace.name
        result.truncated = len(download.state.get("resources") or []) > len(rows)

    result.resources = rows
    for row in rows:
        if row.type:
            result.by_type[row.type] = result.by_type.get(row.type, 0) + 1
        if row.provider:
            result.by_provider[row.provider] = (
                result.by_provider.get(row.provider, 0) + 1
            )
    return result


def push_state(
    client: TFEClient,
    workspace_id: str,
    state: bytes | dict[str, Any],
    *,
    json_state: bytes | None = None,
    force: bool = False,
    confirmed: bool = False,
    confirm: Callable[[PushStateResult], bool] | None = None,
    timeout: float = 300,
) -> PushStateResult:
    """Write a new state version, overwriting the workspace's current state.

    Destructive and gated: without ``confirmed=True`` or a ``confirm`` callback
    this returns ``action="awaiting_confirmation"`` and writes nothing.

    The workspace is locked for the duration and unlocked in a ``finally``. If
    the unlock itself fails, the upload error is still what propagates and
    ``still_locked`` is set on the result, because a masked upload error with a
    stranded lock is the worst possible outcome.

    Args:
        client: The client to act through.
        workspace_id: Target workspace.
        state: Raw ``.tfstate`` bytes, or a dict to serialize.
        json_state: Optional raw JSON state bytes.
        force: Skip the lineage check and the serial floor.
        confirmed: The caller asserts a human approved this.
        confirm: Called with the pending result; return True to proceed.
        timeout: Seconds to wait for state processing.

    Returns:
        A :class:`~pytfe.workflows.models.PushStateResult`.

    Raises:
        TFEError: If the upload fails.

    Example:
        >>> push_state(client, "ws-YnyXLq9fy38afEeb", state_bytes, confirmed=True)
    """
    raw = json.dumps(state).encode("utf-8") if isinstance(state, dict) else state
    parsed = _parse_state(raw)

    current_serial: int | None = None
    current_lineage: str | None = None
    try:
        current = download_state(client, workspace_id, timeout=timeout)
        current_serial = current.serial
        current_lineage = current.lineage
    except (TFEError, WorkflowError):
        logger.debug("workspace %s has no current state", workspace_id)

    result = PushStateResult(
        workspace_id=workspace_id,
        serial_before=current_serial,
        lineage=parsed.get("lineage"),
    )

    incoming_lineage = parsed.get("lineage")
    if (
        not force
        and current_lineage
        and incoming_lineage
        and current_lineage != incoming_lineage
    ):
        result.action = "refused"
        result.ok = False
        result.warnings.append(
            f"lineage mismatch: workspace has {current_lineage!r}, "
            f"incoming state has {incoming_lineage!r}. Pass force=True to override."
        )
        return result

    serial = int(parsed.get("serial") or 0)
    if not force and current_serial is not None and serial <= current_serial:
        serial = current_serial + 1
    result.serial_after = serial

    if confirm is not None:
        if not confirm(result):
            result.action = "awaiting_confirmation"
            return result
    elif not confirmed:
        result.action = "awaiting_confirmation"
        return result

    from ..models.state_version import StateVersionCreateOptions
    from ..models.workspace import WorkspaceLockOptions

    client.workspaces.lock(
        workspace_id, WorkspaceLockOptions(reason="pytfe.workflows.push_state")
    )
    try:
        version = client.state_versions.upload(
            workspace_id,
            raw_state=raw,
            raw_json_state=json_state,
            options=StateVersionCreateOptions(
                serial=serial,
                md5=hashlib.md5(raw).hexdigest(),  # noqa: S324 - required by the API
                lineage=incoming_lineage,
            ),
        )
        result.state_version_id = version.id
        wait_until(
            lambda: client.state_versions.read(version.id or ""),
            lambda sv: bool(getattr(sv, "resources_processed", True)),
            timeout=timeout,
            interval=1.0,
            description="the uploaded state version to be processed",
        )
        result.action = "pushed"
    finally:
        try:
            client.workspaces.unlock(workspace_id)
        except TFEError as exc:
            # Never mask the upload failure with an unlock failure, but do tell
            # the caller the workspace may still be locked.
            result.still_locked = True
            result.warnings.append(f"workspace may still be locked: {exc}")
            logger.warning("could not unlock workspace %s: %s", workspace_id, exc)
    return result


def rollback_state(
    client: TFEClient,
    workspace_id: str,
    *,
    to_state_version_id: str | None = None,
    steps_back: int = 1,
    confirmed: bool = False,
    confirm: Callable[[PushStateResult], bool] | None = None,
) -> PushStateResult:
    """Roll a workspace back to an earlier state version.

    Uses the API's own rollback endpoint, which creates a *new* version whose
    content matches the chosen one. No state version is ever deleted.

    Destructive and gated.

    Args:
        client: The client to act through.
        workspace_id: Target workspace.
        to_state_version_id: The version to roll back to. Overrides ``steps_back``.
        steps_back: How many versions to go back from current. ``1`` is the
            version immediately before the current one.
        confirmed: The caller asserts a human approved this.
        confirm: Called with the pending result; return True to proceed.

    Returns:
        A :class:`~pytfe.workflows.models.PushStateResult`.

    Raises:
        WorkflowError: If no suitable earlier version exists.
        TFEError: If the rollback is rejected.

    Example:
        >>> rollback_state(client, "ws-YnyXLq9fy38afEeb", steps_back=1, confirmed=True)
    """
    from ..models.state_version import StateVersionListOptions

    current = client.state_versions.read_current(workspace_id)
    target_id = to_state_version_id

    if target_id is None:
        if steps_back < 1:
            raise WorkflowError(
                "steps_back must be at least 1",
                hint="steps_back=1 is the version immediately before the current one.",
            )
        # The listing filters by workspace *name* plus organization, not by
        # id, so the workspace has to be resolved first.
        workspace = resolve_workspace(client, workspace_id)
        versions = list(
            client.state_versions.list(
                StateVersionListOptions(
                    workspace=workspace.name or "",
                    organization=organization_of(client, workspace),
                )
            )
        )
        # The listing is newest-first; index 0 is the current version.
        if len(versions) <= steps_back:
            raise WorkflowError(
                f"workspace has only {len(versions)} state version(s); "
                f"cannot go back {steps_back}",
                hint="Pass to_state_version_id explicitly, or use a smaller steps_back.",
            )
        target_id = versions[steps_back].id

    result = PushStateResult(
        workspace_id=workspace_id,
        serial_before=getattr(current, "serial", None),
        state_version_id=target_id,
    )

    if confirm is not None:
        if not confirm(result):
            result.action = "awaiting_confirmation"
            return result
    elif not confirmed:
        result.action = "awaiting_confirmation"
        return result

    rolled = client.state_versions.rollback(workspace_id, target_id or "")
    result.state_version_id = rolled.id
    result.serial_after = getattr(rolled, "serial", None)
    result.action = "pushed"
    return result


def migrate_state(
    client: TFEClient,
    source_workspace_id: str,
    target_workspace_id: str,
    *,
    confirmed: bool = False,
    confirm: Callable[[PushStateResult], bool] | None = None,
    timeout: float = 300,
) -> PushStateResult:
    """Copy state from one workspace to another.

    Destructive and gated: this overwrites the target's state. A target that
    already has state produces a warning, not a refusal - moving state onto a
    populated workspace is sometimes exactly the intent.

    Args:
        client: The client to act through.
        source_workspace_id: Workspace to copy state from.
        target_workspace_id: Workspace to copy state to.
        confirmed: The caller asserts a human approved this.
        confirm: Called with the pending result; return True to proceed.
        timeout: Seconds to wait for state processing.

    Returns:
        A :class:`~pytfe.workflows.models.PushStateResult`.

    Raises:
        TFEError: If either side cannot be read or the upload fails.

    Example:
        >>> migrate_state(client, "ws-source", "ws-target", confirmed=True)
    """
    source = download_state(client, source_workspace_id, timeout=timeout)

    warnings: list[str] = []
    try:
        existing = download_state(client, target_workspace_id, timeout=timeout)
        if existing.state.get("resources"):
            warnings.append(
                f"target workspace already has state at serial {existing.serial} "
                f"with {len(existing.state.get('resources') or [])} resource(s); "
                "it will be overwritten"
            )
    except (TFEError, WorkflowError):
        logger.debug("target workspace %s has no state", target_workspace_id)

    result = push_state(
        client,
        target_workspace_id,
        source.state,
        force=True,
        confirmed=confirmed,
        confirm=confirm,
        timeout=timeout,
    )
    result.warnings = warnings + result.warnings
    return result
