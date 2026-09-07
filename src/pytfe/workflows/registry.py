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
from ..errors import NotFound, WorkflowError
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
from ..models.registry_provider import (
    RegistryProviderCreateOptions,
    RegistryProviderID,
)
from ..models.registry_provider_platform import (
    RegistryProviderPlatformCreateOptions,
)
from ..models.registry_provider_version import (
    RegistryProviderVersionCreateOptions,
    RegistryProviderVersionID,
)
from ._package import package_directory
from ._poll import wait_until
from .models import (
    ProviderPlatformSpec,
    PublishResult,
    RunResult,
    VariableSpec,
)

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
    *,
    gpg_key_id: str,
    shasums: bytes,
    shasums_sig: bytes,
    platforms: list[ProviderPlatformSpec],
    namespace: str | None = None,
    protocols: list[str] | None = None,
    registry_name: str = "private",
) -> PublishResult:
    """Publish a private provider version, with its checksums and binaries.

    The full sequence the private provider registry requires: find-or-create the
    provider, create the version, upload ``SHA256SUMS`` and its detached
    signature, then create and upload every platform binary. Idempotent - a
    version that already exists is reported as ``unchanged`` and nothing is
    re-uploaded.

    The GPG key identified by ``gpg_key_id`` must already be registered with the
    organization, and must be the key that signed ``shasums_sig``.

    Args:
        client: The client to act through.
        organization: Organization that owns the provider.
        name: Provider name, without the ``terraform-provider-`` prefix.
        version: Semantic version to publish.
        gpg_key_id: ID of the registered GPG key that signed the checksums.
        shasums: Contents of the ``SHA256SUMS`` file.
        shasums_sig: Contents of the ``SHA256SUMS.sig`` detached signature.
        platforms: One spec per OS/arch build. See
            :meth:`~pytfe.workflows.models.ProviderPlatformSpec.from_release_dir`
            for building these from a goreleaser output directory.
        namespace: Registry namespace. Defaults to ``organization``, which is
            what the private registry requires.
        protocols: Terraform protocol versions the provider implements.
            Defaults to ``["5.0"]``.
        registry_name: ``"private"`` or ``"public"``.

    Returns:
        A :class:`~pytfe.workflows.models.PublishResult`. ``warnings`` records
        any platform the registry did not confirm as uploaded.

    Raises:
        ValueError: If ``platforms`` is empty or a spec has no binary.
        TFEError: If the API rejects a call or an upload fails.

    Example:
        >>> from pathlib import Path
        >>> from pytfe.workflows import ProviderPlatformSpec
        >>> shasums = Path("dist/terraform-provider-widget_1.0.0_SHA256SUMS").read_bytes()
        >>> publish_provider_version(
        ...     client, "acme", "widget", "1.0.0",
        ...     gpg_key_id="32966F3FB5AC1129",
        ...     shasums=shasums,
        ...     shasums_sig=Path("dist/…_SHA256SUMS.sig").read_bytes(),
        ...     platforms=ProviderPlatformSpec.from_release_dir("dist", shasums=shasums),
        ... )
    """
    if not platforms:
        raise ValueError(
            "platforms must not be empty; a provider version with no platform "
            "binaries is unusable"
        )

    provider_namespace = namespace or organization
    registry = RegistryName(registry_name)
    provider_id = RegistryProviderID(
        organization_name=organization,
        registry_name=registry,
        namespace=provider_namespace,
        name=name,
    )

    try:
        client.registry_providers.read(provider_id)
    except NotFound:
        logger.info("creating registry provider %s/%s", provider_namespace, name)
        client.registry_providers.create(
            organization,
            RegistryProviderCreateOptions(
                name=name, namespace=provider_namespace, registry_name=registry
            ),
        )

    existing = {v.version for v in client.registry_provider_versions.list(provider_id)}
    if version in existing:
        return PublishResult(
            action="unchanged",
            name=name,
            version=version,
            warnings=[f"version {version} already exists; nothing was uploaded"],
        )

    created = client.registry_provider_versions.create(
        provider_id,
        RegistryProviderVersionCreateOptions(
            version=version, key_id=gpg_key_id, protocols=protocols or ["5.0"]
        ),
    )
    logger.info("uploading checksums for %s %s", name, version)
    client.registry_provider_versions.upload_shasums(created, shasums)
    client.registry_provider_versions.upload_shasums_sig(created, shasums_sig)

    version_id = RegistryProviderVersionID(
        organization_name=organization,
        registry_name=registry,
        namespace=provider_namespace,
        name=name,
        version=version,
    )

    result = PublishResult(action="published", name=name, version=version)
    for spec in platforms:
        logger.info("uploading %s_%s binary", spec.os, spec.arch)
        platform = client.registry_provider_platforms.create(
            version_id,
            RegistryProviderPlatformCreateOptions(
                os=spec.os,
                arch=spec.arch,
                shasum=spec.shasum,
                filename=spec.filename,
            ),
        )
        client.registry_provider_platforms.upload_binary(platform, spec.read_binary())

    final = client.registry_provider_versions.read(version_id)
    result.module_id = final.id
    result.status = "published"
    if not final.shasums_uploaded:
        result.warnings.append("the registry has not confirmed the SHA256SUMS upload")
    if not final.shasums_sig_uploaded:
        result.warnings.append("the registry has not confirmed the signature upload")
    result.ok = not result.warnings
    return result


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
