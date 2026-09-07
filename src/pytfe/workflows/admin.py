# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Terraform Enterprise-only workflows.

Every workflow here refuses to run against HCP Terraform, where the admin API
does not exist.
"""

from __future__ import annotations

import logging
from typing import Any

from ..client import TFEClient
from ..errors import TFEError, UnsupportedInCloud
from ..models.organization import OrganizationCreateOptions
from ._result import Change, EnsureResult
from .models import TFEHealth

logger = logging.getLogger("pytfe.workflows")

__all__ = ["admin_bootstrap", "identity_bootstrap", "tfe_health", "is_hcp_terraform"]

#: Hostnames that identify HCP Terraform rather than a self-hosted instance.
_HCP_HOSTS = ("app.terraform.io", "app.eu.terraform.io")


def is_hcp_terraform(client: TFEClient) -> bool:
    """True when the client points at HCP Terraform rather than Terraform Enterprise."""
    address = (client.config.address or "").lower()
    return any(host in address for host in _HCP_HOSTS)


def _require_enterprise(client: TFEClient, workflow: str) -> None:
    if is_hcp_terraform(client):
        raise UnsupportedInCloud(
            f"{workflow} is Terraform Enterprise only; "
            f"{client.config.address} is HCP Terraform",
            hint=(
                "The site admin API exists only on self-hosted Terraform "
                "Enterprise. Use the organization-level workflows instead."
            ),
        )


def admin_bootstrap(
    client: TFEClient,
    *,
    organization_name: str,
    organization_email: str,
    email_enabled: bool | None = None,
    smtp_settings: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> EnsureResult:
    """Create the first organization on a Terraform Enterprise instance.

    Terraform Enterprise only.

    Note:
        The admin API has no organization-create endpoint - ``admin.organizations``
        exposes only list, read, update and delete - so the organization is
        created through the normal organizations endpoint, and admin settings are
        applied afterwards.

    Args:
        client: The client to act through.
        organization_name: Name for the organization.
        organization_email: Owner email for the organization.
        email_enabled: Toggle SMTP delivery in the instance's SMTP settings.
        smtp_settings: Additional SMTP settings to apply.
        dry_run: Read only; report what would change.

    Returns:
        An :class:`~pytfe.workflows._result.EnsureResult`.

    Raises:
        UnsupportedInCloud: If the client points at HCP Terraform.
        TFEError: If the API rejects a write.

    Example:
        >>> admin_bootstrap(client, organization_name="acme",
        ...                 organization_email="ops@example.com")
    """
    _require_enterprise(client, "admin_bootstrap")

    existing = next(
        (o for o in client.organizations.list() if o.name == organization_name), None
    )
    changes: list[Change] = []

    if existing is None:
        if dry_run:
            return EnsureResult(
                action="would_create",
                resource_type="organizations",
                changes=[Change(field="name", before=None, after=organization_name)],
            )
        created = client.organizations.create(
            OrganizationCreateOptions(name=organization_name, email=organization_email)
        )
        changes.append(Change(field="name", before=None, after=organization_name))
        resource_id = created.name
        action = "created"
    else:
        resource_id = existing.name
        action = "unchanged"

    if smtp_settings or email_enabled is not None:
        payload = dict(smtp_settings or {})
        if email_enabled is not None:
            payload["enabled"] = email_enabled
        changes.append(
            Change(field="smtp_settings", before=None, after=sorted(payload))
        )
        if not dry_run:
            try:
                client.admin.smtp_settings.update(payload)  # type: ignore[arg-type]
            except (TFEError, TypeError) as exc:
                # SMTP settings take a typed options model that varies by TFE
                # release; surface rather than guess.
                return EnsureResult(
                    action="updated" if changes else "unchanged",
                    resource_id=resource_id,
                    resource_type="organizations",
                    changes=changes,
                    ok=False,
                    warnings=[
                        f"organization ready, but SMTP settings were not applied: {exc}"
                    ],
                )

    if dry_run:
        return EnsureResult(
            action="would_update" if changes else "unchanged",
            resource_id=resource_id,
            resource_type="organizations",
            changes=changes,
        )
    return EnsureResult(
        action=action
        if action == "created"
        else ("updated" if changes else "unchanged"),
        resource_id=resource_id,
        resource_type="organizations",
        changes=changes,
    )


def identity_bootstrap(
    client: TFEClient,
    *,
    saml_settings: dict[str, Any] | None = None,
    scim_enabled: bool | None = None,
    dry_run: bool = False,
) -> EnsureResult:
    """Configure SSO and SCIM on a Terraform Enterprise instance.

    Terraform Enterprise only.

    Args:
        client: The client to act through.
        saml_settings: SAML settings to apply.
        scim_enabled: Toggle SCIM provisioning.
        dry_run: Read only; report what would change.

    Returns:
        An :class:`~pytfe.workflows._result.EnsureResult`.

    Raises:
        UnsupportedInCloud: If the client points at HCP Terraform.
        TFEError: If the API rejects a write.

    Example:
        >>> identity_bootstrap(client, scim_enabled=True)
    """
    _require_enterprise(client, "identity_bootstrap")
    changes: list[Change] = []
    warnings: list[str] = []

    if saml_settings:
        changes.append(
            Change(field="saml_settings", before=None, after=sorted(saml_settings))
        )
        if not dry_run:
            try:
                client.admin.saml_settings.update(saml_settings)  # type: ignore[arg-type]
            except (TFEError, TypeError) as exc:
                warnings.append(f"SAML settings not applied: {exc}")

    if scim_enabled is not None:
        changes.append(Change(field="scim.enabled", before=None, after=scim_enabled))
        if not dry_run:
            try:
                client.admin.scim_settings.update({"enabled": scim_enabled})  # type: ignore[arg-type]
            except (TFEError, TypeError) as exc:
                warnings.append(f"SCIM settings not applied: {exc}")

    action = "would_update" if dry_run else "updated"
    return EnsureResult(
        action=action if changes else "unchanged",
        resource_type="admin-settings",
        changes=changes,
        ok=not warnings,
        warnings=warnings,
    )


def tfe_health(client: TFEClient, *, max_runs: int = 500) -> TFEHealth:
    """Summarize a Terraform Enterprise instance's size and run-queue pressure.

    Terraform Enterprise only.

    Note:
        There is no health or ping endpoint in the API, and ``client.admin``
        exposes no general-settings namespace. This composes a summary from the
        admin endpoints that do exist, so it reports reachability and queue
        pressure rather than a server-reported health status.

    Args:
        client: The client to read through.
        max_runs: Cap on runs enumerated when measuring the queue.

    Returns:
        A :class:`~pytfe.workflows.models.TFEHealth`.

    Raises:
        UnsupportedInCloud: If the client points at HCP Terraform.

    Example:
        >>> health = tfe_health(client)
        >>> health.run_queue_depth
        3
    """
    _require_enterprise(client, "tfe_health")
    result = TFEHealth()

    try:
        result.organization_count = sum(1 for _ in client.admin.organizations.list())
        result.reachable = True
    except TFEError as exc:
        result.warnings.append(f"organizations unavailable: {exc}")
        result.ok = False

    try:
        result.user_count = sum(1 for _ in client.admin.users.list())
    except TFEError as exc:
        result.warnings.append(f"users unavailable: {exc}")

    try:
        queued = 0
        for index, run in enumerate(client.admin.runs.list()):
            if index >= max_runs:
                result.warnings.append(
                    f"stopped counting runs at {max_runs}; the queue may be deeper"
                )
                break
            status = getattr(run.status, "value", getattr(run, "status", None))
            if status:
                result.runs_by_status[status] = result.runs_by_status.get(status, 0) + 1
            if status in ("pending", "plan_queued", "apply_queued", "queuing"):
                queued += 1
        result.run_queue_depth = queued
    except TFEError as exc:
        result.warnings.append(f"run queue unavailable: {exc}")

    try:
        result.terraform_versions = sum(
            1 for _ in client.admin.terraform_versions.list()
        )
    except TFEError as exc:
        result.warnings.append(f"terraform versions unavailable: {exc}")

    return result
