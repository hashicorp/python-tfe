# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Task-oriented workflows built on the public pytfe API.

Every resource method in pytfe is one HTTP round trip. Real work is not: an
API-driven run is eight calls with a polling loop in the middle, and the SDK has
never said which run states are final. This package is the missing layer - the
multi-step operations that ``docs/scenarios/`` describes in prose and that
``examples/`` currently hand-rolls ten different ways.

It is built strictly on the public surface: ``client.<resource>.<verb>``, typed
options models, and typed errors. It never touches the transport, the pagination
helper, or any private attribute, which ``tests/contract/test_isolation.py``
enforces.

Design rules that matter to a caller:

* **Nothing applies, deletes, or overrides by default.** Destructive workflows
  take ``confirmed=True`` (the caller asserting a human approved) or a
  ``confirm`` callback. Without one they stop and return
  ``phase="awaiting_confirmation"`` rather than raising.
* **A destructive plan is refused** unless ``allow_destroy=True``, even when
  ``confirmed=True``.
* **Every ``ensure_*`` is idempotent** and supports ``dry_run=True``.
* **Every result is a Pydantic model with ``summary()``**, sized for an agent's
  context window and free of secrets.
* **Every wait takes a ``timeout``** and raises ``WorkflowTimeout`` carrying the
  last observed value.

Example:
    >>> from pytfe import TFEClient
    >>> from pytfe.workflows import run_from_directory
    >>> with TFEClient() as tfe:
    ...     result = run_from_directory(
    ...         tfe, "./terraform", organization="acme", workspace_name="web"
    ...     )
    ...     if result.phase == "awaiting_confirmation":
    ...         print(result.plan)  # +3 ~1 -0 (no destroys)
"""

from __future__ import annotations

from ..errors import (
    CoreGap,
    RunFailed,
    RunNotConfirmable,
    UploadFailed,
    WorkflowError,
    WorkflowTimeout,
    WorkspaceNotFound,
)
from ._package import package_directory
from ._poll import wait_until
from ._redact import redact_attributes, redact_state
from ._resolve import resolve_workspace
from ._result import Change, EnsureResult, WorkflowResult
from .admin import admin_bootstrap, identity_bootstrap, is_hcp_terraform, tfe_health
from .fleet import (
    WorkspaceFilter,
    bulk_speculative_plan,
    bulk_update,
    bulk_variable_rotate,
    org_inventory,
    resource_inventory,
)
from .governance import (
    OIDC_VARIABLES,
    ensure_notification,
    ensure_policy_set,
    ensure_project,
    ensure_run_task,
    ensure_run_trigger,
    onboard_team,
    setup_agent_pool,
    setup_oidc_dynamic_credentials,
    token_audit,
)
from .models import (
    AgentPoolSetup,
    CloneResult,
    EnsureVariablesResult,
    FleetItem,
    FleetResult,
    LockResult,
    OrgInventory,
    OutputChange,
    Outputs,
    PlanAnalysis,
    PlanSummary,
    PolicyResult,
    ProviderPlatformSpec,
    PublishResult,
    PushStateResult,
    ResourceChange,
    ResourceInventory,
    ResourceRow,
    RunFailure,
    RunResult,
    StackApprovalResult,
    StackDeploymentState,
    StackDiagnosticError,
    StackDiagnosticRow,
    StackFailure,
    StackRunResult,
    StackStatus,
    StateDownload,
    StateInventory,
    TeardownResult,
    TFEHealth,
    TokenAudit,
    TokenRow,
    VariableSpec,
    VCSRepoSpec,
    WorkspaceList,
    WorkspaceSpec,
    WorkspaceStatus,
    WorkspaceSummary,
)
from .registry import (
    no_code_provision,
    publish_module_version,
    publish_provider_version,
)
from .runs import (
    Confirm,
    PolicyMode,
    analyze_plan,
    apply_with_gate,
    cancel_run,
    destroy_run,
    diagnose_run,
    ensure_configuration_version,
    plan_summary,
    queue_run,
    resolve_policy_override,
    run_from_directory,
    speculative_plan,
    wait_for_run,
)
from .stack_phases import (
    StackPhase,
    configuration_is_prepared,
    configuration_phase,
    group_phase,
    run_is_awaiting_approval,
    run_phase,
    step_is_awaiting_approval,
    step_phase,
)
from .stacks import (
    StackConfirm,
    approve_stack_plans,
    diagnose_stack_configuration,
    speculative_stack_plan,
    stack_fetch_and_run,
    stack_run_from_directory,
    stack_status,
    teardown_stack,
    wait_for_stack_configuration,
)
from .state import (
    download_state,
    migrate_state,
    push_state,
    read_outputs,
    rollback_state,
    state_inventory,
)
from .status import (
    AWAITING_DECISION,
    CONFIRMABLE,
    IN_PROGRESS,
    PLAN_DONE,
    TERMINAL,
    RunPhase,
    is_awaiting_decision,
    is_confirmable,
    is_plan_done,
    is_terminal,
    phase_of,
    run_is_confirmable,
)
from .workspaces import (
    clone_workspace,
    ensure_variable_set,
    ensure_variables,
    ensure_workspace,
    find_workspaces,
    lock,
    teardown_workspace,
    unlock,
    workspace_status,
)

__all__ = [
    # Workflows
    "find_workspaces",
    "workspace_status",
    "ensure_workspace",
    "ensure_variables",
    "run_from_directory",
    "ensure_configuration_version",
    "queue_run",
    "speculative_plan",
    "wait_for_run",
    "plan_summary",
    "analyze_plan",
    "diagnose_run",
    "apply_with_gate",
    "read_outputs",
    # Workflows - tier 2
    "resolve_policy_override",
    "cancel_run",
    "destroy_run",
    "lock",
    "unlock",
    "ensure_variable_set",
    "clone_workspace",
    "teardown_workspace",
    "download_state",
    "state_inventory",
    "push_state",
    "rollback_state",
    "migrate_state",
    "bulk_speculative_plan",
    "bulk_update",
    "bulk_variable_rotate",
    "org_inventory",
    "resource_inventory",
    "onboard_team",
    "ensure_policy_set",
    "ensure_run_task",
    "ensure_notification",
    "ensure_run_trigger",
    "ensure_project",
    "setup_oidc_dynamic_credentials",
    "token_audit",
    "setup_agent_pool",
    "admin_bootstrap",
    "identity_bootstrap",
    "tfe_health",
    "publish_module_version",
    "publish_provider_version",
    "no_code_provision",
    # Workflows - stacks
    "stack_status",
    "wait_for_stack_configuration",
    "stack_fetch_and_run",
    "stack_run_from_directory",
    "speculative_stack_plan",
    "approve_stack_plans",
    "diagnose_stack_configuration",
    "teardown_stack",
    # Inputs
    "WorkspaceSpec",
    "VCSRepoSpec",
    "VariableSpec",
    "PolicyMode",
    "StackConfirm",
    "ProviderPlatformSpec",
    "WorkspaceFilter",
    "Confirm",
    "OIDC_VARIABLES",
    "is_hcp_terraform",
    # Results
    "WorkflowResult",
    "EnsureResult",
    "EnsureVariablesResult",
    "Change",
    "WorkspaceSummary",
    "WorkspaceList",
    "WorkspaceStatus",
    "PlanSummary",
    "PlanAnalysis",
    "ResourceChange",
    "OutputChange",
    "PolicyResult",
    "RunFailure",
    "RunResult",
    "Outputs",
    "StateDownload",
    "StateInventory",
    "ResourceRow",
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
    "StackRunResult",
    "StackDeploymentState",
    "StackApprovalResult",
    "StackFailure",
    "StackStatus",
    "StackDiagnosticError",
    "StackDiagnosticRow",
    # Run-status classification
    "RunPhase",
    "TERMINAL",
    "CONFIRMABLE",
    "AWAITING_DECISION",
    "IN_PROGRESS",
    "PLAN_DONE",
    "phase_of",
    "is_terminal",
    "is_confirmable",
    "is_awaiting_decision",
    "is_plan_done",
    "run_is_confirmable",
    # Stack-status classification (level-prefixed so it cannot shadow the above)
    "StackPhase",
    "configuration_phase",
    "group_phase",
    "run_phase",
    "step_phase",
    "configuration_is_prepared",
    "run_is_awaiting_approval",
    "step_is_awaiting_approval",
    # Errors (defined in pytfe.errors; re-exported for convenience)
    "WorkflowError",
    "WorkflowTimeout",
    "WorkspaceNotFound",
    "RunNotConfirmable",
    "RunFailed",
    "UploadFailed",
    "CoreGap",
    # Helpers
    "wait_until",
    "package_directory",
    "redact_state",
    "redact_attributes",
    "resolve_workspace",
]
