# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""State-shaped workflows."""

from __future__ import annotations

import logging

from ..client import TFEClient
from ._poll import wait_until
from ._resolve import resolve_workspace
from ._result import SENSITIVE
from .models import Outputs

logger = logging.getLogger("pytfe.workflows")

__all__ = ["read_outputs"]


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
