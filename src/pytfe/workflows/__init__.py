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
from ._resolve import resolve_workspace
from ._result import Change, EnsureResult, WorkflowResult
from .models import (
    EnsureVariablesResult,
    Outputs,
    PlanSummary,
    PolicyResult,
    RunFailure,
    RunResult,
    VariableSpec,
    VCSRepoSpec,
    WorkspaceList,
    WorkspaceSpec,
    WorkspaceStatus,
    WorkspaceSummary,
)
from .runs import (
    Confirm,
    apply_with_gate,
    diagnose_run,
    plan_summary,
    run_from_directory,
    speculative_plan,
    wait_for_run,
)
from .state import read_outputs
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
    ensure_variables,
    ensure_workspace,
    find_workspaces,
    workspace_status,
)

__all__ = [
    # Workflows
    "find_workspaces",
    "workspace_status",
    "ensure_workspace",
    "ensure_variables",
    "run_from_directory",
    "speculative_plan",
    "wait_for_run",
    "plan_summary",
    "diagnose_run",
    "apply_with_gate",
    "read_outputs",
    # Inputs
    "WorkspaceSpec",
    "VCSRepoSpec",
    "VariableSpec",
    "Confirm",
    # Results
    "WorkflowResult",
    "EnsureResult",
    "EnsureVariablesResult",
    "Change",
    "WorkspaceSummary",
    "WorkspaceList",
    "WorkspaceStatus",
    "PlanSummary",
    "PolicyResult",
    "RunFailure",
    "RunResult",
    "Outputs",
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
    "resolve_workspace",
]
