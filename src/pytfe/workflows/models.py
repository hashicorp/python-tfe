# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Concrete result and input models for the workflow layer.

Input (``*Spec``) models set ``extra="forbid"``: a mistyped field name must fail
loudly. This is not paranoia - ``WorkspaceCreateOptions`` and friends default to
``extra="ignore"``, so ``WorkspaceCreateOptions(project_id="prj-1")`` silently
discards the value and creates a workspace with no project. Every ``*Spec``
below is mapped field-by-field onto the real options model by its workflow.

Result models embed SDK resource models (``run: Run``) rather than re-flattening
them, so callers keep ``.relationships`` and ``.related()``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..models.run import Run
from ._result import SENSITIVE, Change, EnsureResult, Kind, WorkflowResult

__all__ = [
    "VCSRepoSpec",
    "WorkspaceSpec",
    "VariableSpec",
    "WorkspaceSummary",
    "WorkspaceList",
    "WorkspaceStatus",
    "PlanSummary",
    "PolicyResult",
    "RunFailure",
    "RunResult",
    "Outputs",
    "EnsureVariablesResult",
    "RunPhaseName",
    "StateDownload",
    "ResourceRow",
    "StateInventory",
    "PushStateResult",
    "LockResult",
    "CloneResult",
    "TeardownResult",
    "FleetItem",
    "FleetResult",
    "OrgInventory",
    "ResourceInventory",
    "TokenRow",
    "TokenAudit",
    "AgentPoolSetup",
    "PublishResult",
    "TFEHealth",
]

RunPhaseName = Literal[
    "planned",
    "no_changes",
    "awaiting_confirmation",
    "awaiting_policy_override",
    "refused_destructive",
    "rejected",
    "applied",
    "errored",
]


class _Spec(BaseModel):
    """Base for caller-supplied inputs: unknown fields are an error."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="forbid"
    )


class VCSRepoSpec(_Spec):
    """VCS attachment for a workspace."""

    identifier: str
    branch: str | None = None
    oauth_token_id: str | None = None
    github_app_installation_id: str | None = None
    ingress_submodules: bool = False


class WorkspaceSpec(_Spec):
    """Desired workspace settings.

    Field semantics follow ``model_fields_set``: a field left unset is
    *unmanaged* and never touched; a field set explicitly to ``None`` is
    cleared. So ``WorkspaceSpec()`` changes nothing, while
    ``WorkspaceSpec(vcs_repo=None)`` detaches VCS.
    """

    description: str | None = None
    project_id: str | None = None
    execution_mode: str | None = None
    agent_pool_id: str | None = None
    terraform_version: str | None = None
    working_directory: str | None = None
    auto_apply: bool | None = None
    queue_all_runs: bool | None = None
    speculative_enabled: bool | None = None
    file_triggers_enabled: bool | None = None
    trigger_prefixes: list[str] | None = None
    trigger_patterns: list[str] | None = None
    allow_destroy_plan: bool | None = None
    assessments_enabled: bool | None = None
    global_remote_state: bool | None = None
    source_name: str | None = None
    source_url: str | None = None
    tags: set[str] | None = None
    vcs_repo: VCSRepoSpec | None = None


class VariableSpec(_Spec):
    """One workspace or variable-set variable."""

    key: str
    value: str
    category: Literal["terraform", "env"] = "terraform"
    hcl: bool = False
    sensitive: bool = False
    description: str | None = None

    @classmethod
    def from_dict(
        cls,
        mapping: dict[str, str],
        *,
        category: Literal["terraform", "env"] = "terraform",
        sensitive: bool = False,
    ) -> list[VariableSpec]:
        """Build specs from a plain ``{key: value}`` mapping."""
        return [
            cls(key=k, value=v, category=category, sensitive=sensitive)
            for k, v in mapping.items()
        ]

    @classmethod
    def from_tfvars_json(cls, path: str) -> list[VariableSpec]:
        """Build specs from a ``.tfvars.json`` file.

        Only JSON is supported; HCL is deliberately not parsed. Non-scalar
        values are serialized and marked ``hcl=True``.

        Raises:
            ValueError: If the file's top level is not a JSON object.
        """
        import json
        from pathlib import Path

        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{path}: expected a JSON object at the top level")
        out: list[VariableSpec] = []
        for key, value in data.items():
            if isinstance(value, str):
                out.append(cls(key=key, value=value))
            else:
                out.append(cls(key=key, value=json.dumps(value), hcl=True))
        return out


class WorkspaceSummary(BaseModel):
    """A workspace, reduced to what an agent needs to choose between them."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    name: str
    project_id: str | None = None
    terraform_version: str | None = None
    execution_mode: str | None = None
    locked: bool = False
    resource_count: int | None = None
    current_run_status: str | None = None
    updated_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    vcs_repo_identifier: str | None = None


class WorkspaceList(WorkflowResult):
    """Result of :func:`~pytfe.workflows.find_workspaces`."""

    kind: Kind = "read"
    items: list[WorkspaceSummary] = Field(default_factory=list)
    truncated: bool = False

    def summary(self) -> dict[str, Any]:
        out = super().summary()
        out.update(
            {
                "count": len(self.items),
                "truncated": self.truncated,
                "names": [w.name for w in self.items[:50]],
            }
        )
        return out

    def __str__(self) -> str:
        more = "+" if self.truncated else ""
        return f"{len(self.items)}{more} workspace(s)"


class WorkspaceStatus(WorkflowResult):
    """A workspace's current health, in one call."""

    kind: Kind = "read"
    id: str
    name: str
    terraform_version: str | None = None
    execution_mode: str | None = None
    locked: bool = False
    locked_by: str | None = None
    resource_count: int | None = None
    latest_run: dict[str, Any] | None = None
    current_state_version: dict[str, Any] | None = None
    drift: dict[str, Any] | None = None
    vcs_repo: str | None = None
    auto_apply: bool | None = None
    health: Literal["ok", "drifted", "errored", "locked", "never_run", "unknown"] = (
        "unknown"
    )

    def summary(self) -> dict[str, Any]:
        out = super().summary()
        out.update(
            {
                "id": self.id,
                "name": self.name,
                "health": self.health,
                "locked": self.locked,
                "resource_count": self.resource_count,
                "terraform_version": self.terraform_version,
                "latest_run_status": (self.latest_run or {}).get("status"),
            }
        )
        return out

    def __str__(self) -> str:
        return f"{self.name}: {self.health}"


class PolicyResult(BaseModel):
    """One policy check or evaluation attached to a run."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str | None = None
    name: str | None = None
    status: str | None = None
    passed: bool | None = None
    hard_failed: bool = False
    overridable: bool = False


class PlanSummary(WorkflowResult):
    """What a plan would do, counted and addressed."""

    kind: Kind = "read"
    plan_id: str | None = None
    run_id: str | None = None
    source: Literal["plan_json", "plan_attributes"] = "plan_json"
    add: int = 0
    change: int = 0
    destroy: int = 0
    replace: int = 0
    import_: int = Field(0, alias="import")
    drift: int = 0
    added_addresses: list[str] = Field(default_factory=list)
    changed_addresses: list[str] = Field(default_factory=list)
    destroy_addresses: list[str] = Field(default_factory=list)
    replace_addresses: list[str] = Field(default_factory=list)
    output_changes: list[str] = Field(default_factory=list)
    monthly_cost_delta: str | None = None
    policy_results: list[PolicyResult] = Field(default_factory=list)
    truncated: bool = False

    @property
    def is_destructive(self) -> bool:
        """True when applying would destroy or replace anything."""
        return (self.destroy + self.replace) > 0

    @property
    def has_changes(self) -> bool:
        """True when applying would change anything at all."""
        return (self.add + self.change + self.destroy + self.replace + self.import_) > 0

    def summary(self) -> dict[str, Any]:
        out = super().summary()
        out.update(
            {
                "add": self.add,
                "change": self.change,
                "destroy": self.destroy,
                "replace": self.replace,
                "import": self.import_,
                "is_destructive": self.is_destructive,
                "has_changes": self.has_changes,
                "source": self.source,
                "destroy_addresses": self.destroy_addresses[:20],
                "monthly_cost_delta": self.monthly_cost_delta,
                "policy_failures": [
                    p.name for p in self.policy_results if p.passed is False
                ],
            }
        )
        return out

    def __str__(self) -> str:
        base = f"+{self.add} ~{self.change} -{self.destroy}"
        if self.replace:
            base += f" replace {self.replace}"
        return f"{base} ({'DESTRUCTIVE' if self.is_destructive else 'no destroys'})"


class RunFailure(WorkflowResult):
    """Why a run failed, and what to try next."""

    kind: Kind = "read"
    run_id: str
    stage: Literal["plan", "apply", "policy", "task", "canceled", "none", "unknown"] = (
        "unknown"
    )
    status: str | None = None
    message: str | None = None
    error_lines: list[str] = Field(default_factory=list)
    log_excerpt: str | None = None
    log_read_url: str | None = None
    errored_state_available: bool = False
    policy_failures: list[PolicyResult] = Field(default_factory=list)
    task_failures: list[str] = Field(default_factory=list)
    suggestion: str | None = None
    url: str | None = None

    def summary(self) -> dict[str, Any]:
        out = super().summary()
        out.update(
            {
                "run_id": self.run_id,
                "stage": self.stage,
                "status": self.status,
                "message": self.message,
                "first_error": self.error_lines[0] if self.error_lines else None,
                "errored_state_available": self.errored_state_available,
                "suggestion": self.suggestion,
                "url": self.url,
            }
        )
        return out

    def __str__(self) -> str:
        return f"run {self.run_id} failed at {self.stage}: {self.message or 'unknown'}"


class RunResult(WorkflowResult):
    """Outcome of a run-shaped workflow.

    ``phase`` is the field to branch on. It distinguishes "planned and waiting
    for you" from "applied" from "refused because it would destroy things",
    which a bare status string cannot.
    """

    kind: Kind = "destructive"
    run_id: str | None = None
    workspace_id: str | None = None
    configuration_version_id: str | None = None
    phase: RunPhaseName
    status: str | None = None
    plan: PlanSummary | None = None
    applied: bool = False
    outputs: dict[str, Any] | None = None
    failure: RunFailure | None = None
    url: str | None = None
    duration_s: float = 0.0
    run: Run | None = None

    def summary(self) -> dict[str, Any]:
        out = super().summary()
        out.update(
            {
                "phase": self.phase,
                "run_id": self.run_id,
                "workspace_id": self.workspace_id,
                "status": self.status,
                "applied": self.applied,
                "url": self.url,
                "duration_s": round(self.duration_s, 1),
            }
        )
        if self.plan is not None:
            out["plan"] = {
                "add": self.plan.add,
                "change": self.plan.change,
                "destroy": self.plan.destroy,
                "replace": self.plan.replace,
                "is_destructive": self.plan.is_destructive,
            }
        if self.failure is not None:
            out["first_error"] = (
                self.failure.error_lines[0] if self.failure.error_lines else None
            )
            out["stage"] = self.failure.stage
        return out

    def __str__(self) -> str:
        return f"run {self.run_id or '?'}: {self.phase}"


class Outputs(WorkflowResult):
    """A workspace's current state outputs."""

    kind: Kind = "read"
    values: dict[str, Any] = Field(default_factory=dict)
    sensitive_keys: list[str] = Field(default_factory=list)
    state_version_id: str | None = None
    serial: int | None = None
    terraform_version: str | None = None

    def summary(self) -> dict[str, Any]:
        """Digest of the outputs. Sensitive values are never included, even
        when the workflow was called with ``include_sensitive=True``."""
        out = super().summary()
        out.update(
            {
                "keys": sorted(self.values),
                "sensitive_keys": sorted(self.sensitive_keys),
                "state_version_id": self.state_version_id,
                "serial": self.serial,
                "values": {
                    k: (SENSITIVE if k in self.sensitive_keys else v)
                    for k, v in self.values.items()
                },
            }
        )
        return out

    def __str__(self) -> str:
        return f"{len(self.values)} output(s)"


class EnsureVariablesResult(WorkflowResult):
    """Outcome of :func:`~pytfe.workflows.ensure_variables`."""

    kind: Kind = "write"
    action: Literal[
        "created", "updated", "unchanged", "would_update", "awaiting_confirmation"
    ] = "unchanged"
    created: list[str] = Field(default_factory=list)
    updated: list[str] = Field(default_factory=list)
    deleted: list[str] = Field(default_factory=list)
    unchanged: list[str] = Field(default_factory=list)
    changes: list[Change] = Field(default_factory=list)
    would_delete: list[str] = Field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        out = super().summary()
        out.update(
            {
                "action": self.action,
                "created": self.created,
                "updated": self.updated,
                "deleted": self.deleted,
                "unchanged_count": len(self.unchanged),
                "would_delete": self.would_delete,
            }
        )
        return out

    def __str__(self) -> str:
        return (
            f"+{len(self.created)} ~{len(self.updated)} "
            f"-{len(self.deleted)} ={len(self.unchanged)}"
        )


# Re-exported so callers need only one import site.
EnsureResult = EnsureResult


# ── Tier-2 results ──────────────────────────────────────────────────────────


class StateDownload(WorkflowResult):
    """A workspace's state, downloaded and parsed."""

    kind: Kind = "read"
    workspace_id: str | None = None
    state_version_id: str | None = None
    serial: int | None = None
    lineage: str | None = None
    terraform_version: str | None = None
    size_bytes: int = 0
    state: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        """Digest. Omits ``state`` entirely - it is large and may hold secrets."""
        out = super().summary()
        out.update(
            {
                "workspace_id": self.workspace_id,
                "state_version_id": self.state_version_id,
                "serial": self.serial,
                "lineage": self.lineage,
                "size_bytes": self.size_bytes,
                "resource_count": len(self.state.get("resources") or []),
            }
        )
        return out

    def __str__(self) -> str:
        return f"state serial {self.serial} ({self.size_bytes} bytes)"


class ResourceRow(BaseModel):
    """One resource instance in a workspace's state."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    workspace_id: str | None = None
    workspace_name: str | None = None
    address: str
    type: str | None = None
    provider: str | None = None
    module: str | None = None
    mode: str | None = None


class StateInventory(WorkflowResult):
    """What a workspace actually manages."""

    kind: Kind = "read"
    workspace_id: str | None = None
    resources: list[ResourceRow] = Field(default_factory=list)
    by_type: dict[str, int] = Field(default_factory=dict)
    by_provider: dict[str, int] = Field(default_factory=dict)
    truncated: bool = False

    def summary(self) -> dict[str, Any]:
        out = super().summary()
        out.update(
            {
                "workspace_id": self.workspace_id,
                "count": len(self.resources),
                "truncated": self.truncated,
                "by_type": dict(sorted(self.by_type.items())[:25]),
                "by_provider": self.by_provider,
            }
        )
        return out

    def __str__(self) -> str:
        return f"{len(self.resources)} resource(s)"


class PushStateResult(WorkflowResult):
    """Outcome of a state write."""

    kind: Kind = "destructive"
    action: Literal["pushed", "awaiting_confirmation", "refused", "unchanged"] = (
        "pushed"
    )
    workspace_id: str | None = None
    state_version_id: str | None = None
    serial_before: int | None = None
    serial_after: int | None = None
    lineage: str | None = None
    still_locked: bool = False

    def summary(self) -> dict[str, Any]:
        out = super().summary()
        out.update(
            {
                "action": self.action,
                "workspace_id": self.workspace_id,
                "state_version_id": self.state_version_id,
                "serial_before": self.serial_before,
                "serial_after": self.serial_after,
                "still_locked": self.still_locked,
            }
        )
        return out

    def __str__(self) -> str:
        return f"{self.action}: serial {self.serial_before} -> {self.serial_after}"


class LockResult(WorkflowResult):
    """Outcome of a lock or unlock."""

    kind: Kind = "write"
    action: Literal["locked", "unlocked", "unchanged"] = "unchanged"
    workspace_id: str | None = None
    locked: bool = False
    locked_by: str | None = None

    def summary(self) -> dict[str, Any]:
        out = super().summary()
        out.update(
            {
                "action": self.action,
                "workspace_id": self.workspace_id,
                "locked": self.locked,
                "locked_by": self.locked_by,
            }
        )
        return out

    def __str__(self) -> str:
        return f"{self.workspace_id}: {self.action}"


class CloneResult(WorkflowResult):
    """Outcome of cloning a workspace."""

    kind: Kind = "write"
    action: Literal["created", "updated", "unchanged", "would_create"] = "created"
    source_workspace_id: str | None = None
    target_workspace_id: str | None = None
    copied_variables: list[str] = Field(default_factory=list)
    manual_followups: list[str] = Field(default_factory=list)
    state_migrated: bool = False

    def summary(self) -> dict[str, Any]:
        out = super().summary()
        out.update(
            {
                "action": self.action,
                "source_workspace_id": self.source_workspace_id,
                "target_workspace_id": self.target_workspace_id,
                "copied_variables": self.copied_variables,
                "manual_followups": self.manual_followups,
                "state_migrated": self.state_migrated,
            }
        )
        return out

    def __str__(self) -> str:
        return f"cloned -> {self.target_workspace_id} ({self.action})"


class TeardownResult(WorkflowResult):
    """Outcome of tearing a workspace down."""

    kind: Kind = "destructive"
    action: Literal["deleted", "awaiting_confirmation", "refused", "not_found"] = (
        "awaiting_confirmation"
    )
    workspace_id: str | None = None
    destroy_run_id: str | None = None
    resources_remaining: int | None = None

    def summary(self) -> dict[str, Any]:
        out = super().summary()
        out.update(
            {
                "action": self.action,
                "workspace_id": self.workspace_id,
                "destroy_run_id": self.destroy_run_id,
                "resources_remaining": self.resources_remaining,
            }
        )
        return out

    def __str__(self) -> str:
        return f"{self.workspace_id}: {self.action}"


class FleetItem(BaseModel):
    """One workspace's outcome inside a fleet workflow."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    workspace: WorkspaceSummary
    result: Any = None
    error: dict[str, Any] | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


class FleetResult(WorkflowResult):
    """Aggregate of a workflow fanned out over many workspaces.

    One workspace failing never aborts the others; its error is captured via
    ``TFEError.to_dict()`` and reported alongside the successes.
    """

    kind: Kind = "write"
    items: list[FleetItem] = Field(default_factory=list)
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0

    def summary(self) -> dict[str, Any]:
        out = super().summary()
        out.update(
            {
                "succeeded": self.succeeded,
                "failed": self.failed,
                "skipped": self.skipped,
                "failures": [
                    {
                        "workspace": item.workspace.name,
                        "error": (item.error or {}).get("message"),
                    }
                    for item in self.items
                    if item.error
                ][:25],
            }
        )
        return out

    def __str__(self) -> str:
        return f"{self.succeeded} ok, {self.failed} failed, {self.skipped} skipped"


class OrgInventory(WorkflowResult):
    """Every workspace in an organization, with its health."""

    kind: Kind = "read"
    organization: str
    rows: list[WorkspaceStatus] = Field(default_factory=list)
    by_terraform_version: dict[str, int] = Field(default_factory=dict)
    by_execution_mode: dict[str, int] = Field(default_factory=dict)
    drifted: list[str] = Field(default_factory=list)
    locked: list[str] = Field(default_factory=list)
    errored: list[str] = Field(default_factory=list)

    def to_csv(self) -> str:
        """Render the inventory as CSV, one row per workspace."""
        import csv
        import io

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "id",
                "name",
                "health",
                "terraform_version",
                "execution_mode",
                "locked",
                "resource_count",
                "latest_run_status",
            ]
        )
        for row in self.rows:
            writer.writerow(
                [
                    row.id,
                    row.name,
                    row.health,
                    row.terraform_version or "",
                    row.execution_mode or "",
                    row.locked,
                    row.resource_count if row.resource_count is not None else "",
                    (row.latest_run or {}).get("status") or "",
                ]
            )
        return buffer.getvalue()

    def summary(self) -> dict[str, Any]:
        out = super().summary()
        out.update(
            {
                "organization": self.organization,
                "count": len(self.rows),
                "by_terraform_version": self.by_terraform_version,
                "by_execution_mode": self.by_execution_mode,
                "drifted": self.drifted[:25],
                "locked": self.locked[:25],
                "errored": self.errored[:25],
            }
        )
        return out

    def __str__(self) -> str:
        return f"{len(self.rows)} workspace(s) in {self.organization}"


class ResourceInventory(WorkflowResult):
    """Managed resources across an organization."""

    kind: Kind = "read"
    organization: str
    rows: list[ResourceRow] = Field(default_factory=list)
    by_type: dict[str, int] = Field(default_factory=dict)
    by_provider: dict[str, int] = Field(default_factory=dict)
    by_workspace: dict[str, int] = Field(default_factory=dict)
    truncated: bool = False

    def summary(self) -> dict[str, Any]:
        out = super().summary()
        out.update(
            {
                "organization": self.organization,
                "count": len(self.rows),
                "truncated": self.truncated,
                "by_type": dict(sorted(self.by_type.items())[:25]),
                "by_provider": self.by_provider,
            }
        )
        return out

    def __str__(self) -> str:
        return (
            f"{len(self.rows)} resource(s) across {len(self.by_workspace)} workspace(s)"
        )


class TokenRow(BaseModel):
    """One API token, described without ever exposing its value."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str | None = None
    kind: Literal["organization", "team", "agent"]
    owner: str | None = None
    description: str | None = None
    created_at: datetime | None = None
    expired_at: datetime | None = None
    last_used_at: datetime | None = None
    expired: bool = False
    expiring: bool = False


class TokenAudit(WorkflowResult):
    """Every token this credential can enumerate, and when it expires."""

    kind: Kind = "read"
    organization: str
    tokens: list[TokenRow] = Field(default_factory=list)
    expiring_within_days: int = 30

    def summary(self) -> dict[str, Any]:
        out = super().summary()
        out.update(
            {
                "organization": self.organization,
                "count": len(self.tokens),
                "expired": [t.id for t in self.tokens if t.expired],
                "expiring": [t.id for t in self.tokens if t.expiring],
                "by_kind": {
                    kind: sum(1 for t in self.tokens if t.kind == kind)
                    for kind in ("organization", "team", "agent")
                },
            }
        )
        return out

    def __str__(self) -> str:
        expiring = sum(1 for t in self.tokens if t.expiring or t.expired)
        return f"{len(self.tokens)} token(s), {expiring} expiring or expired"


class AgentPoolSetup(WorkflowResult):
    """Outcome of setting up an agent pool.

    ``token`` is returned exactly once, because the API shows an agent token's
    value only at creation. It is deliberately excluded from ``summary()``.
    """

    kind: Kind = "write"
    action: Literal["created", "updated", "unchanged", "would_create"] = "unchanged"
    agent_pool_id: str | None = None
    name: str | None = None
    token: str | None = None
    token_id: str | None = None
    assigned_workspace_ids: list[str] = Field(default_factory=list)
    agent_connected: bool = False

    def summary(self) -> dict[str, Any]:
        """Digest. Never contains the token value."""
        out = super().summary()
        out.update(
            {
                "action": self.action,
                "agent_pool_id": self.agent_pool_id,
                "name": self.name,
                "token_id": self.token_id,
                "token_returned": self.token is not None,
                "assigned_workspace_ids": self.assigned_workspace_ids,
                "agent_connected": self.agent_connected,
            }
        )
        return out

    def __str__(self) -> str:
        return f"agent pool {self.name}: {self.action}"


class PublishResult(WorkflowResult):
    """Outcome of publishing a registry artifact."""

    kind: Kind = "write"
    action: Literal["published", "unchanged", "would_publish"] = "published"
    module_id: str | None = None
    name: str | None = None
    provider: str | None = None
    version: str | None = None
    status: str | None = None

    def summary(self) -> dict[str, Any]:
        out = super().summary()
        out.update(
            {
                "action": self.action,
                "name": self.name,
                "provider": self.provider,
                "version": self.version,
                "status": self.status,
            }
        )
        return out

    def __str__(self) -> str:
        return f"{self.name}/{self.provider} {self.version}: {self.action}"


class TFEHealth(WorkflowResult):
    """A Terraform Enterprise instance summary, assembled from admin reads.

    Note:
        There is no health or ping endpoint in the API. This is composed from
        the admin namespaces that do exist - organizations, runs, users and
        Terraform versions - so it reports reachability and queue pressure
        rather than a server-reported health status.
    """

    kind: Kind = "read"
    reachable: bool = False
    organization_count: int | None = None
    user_count: int | None = None
    run_queue_depth: int | None = None
    runs_by_status: dict[str, int] = Field(default_factory=dict)
    terraform_versions: int | None = None

    def summary(self) -> dict[str, Any]:
        out = super().summary()
        out.update(
            {
                "reachable": self.reachable,
                "organization_count": self.organization_count,
                "user_count": self.user_count,
                "run_queue_depth": self.run_queue_depth,
                "runs_by_status": self.runs_by_status,
                "terraform_versions": self.terraform_versions,
            }
        )
        return out

    def __str__(self) -> str:
        state = "reachable" if self.reachable else "unreachable"
        return f"TFE {state}, {self.run_queue_depth} run(s) queued"
