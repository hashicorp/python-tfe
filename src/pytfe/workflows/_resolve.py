# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Identifier resolution shared by workspace-scoped workflows.

The resource layer addresses workspaces two ways - ``read(name, *,
organization=...)`` and ``read_by_id(workspace_id)``. Workflows accept either
and resolve once, so a caller never has to know which form a given step needs.
"""

from __future__ import annotations

from ..client import TFEClient
from ..errors import WORKSPACE_NOT_FOUND_HINT, NotFound, TFEError, WorkspaceNotFound
from ..models.workspace import Workspace

__all__ = [
    "resolve_workspace",
    "organization_of",
    "workspace_web_url",
    "run_web_url",
]


def resolve_workspace(
    client: TFEClient,
    workspace_id: str | None = None,
    *,
    organization: str | None = None,
    workspace_name: str | None = None,
) -> Workspace:
    """Resolve a workspace from either an ID or an organization/name pair.

    Args:
        client: The client to read through.
        workspace_id: A ``ws-`` identifier. Takes precedence when given.
        organization: Organization name, required with ``workspace_name``.
        workspace_name: Workspace name, required with ``organization``.

    Returns:
        The workspace.

    Raises:
        WorkspaceNotFound: If no workspace matches, or if neither addressing
            form was supplied.

    Example:
        >>> ws = resolve_workspace(client, organization="acme", workspace_name="web")
        >>> ws.id
        'ws-YnyXLq9fy38afEeb'
    """
    if workspace_id:
        try:
            return client.workspaces.read_by_id(workspace_id)
        except NotFound as exc:
            raise WorkspaceNotFound(
                f"no workspace with ID {workspace_id!r}", hint=WORKSPACE_NOT_FOUND_HINT
            ) from exc

    if organization and workspace_name:
        try:
            return client.workspaces.read(workspace_name, organization=organization)
        except NotFound as exc:
            raise WorkspaceNotFound(
                f"no workspace named {workspace_name!r} in organization "
                f"{organization!r}",
                hint=WORKSPACE_NOT_FOUND_HINT,
            ) from exc

    raise WorkspaceNotFound(
        "pass workspace_id, or both organization and workspace_name",
        hint=WORKSPACE_NOT_FOUND_HINT,
    )


def organization_of(
    client: TFEClient, workspace: Workspace, fallback: str | None = None
) -> str:
    """Organization name for a workspace.

    ``Workspace`` carries no ``organization_name`` field, so this reads the
    parsed relationship and falls back to whatever the caller supplied.
    """
    try:
        if workspace.has_relationships:
            org = workspace.related("organization")
            name = getattr(org, "name", None) or getattr(org, "id", None)
            if isinstance(name, str):
                return name
    except (AttributeError, TFEError):
        pass
    return fallback or ""


def workspace_web_url(client: TFEClient, organization: str, workspace_name: str) -> str:
    """Return the browser URL for a workspace.

    Reads ``client.config.address`` rather than the private transport, so it
    stays inside the public surface the workflow layer is allowed to touch.
    """
    base = client.config.address.rstrip("/")
    return f"{base}/app/{organization}/workspaces/{workspace_name}"


def run_web_url(
    client: TFEClient, organization: str, workspace_name: str, run_id: str
) -> str:
    """Return the browser URL for a run, for an agent to hand to a human."""
    return f"{workspace_web_url(client, organization, workspace_name)}/runs/{run_id}"
