# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Registry workflows: publish modules, provision from no-code modules."""

from __future__ import annotations

import io
import logging
import os
import time
from collections.abc import Callable
from typing import Any

from ..client import TFEClient
from ..errors import CoreGap, NotFound, WorkflowError
from ..models.no_code_module import (
    NoCodeWorkspaceCreateOptions,
    NoCodeWorkspaceVariable,
)
from ..models.registry_module import (
    RegistryModuleCreateOptions,
    RegistryModuleCreateVersionOptions,
    RegistryModuleID,
    RegistryName,
)
from ._package import package_directory
from ._poll import wait_until
from .models import PublishResult, RunResult, VariableSpec

logger = logging.getLogger("pytfe.workflows")

__all__ = [
    "publish_module_version",
    "publish_provider_version",
    "no_code_provision",
]


def _upload_url_of(version: Any) -> str | None:
    """Pull the upload link off a registry module version."""
    links = getattr(version, "links", None) or {}
    if isinstance(links, dict):
        for key in ("upload", "upload-url", "uploadUrl"):
            value = links.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def publish_module_version(
    client: TFEClient,
    organization: str,
    name: str,
    provider: str,
    version: str,
    directory: str | os.PathLike[str],
    *,
    namespace: str | None = None,
    registry_name: str = "private",
    timeout: float = 300,
) -> PublishResult:
    """Publish a new version of a private registry module from a directory.

    Note:
        ``client.registry_modules.upload(rmv, path)`` raises
        ``NotImplementedError`` in pytfe |version|, so this workflow packages the
        directory itself - with Terraform's exclusion rules - and uses the public
        ``upload_tar_gzip`` method.

    Args:
        client: The client to act through.
        organization: Organization that owns the module.
        name: Module name.
        provider: Module provider, e.g. ``"aws"``.
        version: Semantic version to publish.
        directory: Local directory holding the module source.
        namespace: Registry namespace, for public modules.
        registry_name: ``"private"`` or ``"public"``.
        timeout: Seconds to wait for the version to finish processing.

    Returns:
        A :class:`~pytfe.workflows.models.PublishResult`.

    Raises:
        WorkflowError: If the version does not provide an upload link, or ends
            in an errored state.
        WorkflowTimeout: If processing does not finish in time.
        TFEError: If the API rejects a call.

    Example:
        >>> publish_module_version(client, "acme", "vpc", "aws", "1.2.0", "./vpc")
    """
    module_id = RegistryModuleID(
        organization=organization,
        name=name,
        provider=provider,
        namespace=namespace,
        registry_name=RegistryName(registry_name),
    )

    try:
        client.registry_modules.read(module_id)
    except NotFound:
        logger.info("creating registry module %s/%s", name, provider)
        client.registry_modules.create(
            organization,
            RegistryModuleCreateOptions(
                name=name,
                provider=provider,
                namespace=namespace,
                registry_name=RegistryName(registry_name),
            ),
        )

    existing = {v.version for v in client.registry_modules.list_versions(module_id)}
    if version in existing:
        return PublishResult(
            action="unchanged",
            name=name,
            provider=provider,
            version=version,
            warnings=[f"version {version} already exists; nothing was uploaded"],
        )

    module_version = client.registry_modules.create_version(
        module_id, RegistryModuleCreateVersionOptions(version=version)
    )
    upload_url = _upload_url_of(module_version)
    if not upload_url:
        raise WorkflowError(
            f"registry module version {version} did not include an upload link",
            hint="The module may be VCS-backed, in which case versions are "
            "published by tagging the repository rather than by upload.",
        )

    archive = package_directory(directory)
    client.registry_modules.upload_tar_gzip(upload_url, io.BytesIO(archive))

    final = wait_until(
        lambda: client.registry_modules.read_version(module_id, version),
        lambda v: getattr(v.status, "value", v.status)
        in ("ok", "setup_complete", "errored", "setup_failed"),
        timeout=timeout,
        interval=2.0,
        description=f"registry module version {version} to finish processing",
    )
    status = getattr(final.status, "value", final.status)
    if status in ("errored", "setup_failed"):
        raise WorkflowError(
            f"registry module version {version} failed to publish (status {status})",
            hint="Check the module source for a missing required file or an "
            "invalid Terraform configuration.",
        )

    return PublishResult(
        action="published",
        module_id=getattr(module_version, "id", None),
        name=name,
        provider=provider,
        version=version,
        status=status,
    )


def publish_provider_version(
    client: TFEClient,
    organization: str,
    name: str,
    version: str,
    **kwargs: Any,
) -> PublishResult:
    """Publish a private provider version.

    Raises:
        CoreGap: Always. pytfe has no method that uploads provider SHA256SUMS,
            their signature, or platform binaries - only URL properties exist on
            the models - so this workflow cannot be built on the public API.
            Publishing a provider requires new methods in ``resources/``.

    Example:
        >>> publish_provider_version(client, "acme", "widget", "1.0.0")
        Traceback (most recent call last):
        pytfe.errors.CoreGap: ...
    """
    raise CoreGap("registry_provider_versions", "upload_shasums")


def no_code_provision(
    client: TFEClient,
    organization: str,
    *,
    no_code_module_id: str,
    workspace_name: str,
    project_id: str,
    variables: list[VariableSpec] | None = None,
    terraform_version: str | None = None,
    confirmed: bool = False,
    confirm: Callable[[Any], bool] | None = None,
    allow_destroy: bool = False,
    timeout: float = 1800,
    on_status: Callable[[Any], None] | None = None,
) -> RunResult:
    """Create a workspace from a no-code module and drive its first run.

    The workspace is created from the module, which queues a run automatically.
    That run is then treated exactly like any other: waited on, summarized, and
    gated before any apply.

    Args:
        client: The client to act through.
        organization: Organization that owns the module.
        no_code_module_id: The no-code module to provision from.
        workspace_name: Name for the new workspace.
        project_id: Project to create the workspace in.
        variables: Variables to set on the new workspace.
        terraform_version: Terraform version for the workspace.
        confirmed: The caller asserts a human approved the apply.
        confirm: Called with the plan summary; return True to apply.
        allow_destroy: Permit a destructive plan.
        timeout: Seconds to wait for the run.
        on_status: Called with the run on every poll.

    Returns:
        A :class:`~pytfe.workflows.models.RunResult`. Branch on ``.phase``.

    Raises:
        WorkflowError: If the module provisions no workspace or queues no run.
        TFEError: If the API rejects a call.

    Example:
        >>> no_code_provision(client, "acme", no_code_module_id="nocode-abc",
        ...                   workspace_name="team-sandbox", project_id="prj-1")
    """
    from ..models.run import RunListOptions
    from .runs import _finish, _gate, diagnose_run, plan_summary, wait_for_run

    started = time.monotonic()
    workspace = client.no_code_modules.create_workspace(
        no_code_module_id,
        NoCodeWorkspaceCreateOptions(
            name=workspace_name,
            project_id=project_id,
            terraform_version=terraform_version,
            vars=[
                NoCodeWorkspaceVariable(
                    key=spec.key,
                    value=spec.value,
                    category=spec.category,
                    hcl=spec.hcl,
                    sensitive=spec.sensitive,
                )
                for spec in (variables or [])
            ],
        ),
    )
    ws_id = workspace.id or ""
    if not ws_id:
        raise WorkflowError(
            "no-code module did not return a workspace",
            hint="Check that the module id is correct and the module is published.",
        )

    # Provisioning queues a run on its own; find it rather than creating another.
    runs = list(client.runs.list(ws_id, RunListOptions(page_size=1)))
    if not runs:
        raise WorkflowError(
            f"workspace {ws_id} was created but no run was queued",
            hint="Queue one with run_from_directory, or check the module's "
            "auto-queue settings.",
        )
    run_id = runs[0].id or ""

    planned = wait_for_run(
        client, run_id, until="plan_done", timeout=timeout, on_status=on_status
    )
    status = getattr(planned.status, "value", planned.status)
    if status in ("errored", "canceled", "discarded"):
        return RunResult(
            run_id=run_id,
            workspace_id=ws_id,
            phase="errored",
            status=status,
            ok=False,
            failure=diagnose_run(client, run_id),
            run=planned,
            duration_s=time.monotonic() - started,
        )

    summary = plan_summary(client, run_id)
    blocked = _gate(
        summary, confirmed=confirmed, confirm=confirm, allow_destroy=allow_destroy
    )
    if blocked:
        return RunResult(
            run_id=run_id,
            workspace_id=ws_id,
            phase=blocked,
            status=status,
            plan=summary,
            ok=blocked != "refused_destructive",
            run=planned,
            duration_s=time.monotonic() - started,
        )

    from ..models.run import RunApplyOptions

    client.runs.apply(run_id, RunApplyOptions(comment=None))
    final = wait_for_run(
        client, run_id, until="terminal", timeout=timeout, on_status=on_status
    )
    return _finish(client, final, summary, started)
