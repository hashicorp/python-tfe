# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Governance workflows: access, policy, run tasks, notifications, tokens, agents."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from ..client import TFEClient
from ..errors import TFEError
from ..models.agent import AgentPoolAssignToWorkspacesOptions, AgentTokenCreateOptions
from ..models.notification_configuration import (
    NotificationConfigurationCreateOptions,
    NotificationConfigurationUpdateOptions,
    NotificationDestinationType,
    NotificationTriggerType,
)
from ..models.policy_set import (
    PolicySetAddWorkspacesOptions,
    PolicySetCreateOptions,
    PolicySetUpdateOptions,
)
from ..models.project import ProjectCreateOptions
from ..models.run_task import (
    RunTaskCreateOptions,
    RunTaskUpdateOptions,
    Stage,
    TaskEnforcementLevel,
)
from ..models.run_trigger import RunTriggerCreateOptions
from ..models.team import TeamCreateOptions
from ..models.team_workspace_access import (
    TeamWorkspaceAccessAddOptions,
    TeamWorkspaceAccessType,
    TeamWorkspaceAccessUpdateOptions,
)
from ..models.workspace import Workspace
from ..models.workspace_run_task import (
    WorkspaceRunTaskCreateOptions,
    WorkspaceRunTaskUpdateOptions,
)
from ._poll import wait_until
from ._result import Change, EnsureResult
from .models import (
    AgentPoolSetup,
    EnsureVariablesResult,
    TokenAudit,
    TokenRow,
    VariableSpec,
)

logger = logging.getLogger("pytfe.workflows")

__all__ = [
    "onboard_team",
    "ensure_policy_set",
    "ensure_run_task",
    "ensure_notification",
    "ensure_run_trigger",
    "ensure_project",
    "setup_oidc_dynamic_credentials",
    "token_audit",
    "setup_agent_pool",
    "OIDC_VARIABLES",
]

#: Env-variable names per provider for HCP Terraform dynamic credentials.
#:
#: These are ordinary workspace environment variables, not the ``*_oidc_configurations``
#: resources - those are gated behind the HYOK entitlement, are four disjoint
#: namespaces with no ``list()``, and are a different feature. See
#: ``docs/scenarios/oidc-dynamic-credentials.md``.
OIDC_VARIABLES: dict[str, dict[str, str]] = {
    "aws": {
        "enable": "TFC_AWS_PROVIDER_AUTH",
        "role": "TFC_AWS_RUN_ROLE_ARN",
        "audience": "TFC_AWS_WORKLOAD_IDENTITY_AUDIENCE",
    },
    "gcp": {
        "enable": "TFC_GCP_PROVIDER_AUTH",
        "provider_name": "TFC_GCP_WORKLOAD_PROVIDER_NAME",
        "service_account_email": "TFC_GCP_RUN_SERVICE_ACCOUNT_EMAIL",
        "audience": "TFC_GCP_WORKLOAD_IDENTITY_AUDIENCE",
    },
    "azure": {
        "enable": "TFC_AZURE_PROVIDER_AUTH",
        "client_id": "TFC_AZURE_RUN_CLIENT_ID",
        "audience": "TFC_AZURE_WORKLOAD_IDENTITY_AUDIENCE",
    },
    "vault": {
        "enable": "TFC_VAULT_PROVIDER_AUTH",
        "addr": "TFC_VAULT_ADDR",
        "role": "TFC_VAULT_RUN_ROLE",
        "namespace": "TFC_VAULT_NAMESPACE",
        "audience": "TFC_VAULT_WORKLOAD_IDENTITY_AUDIENCE",
    },
}


def onboard_team(
    client: TFEClient,
    organization: str,
    team_name: str,
    *,
    members: list[str] | None = None,
    workspace_access: dict[str, str] | None = None,
    visibility: str | None = None,
    prune_members: bool = False,
    confirmed: bool = False,
    dry_run: bool = False,
) -> EnsureResult:
    """Create a team, add members, and grant workspace access.

    Idempotent. Members are added but never removed unless ``prune_members`` is
    set, which is destructive and requires ``confirmed=True`` - removing someone's
    access by accident is far worse than leaving a stale member.

    Args:
        client: The client to act through.
        organization: Organization that owns the team.
        team_name: Team name, used to find an existing team.
        members: Usernames to add to the team.
        workspace_access: ``{workspace_id: access_level}``, where the level is
            one of read, plan, write, admin.
        visibility: Team visibility (``"secret"`` or ``"organization"``).
        prune_members: Remove members not listed. Requires ``confirmed=True``.
        confirmed: Required for ``prune_members``.
        dry_run: Read only; report what would change.

    Returns:
        An :class:`~pytfe.workflows._result.EnsureResult`.

    Raises:
        TFEError: If the API rejects a write.

    Example:
        >>> onboard_team(client, "acme", "platform",
        ...              members=["alice", "bob"],
        ...              workspace_access={"ws-1": "write"})
    """
    team = next(
        (t for t in client.teams.list(organization) if t.name == team_name), None
    )
    changes: list[Change] = []

    if team is None:
        if dry_run:
            return EnsureResult(
                action="would_create",
                resource_type="teams",
                changes=[Change(field="name", before=None, after=team_name)],
            )
        team = client.teams.create(
            organization,
            TeamCreateOptions(name=team_name, visibility=visibility),
        )
        changes.append(Change(field="name", before=None, after=team_name))

    team_id = team.id or ""

    if members is not None:
        current = {u.username for u in client.teams.list_users(team_id) if u.username}
        to_add = sorted(set(members) - current)
        to_remove = sorted(current - set(members)) if prune_members else []

        if to_remove and not confirmed:
            return EnsureResult(
                action="awaiting_confirmation",
                resource_id=team_id,
                resource_type="teams",
                changes=changes,
                warnings=["prune_members=True would remove: " + ", ".join(to_remove)],
            )
        if to_add:
            changes.append(Change(field="members.added", before=None, after=to_add))
            if not dry_run:
                client.teams.add_users(team_id, to_add)
        if to_remove:
            changes.append(
                Change(field="members.removed", before=to_remove, after=None)
            )
            if not dry_run:
                client.teams.remove_users(team_id, to_remove)

    if workspace_access:
        for workspace_id, level in sorted(workspace_access.items()):
            existing = next(
                (
                    a
                    for a in client.team_workspace_accesses.list(workspace_id)
                    if getattr(getattr(a, "team", None), "id", None) == team_id
                ),
                None,
            )
            access = TeamWorkspaceAccessType(level)
            if existing is None:
                changes.append(
                    Change(field=f"access.{workspace_id}", before=None, after=level)
                )
                if not dry_run:
                    client.team_workspace_accesses.add(
                        TeamWorkspaceAccessAddOptions(
                            team_id=team_id,
                            workspace_id=workspace_id,
                            access=access,
                        )
                    )
            elif getattr(existing.access, "value", existing.access) != level:
                changes.append(
                    Change(
                        field=f"access.{workspace_id}",
                        before=getattr(existing.access, "value", existing.access),
                        after=level,
                    )
                )
                if not dry_run:
                    client.team_workspace_accesses.update(
                        existing.id or "",
                        TeamWorkspaceAccessUpdateOptions(access=access),
                    )

    if dry_run:
        return EnsureResult(
            action="would_update" if changes else "unchanged",
            resource_id=team_id,
            resource_type="teams",
            changes=changes,
        )
    return EnsureResult(
        action="updated" if changes else "unchanged",
        resource_id=team_id,
        resource_type="teams",
        changes=changes,
    )


def ensure_policy_set(
    client: TFEClient,
    organization: str,
    name: str,
    *,
    description: str | None = None,
    kind: str = "sentinel",
    global_: bool = False,
    workspace_ids: set[str] | None = None,
    dry_run: bool = False,
) -> EnsureResult:
    """Create a policy set, or converge an existing one.

    Args:
        client: The client to act through.
        organization: Organization that owns the set.
        name: Policy-set name, used to find an existing set.
        description: Set description.
        kind: ``"sentinel"``, ``"opa"`` or ``"tfpolicy"``.
        global_: Apply to every workspace in the organization.
        workspace_ids: Workspaces to attach. ``None`` leaves attachments alone.
        dry_run: Read only; report what would change.

    Returns:
        An :class:`~pytfe.workflows._result.EnsureResult`.

    Raises:
        TFEError: If the API rejects a write.

    Example:
        >>> ensure_policy_set(client, "acme", "guardrails",
        ...                   workspace_ids={"ws-1"})
    """
    from ..models.policy_types import PolicyKind

    existing = next(
        (p for p in client.policy_sets.list(organization) if p.name == name), None
    )
    changes: list[Change] = []

    if existing is None:
        if dry_run:
            return EnsureResult(
                action="would_create",
                resource_type="policy-sets",
                changes=[Change(field="name", before=None, after=name)],
            )
        existing = client.policy_sets.create(
            organization,
            PolicySetCreateOptions(
                name=name,
                description=description,
                # The field is `Global` with a capital G; its wire alias is `global`.
                Global=global_,
                kind=PolicyKind(kind),
            ),
        )
        changes.append(Change(field="name", before=None, after=name))
    else:
        updates: dict[str, Any] = {}
        if description is not None and existing.description != description:
            updates["description"] = description
            changes.append(
                Change(
                    field="description", before=existing.description, after=description
                )
            )
        if updates and not dry_run:
            client.policy_sets.update(
                existing.id or "", PolicySetUpdateOptions(**updates)
            )

    set_id = existing.id or ""
    if workspace_ids:
        changes.append(
            Change(field="workspaces", before=None, after=sorted(workspace_ids))
        )
        if not dry_run:
            client.policy_sets.add_workspaces(
                set_id,
                PolicySetAddWorkspacesOptions(
                    workspaces=[Workspace(id=i) for i in sorted(workspace_ids)]
                ),
            )

    action = "would_update" if dry_run else "updated"
    return EnsureResult(
        action=action if changes else "unchanged",
        resource_id=set_id,
        resource_type="policy-sets",
        changes=changes,
    )


def ensure_run_task(
    client: TFEClient,
    organization: str,
    name: str,
    *,
    url: str,
    category: str = "task",
    hmac_key: str | None = None,
    enabled: bool = True,
    description: str | None = None,
    workspace_ids: dict[str, str] | None = None,
    stage: str = "post_plan",
    dry_run: bool = False,
) -> EnsureResult:
    """Create an organization run task and attach it to workspaces.

    Args:
        client: The client to act through.
        organization: Organization that owns the task.
        name: Run-task name, used to find an existing task.
        url: Endpoint the task calls.
        category: Task category, normally ``"task"``.
        hmac_key: Shared secret. Never logged or echoed in the result.
        enabled: Whether the task is active.
        description: Task description.
        workspace_ids: ``{workspace_id: enforcement_level}`` where the level is
            ``"advisory"`` or ``"mandatory"``.
        stage: Run stage to attach at.
        dry_run: Read only; report what would change.

    Returns:
        An :class:`~pytfe.workflows._result.EnsureResult`.

    Raises:
        TFEError: If the API rejects a write.

    Example:
        >>> ensure_run_task(client, "acme", "scanner",
        ...                 url="https://scan.example.com/hook",
        ...                 workspace_ids={"ws-1": "mandatory"})
    """
    existing = next(
        (t for t in client.run_tasks.list(organization) if t.name == name), None
    )
    changes: list[Change] = []

    if existing is None:
        if dry_run:
            return EnsureResult(
                action="would_create",
                resource_type="tasks",
                changes=[Change(field="name", before=None, after=name)],
            )
        existing = client.run_tasks.create(
            organization,
            RunTaskCreateOptions(
                name=name,
                url=url,
                category=category,
                hmac_key=hmac_key,
                enabled=enabled,
                description=description,
            ),
        )
        changes.append(Change(field="name", before=None, after=name))
    else:
        updates: dict[str, Any] = {}
        if existing.url != url:
            updates["url"] = url
            changes.append(Change(field="url", before=existing.url, after=url))
        if bool(existing.enabled) != enabled:
            updates["enabled"] = enabled
            changes.append(
                Change(field="enabled", before=existing.enabled, after=enabled)
            )
        if hmac_key is not None:
            updates["hmac_key"] = hmac_key
            changes.append(Change.redacted("hmac_key"))
        if updates and not dry_run:
            client.run_tasks.update(existing.id or "", RunTaskUpdateOptions(**updates))

    task_id = existing.id or ""
    if workspace_ids:
        for workspace_id, level in sorted(workspace_ids.items()):
            attached = next(
                (
                    w
                    for w in client.workspace_run_tasks.list(workspace_id)
                    if getattr(getattr(w, "run_task", None), "id", None) == task_id
                ),
                None,
            )
            enforcement = TaskEnforcementLevel(level)
            if attached is None:
                changes.append(
                    Change(field=f"attach.{workspace_id}", before=None, after=level)
                )
                if not dry_run:
                    client.workspace_run_tasks.create(
                        workspace_id,
                        WorkspaceRunTaskCreateOptions(
                            enforcement_level=enforcement,
                            run_task=existing,
                            stages=[Stage(stage)],
                        ),
                    )
            elif (
                getattr(attached.enforcement_level, "value", attached.enforcement_level)
                != level
            ):
                changes.append(
                    Change(
                        field=f"attach.{workspace_id}",
                        before=getattr(
                            attached.enforcement_level,
                            "value",
                            attached.enforcement_level,
                        ),
                        after=level,
                    )
                )
                if not dry_run:
                    client.workspace_run_tasks.update(
                        workspace_id,
                        attached.id or "",
                        WorkspaceRunTaskUpdateOptions(enforcement_level=enforcement),
                    )

    action = "would_update" if dry_run else "updated"
    return EnsureResult(
        action=action if changes else "unchanged",
        resource_id=task_id,
        resource_type="tasks",
        changes=changes,
    )


def ensure_notification(
    client: TFEClient,
    workspace_id: str,
    name: str,
    *,
    destination_type: str,
    url: str | None = None,
    email_addresses: list[str] | None = None,
    triggers: list[str] | None = None,
    enabled: bool = True,
    token: str | None = None,
    dry_run: bool = False,
) -> EnsureResult:
    """Create a workspace notification configuration, or converge one.

    Note:
        ``url`` and ``token`` are never logged, because a webhook URL routinely
        embeds a secret.

    Args:
        client: The client to act through.
        workspace_id: Workspace the notification belongs to.
        name: Configuration name, used to find an existing one.
        destination_type: ``email``, ``generic``, ``slack`` or ``microsoft-teams``.
        url: Webhook URL, for non-email destinations.
        email_addresses: Recipients, for the email destination.
        triggers: Trigger names, e.g. ``["run:errored", "run:completed"]``.
        enabled: Whether the configuration is active.
        token: Shared secret for generic webhooks.
        dry_run: Read only; report what would change.

    Returns:
        An :class:`~pytfe.workflows._result.EnsureResult`.

    Raises:
        TFEError: If the API rejects a write.

    Example:
        >>> ensure_notification(client, "ws-1", "oncall",
        ...                     destination_type="slack",
        ...                     url="https://hooks.slack.com/services/...",
        ...                     triggers=["run:errored"])
    """
    existing = next(
        (
            n
            for n in client.notification_configurations.list(workspace_id)
            if n.name == name
        ),
        None,
    )
    trigger_values = [NotificationTriggerType(t) for t in (triggers or [])]
    destination = NotificationDestinationType(destination_type)
    changes: list[Change] = []

    if existing is None:
        if dry_run:
            return EnsureResult(
                action="would_create",
                resource_type="notification-configurations",
                changes=[Change(field="name", before=None, after=name)],
            )
        created = client.notification_configurations.create(
            workspace_id,
            NotificationConfigurationCreateOptions(
                name=name,
                destination_type=destination,
                enabled=enabled,
                url=url,
                token=token,
                triggers=trigger_values,
                email_addresses=email_addresses or [],
            ),
        )
        return EnsureResult(
            action="created",
            resource_id=created.id,
            resource_type="notification-configurations",
            changes=[Change(field="name", before=None, after=name)],
        )

    updates: dict[str, Any] = {}
    if bool(existing.enabled) != enabled:
        updates["enabled"] = enabled
        changes.append(Change(field="enabled", before=existing.enabled, after=enabled))
    current_triggers = [
        getattr(t, "value", t) for t in (getattr(existing, "triggers", None) or [])
    ]
    if triggers is not None and sorted(current_triggers) != sorted(triggers):
        updates["triggers"] = trigger_values
        changes.append(
            Change(field="triggers", before=current_triggers, after=triggers)
        )
    if url is not None and existing.url != url:
        updates["url"] = url
        # The URL can embed a secret, so the value is not recorded.
        changes.append(Change.redacted("url"))

    if updates and not dry_run:
        client.notification_configurations.update(
            existing.id or "", NotificationConfigurationUpdateOptions(**updates)
        )

    action = "would_update" if dry_run else "updated"
    return EnsureResult(
        action=action if changes else "unchanged",
        resource_id=existing.id,
        resource_type="notification-configurations",
        changes=changes,
    )


def ensure_run_trigger(
    client: TFEClient,
    workspace_id: str,
    *,
    source_workspace_ids: set[str],
    prune: bool = False,
    confirmed: bool = False,
    dry_run: bool = False,
) -> EnsureResult:
    """Converge the inbound run triggers on a workspace.

    A run trigger makes this workspace queue a run when one of the source
    workspaces finishes an apply.

    Args:
        client: The client to act through.
        workspace_id: The workspace that will be triggered.
        source_workspace_ids: Workspaces whose applies should trigger it.
        prune: Remove triggers not in the desired set. Requires ``confirmed=True``.
        confirmed: Required for ``prune``.
        dry_run: Read only; report what would change.

    Returns:
        An :class:`~pytfe.workflows._result.EnsureResult`.

    Raises:
        TFEError: If the API rejects a write.

    Example:
        >>> ensure_run_trigger(client, "ws-app", source_workspace_ids={"ws-network"})
    """
    from ..models.run_trigger import RunTriggerFilterOp, RunTriggerListOptions

    # run_trigger_type is a required field on the list options.
    existing = list(
        client.run_triggers.list(
            workspace_id,
            RunTriggerListOptions(
                run_trigger_type=RunTriggerFilterOp.RUN_TRIGGER_INBOUND
            ),
        )
    )
    current = {getattr(getattr(t, "sourceable", None), "id", None): t for t in existing}
    changes: list[Change] = []

    to_add = sorted(source_workspace_ids - set(current))
    for source_id in to_add:
        changes.append(Change(field="trigger.added", before=None, after=source_id))
        if not dry_run:
            client.run_triggers.create(
                workspace_id,
                RunTriggerCreateOptions(sourceable=Workspace(id=source_id)),
            )

    if prune:
        to_remove = [
            (source_id, trigger)
            for source_id, trigger in current.items()
            if source_id not in source_workspace_ids
        ]
        if to_remove and not confirmed:
            return EnsureResult(
                action="awaiting_confirmation",
                resource_id=workspace_id,
                resource_type="run-triggers",
                changes=changes,
                warnings=[
                    "prune=True would remove triggers from: "
                    + ", ".join(sorted(str(s) for s, _ in to_remove))
                ],
            )
        for stale_id, trigger in to_remove:
            changes.append(Change(field="trigger.removed", before=stale_id, after=None))
            if not dry_run:
                client.run_triggers.delete(trigger.id or "")

    action = "would_update" if dry_run else "updated"
    return EnsureResult(
        action=action if changes else "unchanged",
        resource_id=workspace_id,
        resource_type="run-triggers",
        changes=changes,
    )


def ensure_project(
    client: TFEClient,
    organization: str,
    name: str,
    *,
    description: str | None = None,
    workspace_ids: set[str] | None = None,
    dry_run: bool = False,
) -> EnsureResult:
    """Create a project, or converge one, and move workspaces into it.

    Args:
        client: The client to act through.
        organization: Organization that owns the project.
        name: Project name, used to find an existing project.
        description: Project description.
        workspace_ids: Workspaces to move into the project.
        dry_run: Read only; report what would change.

    Returns:
        An :class:`~pytfe.workflows._result.EnsureResult`.

    Raises:
        TFEError: If the API rejects a write.

    Example:
        >>> ensure_project(client, "acme", "platform", workspace_ids={"ws-1"})
    """
    from ..models.project import ProjectUpdateOptions

    existing = next(
        (p for p in client.projects.list(organization) if p.name == name), None
    )
    changes: list[Change] = []

    if existing is None:
        if dry_run:
            return EnsureResult(
                action="would_create",
                resource_type="projects",
                changes=[Change(field="name", before=None, after=name)],
            )
        existing = client.projects.create(
            organization, ProjectCreateOptions(name=name, description=description)
        )
        changes.append(Change(field="name", before=None, after=name))
    elif description is not None and existing.description != description:
        changes.append(
            Change(field="description", before=existing.description, after=description)
        )
        if not dry_run:
            client.projects.update(
                existing.id or "", ProjectUpdateOptions(description=description)
            )

    project_id = existing.id or ""
    if workspace_ids:
        changes.append(
            Change(field="workspaces", before=None, after=sorted(workspace_ids))
        )
        if not dry_run:
            client.projects.move_workspaces(project_id, sorted(workspace_ids))

    action = "would_update" if dry_run else "updated"
    return EnsureResult(
        action=action if changes else "unchanged",
        resource_id=project_id,
        resource_type="projects",
        changes=changes,
    )


def setup_oidc_dynamic_credentials(
    client: TFEClient,
    workspace_id: str,
    *,
    provider: Literal["aws", "gcp", "azure", "vault"],
    dry_run: bool = False,
    **provider_kwargs: str,
) -> EnsureVariablesResult:
    """Configure dynamic provider credentials on a workspace.

    Writes the documented ``TFC_*_PROVIDER_AUTH`` environment variables, which is
    how standard-tier dynamic credentials work.

    Note:
        This deliberately does *not* use the ``*_oidc_configurations`` resources.
        Those are four disjoint namespaces gated behind the HYOK entitlement,
        none of which exposes ``list()``, so they cannot back an idempotent
        single-entry-point workflow. See
        ``docs/scenarios/oidc-dynamic-credentials.md``.

    Args:
        client: The client to act through.
        workspace_id: Workspace to configure.
        provider: Which cloud provider to configure.
        dry_run: Read only; report what would change.
        **provider_kwargs: Provider-specific settings. Keys are the logical
            names in :data:`OIDC_VARIABLES` - for AWS, ``role`` and optionally
            ``audience``.

    Returns:
        An :class:`~pytfe.workflows.models.EnsureVariablesResult`.

    Raises:
        ValueError: If the provider is unknown or a required setting is missing.
        TFEError: If the API rejects a write.

    Example:
        >>> setup_oidc_dynamic_credentials(
        ...     client, "ws-1", provider="aws",
        ...     role="arn:aws:iam::123456789012:role/tfc")
    """
    from .workspaces import ensure_variables

    mapping = OIDC_VARIABLES.get(provider)
    if mapping is None:
        raise ValueError(
            f"unknown provider {provider!r}; expected one of "
            + ", ".join(sorted(OIDC_VARIABLES))
        )

    unknown = sorted(set(provider_kwargs) - set(mapping) - {"enable"})
    if unknown:
        raise ValueError(
            f"unknown setting(s) for {provider}: {', '.join(unknown)}. "
            f"Valid settings: {', '.join(sorted(k for k in mapping if k != 'enable'))}"
        )

    specs = [
        VariableSpec(
            key=mapping["enable"],
            value="true",
            category="env",
            description="Enables dynamic provider credentials",
        )
    ]
    for logical, value in sorted(provider_kwargs.items()):
        specs.append(VariableSpec(key=mapping[logical], value=value, category="env"))
    return ensure_variables(client, workspace_id, specs, dry_run=dry_run)


def token_audit(
    client: TFEClient, organization: str, *, expiring_within_days: int = 30
) -> TokenAudit:
    """Report every API token this credential can enumerate, and when it expires.

    Token values are never returned.

    Note:
        User API tokens are not included: ``client.users`` exposes only
        ``read``/``read_current``/``update_current``, and pytfe has no user-token
        namespace, so they cannot be enumerated through this SDK.

    Args:
        client: The client to read through.
        organization: Organization to audit.
        expiring_within_days: Flag tokens expiring inside this window.

    Returns:
        A :class:`~pytfe.workflows.models.TokenAudit`.

    Raises:
        TFEError: If the organization cannot be read.

    Example:
        >>> audit = token_audit(client, "acme")
        >>> audit.summary()["expiring"]
        []
    """
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=expiring_within_days)
    result = TokenAudit(
        organization=organization, expiring_within_days=expiring_within_days
    )

    def add(
        kind: Literal["organization", "team", "agent"],
        obj: Any,
        owner: str | None,
    ) -> None:
        expires = getattr(obj, "expired_at", None)
        if expires is not None and expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        result.tokens.append(
            TokenRow(
                id=getattr(obj, "id", None),
                kind=kind,
                owner=owner,
                description=getattr(obj, "description", None),
                created_at=getattr(obj, "created_at", None),
                expired_at=expires,
                last_used_at=getattr(obj, "last_used_at", None),
                expired=bool(expires and expires <= now),
                expiring=bool(expires and now < expires <= horizon),
            )
        )

    try:
        add("organization", client.organization_tokens.read(organization), organization)
    except TFEError as exc:
        result.warnings.append(f"organization token unavailable: {exc}")

    try:
        for team_token in client.team_tokens.list(organization):
            add(
                "team",
                team_token,
                getattr(getattr(team_token, "team", None), "id", None),
            )
    except TFEError as exc:
        result.warnings.append(f"team tokens unavailable: {exc}")

    try:
        for pool in client.agent_pools.list(organization):
            for agent_token in client.agent_tokens.list(pool.id or ""):
                add("agent", agent_token, pool.name)
    except TFEError as exc:
        result.warnings.append(f"agent tokens unavailable: {exc}")

    result.warnings.append(
        "user API tokens are not included: the SDK exposes no user-token namespace"
    )
    return result


def setup_agent_pool(
    client: TFEClient,
    organization: str,
    name: str,
    *,
    workspace_ids: set[str] | None = None,
    create_token: bool = True,
    token_description: str = "Created by pytfe.workflows",
    wait_for_agent: float = 0,
    dry_run: bool = False,
) -> AgentPoolSetup:
    """Create an agent pool, issue a token, and assign workspaces.

    Note:
        The agent token value is shown by the API exactly once, at creation. It
        is returned on the result as ``token`` and deliberately excluded from
        ``summary()``. Store it immediately; it cannot be retrieved again.

    Args:
        client: The client to act through.
        organization: Organization that owns the pool.
        name: Pool name, used to find an existing pool.
        workspace_ids: Workspaces to assign to the pool.
        create_token: Issue a new agent token.
        token_description: Description recorded on the token.
        wait_for_agent: Seconds to wait for an agent to connect. ``0`` skips.
        dry_run: Read only; report what would change.

    Returns:
        An :class:`~pytfe.workflows.models.AgentPoolSetup`.

    Raises:
        WorkflowTimeout: If ``wait_for_agent`` elapses with no agent connected.
        TFEError: If the API rejects a write.

    Example:
        >>> setup = setup_agent_pool(client, "acme", "runners",
        ...                          workspace_ids={"ws-1"})
        >>> setup.token   # store this now; it is never shown again
    """
    from ..models.agent import AgentPoolCreateOptions

    existing = next(
        (p for p in client.agent_pools.list(organization) if p.name == name), None
    )
    result = AgentPoolSetup(name=name)

    if existing is None:
        if dry_run:
            result.action = "would_create"
            return result
        existing = client.agent_pools.create(
            organization, AgentPoolCreateOptions(name=name)
        )
        result.action = "created"
    else:
        result.action = "unchanged"

    pool_id = existing.id or ""
    result.agent_pool_id = pool_id

    if create_token and not dry_run:
        token = client.agent_tokens.create(
            pool_id, AgentTokenCreateOptions(description=token_description)
        )
        result.token = getattr(token, "token", None)
        result.token_id = token.id
        if result.action == "unchanged":
            result.action = "updated"

    if workspace_ids:
        result.assigned_workspace_ids = sorted(workspace_ids)
        if not dry_run:
            client.agent_pools.assign_to_workspaces(
                pool_id,
                AgentPoolAssignToWorkspacesOptions(workspace_ids=sorted(workspace_ids)),
            )
            if result.action == "unchanged":
                result.action = "updated"

    if wait_for_agent > 0 and not dry_run:
        agents = wait_until(
            lambda: list(client.agents.list(pool_id)),
            lambda found: any(
                getattr(a, "status", None) in ("idle", "busy") for a in found
            ),
            timeout=wait_for_agent,
            interval=2.0,
            description=f"an agent to connect to pool {name}",
        )
        result.agent_connected = bool(agents)
    return result
