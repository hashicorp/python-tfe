# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Ask what a stack status means, without hard-coding status strings.

A stack deployment reports status at four levels - configuration, deployment
group, deployment run, deployment step - each with its own vocabulary and none
with a way to ask whether a value is final. Use these predicates in your own
polling, dashboards and alerting rather than writing the string sets yourself::

    from pytfe.workflows import run_is_awaiting_approval, run_phase, StackPhase

    for run in tfe.stack_deployment_runs.list(group_id):
        if run_is_awaiting_approval(run.status):
            notify_approver(run.deployment)
        elif run_phase(run.status) is StackPhase.TERMINAL:
            record_outcome(run.deployment, run.status)

Every status falls into exactly one :class:`StackPhase`:

``TERMINAL``
    Finished. Nothing more happens without new work.
``AWAITING_APPROVAL``
    Parked for an operator. **This will never advance on its own** - a poller
    that treats it as in-progress waits forever on work that needs a human.
    Deployment runs report it as ``pre-deploying-pending-operator`` or
    ``deploying-pending-operator``; steps report ``pending-operator``.
``IN_PROGRESS``
    Still working, including a step ``blocked`` behind a predecessor, and any
    status this SDK does not recognise - so a newly added upstream status keeps
    your loop polling rather than being read as finished.

Names are prefixed by level (``CONFIG_``, ``GROUP_``, ``RUN_``, ``STEP_``)
because ``pytfe.workflows`` exports everything into one namespace alongside the
workspace-run classification in :mod:`pytfe.workflows.status`. Use the frozensets
directly (``RUN_TERMINAL``, ``STEP_FAILED``, …) when you want set membership
instead of a predicate.
"""

from __future__ import annotations

from enum import Enum

from ..models.stack_configuration import StackConfigurationStatus
from ..models.stack_deployment_group import DeploymentGroupStatus
from ..models.stack_deployment_run import DeploymentRunStatus
from ..models.stack_deployment_step import DeploymentStepStatus

__all__ = [
    "StackPhase",
    "CONFIG_TERMINAL",
    "CONFIG_IN_PROGRESS",
    "CONFIG_SUCCEEDED",
    "CONFIG_FAILED",
    "GROUP_TERMINAL",
    "GROUP_IN_PROGRESS",
    "GROUP_SUCCEEDED",
    "GROUP_FAILED",
    "RUN_TERMINAL",
    "RUN_AWAITING_APPROVAL",
    "RUN_IN_PROGRESS",
    "RUN_SUCCEEDED",
    "RUN_FAILED",
    "STEP_TERMINAL",
    "STEP_AWAITING_APPROVAL",
    "STEP_IN_PROGRESS",
    "STEP_FAILED",
    "configuration_phase",
    "group_phase",
    "run_phase",
    "step_phase",
    "configuration_is_prepared",
    "run_is_awaiting_approval",
    "run_is_terminal",
    "step_is_awaiting_approval",
]


class StackPhase(str, Enum):
    """Which phase of its life a stack object is in."""

    TERMINAL = "terminal"
    """Finished. Nothing further happens without new work."""

    AWAITING_APPROVAL = "awaiting_approval"
    """Paused for an operator. Will never advance on its own."""

    IN_PROGRESS = "in_progress"
    """Still working. Keep polling."""


# ── Configuration ───────────────────────────────────────────────────────────
#
# A configuration is prepared once, then deployments run against it. There is no
# operator gate at this level.

CONFIG_TERMINAL: frozenset[StackConfigurationStatus] = frozenset(
    {StackConfigurationStatus.COMPLETED, StackConfigurationStatus.FAILED}
)
CONFIG_IN_PROGRESS: frozenset[StackConfigurationStatus] = frozenset(
    set(StackConfigurationStatus) - CONFIG_TERMINAL
)
CONFIG_SUCCEEDED: frozenset[StackConfigurationStatus] = frozenset(
    {StackConfigurationStatus.COMPLETED}
)
CONFIG_FAILED: frozenset[StackConfigurationStatus] = CONFIG_TERMINAL - CONFIG_SUCCEEDED


# ── Deployment group ────────────────────────────────────────────────────────
#
# A group's status does NOT expose the operator gate: a group whose runs are all
# parked awaiting approval still reports `deploying`. Ask at the run level.

GROUP_TERMINAL: frozenset[DeploymentGroupStatus] = frozenset(
    {
        DeploymentGroupStatus.SUCCEEDED,
        DeploymentGroupStatus.FAILED,
        DeploymentGroupStatus.ABANDONED,
    }
)
GROUP_IN_PROGRESS: frozenset[DeploymentGroupStatus] = frozenset(
    set(DeploymentGroupStatus) - GROUP_TERMINAL
)
GROUP_SUCCEEDED: frozenset[DeploymentGroupStatus] = frozenset(
    {DeploymentGroupStatus.SUCCEEDED}
)
GROUP_FAILED: frozenset[DeploymentGroupStatus] = GROUP_TERMINAL - GROUP_SUCCEEDED


# ── Deployment run ──────────────────────────────────────────────────────────
#
# The only level whose status covers the whole lifecycle AND carries the gate.
# This is the level to wait on.

RUN_AWAITING_APPROVAL: frozenset[DeploymentRunStatus] = frozenset(
    {
        DeploymentRunStatus.PRE_DEPLOYING_PENDING_OPERATOR,
        DeploymentRunStatus.DEPLOYING_PENDING_OPERATOR,
    }
)
RUN_TERMINAL: frozenset[DeploymentRunStatus] = frozenset(
    {
        DeploymentRunStatus.SUCCEEDED,
        DeploymentRunStatus.FAILED,
        DeploymentRunStatus.ABANDONED,
    }
)
RUN_IN_PROGRESS: frozenset[DeploymentRunStatus] = frozenset(
    set(DeploymentRunStatus) - RUN_TERMINAL - RUN_AWAITING_APPROVAL
)
RUN_SUCCEEDED: frozenset[DeploymentRunStatus] = frozenset(
    {DeploymentRunStatus.SUCCEEDED}
)
RUN_FAILED: frozenset[DeploymentRunStatus] = RUN_TERMINAL - RUN_SUCCEEDED


# ── Deployment step ─────────────────────────────────────────────────────────
#
# `blocked` is IN_PROGRESS, not terminal: the step is waiting on a predecessor.
# It is also why a step-level waiter is a trap - when the predecessor fails, a
# blocked step can stay blocked while its run goes `failed`, so a step waiter
# spins on an already-dead deployment. Wait on the run.

STEP_AWAITING_APPROVAL: frozenset[DeploymentStepStatus] = frozenset(
    {DeploymentStepStatus.PENDING_OPERATOR}
)
STEP_TERMINAL: frozenset[DeploymentStepStatus] = frozenset(
    {
        DeploymentStepStatus.COMPLETED,
        DeploymentStepStatus.FAILED,
        DeploymentStepStatus.ABANDONED,
    }
)
STEP_IN_PROGRESS: frozenset[DeploymentStepStatus] = frozenset(
    set(DeploymentStepStatus) - STEP_TERMINAL - STEP_AWAITING_APPROVAL
)
STEP_FAILED: frozenset[DeploymentStepStatus] = frozenset(
    {DeploymentStepStatus.FAILED, DeploymentStepStatus.ABANDONED}
)


def _phase(
    status: object,
    enum: type[Enum],
    terminal: frozenset,  # type: ignore[type-arg]
    awaiting: frozenset,  # type: ignore[type-arg]
) -> StackPhase:
    """Classify one status value, tolerating strings and unknowns."""
    if status is None:
        return StackPhase.IN_PROGRESS
    try:
        value = enum(status)
    except ValueError:
        # An unrecognised status keeps a waiter polling rather than declaring
        # work finished it cannot classify.
        return StackPhase.IN_PROGRESS
    if value in terminal:
        return StackPhase.TERMINAL
    if value in awaiting:
        return StackPhase.AWAITING_APPROVAL
    return StackPhase.IN_PROGRESS


def configuration_phase(status: StackConfigurationStatus | str | None) -> StackPhase:
    """Return the phase of a stack configuration status."""
    return _phase(status, StackConfigurationStatus, CONFIG_TERMINAL, frozenset())


def group_phase(status: DeploymentGroupStatus | str | None) -> StackPhase:
    """Return the phase of a deployment group status."""
    return _phase(status, DeploymentGroupStatus, GROUP_TERMINAL, frozenset())


def run_phase(status: DeploymentRunStatus | str | None) -> StackPhase:
    """Return the phase of a deployment run status.

    Example:
        >>> run_phase("deploying-pending-operator")
        <StackPhase.AWAITING_APPROVAL: 'awaiting_approval'>
    """
    return _phase(status, DeploymentRunStatus, RUN_TERMINAL, RUN_AWAITING_APPROVAL)


def step_phase(status: DeploymentStepStatus | str | None) -> StackPhase:
    """Return the phase of a deployment step status."""
    return _phase(status, DeploymentStepStatus, STEP_TERMINAL, STEP_AWAITING_APPROVAL)


def configuration_is_prepared(status: StackConfigurationStatus | str | None) -> bool:
    """True when a configuration finished preparing successfully."""
    try:
        return StackConfigurationStatus(status) in CONFIG_SUCCEEDED
    except ValueError:
        return False


def run_is_awaiting_approval(status: DeploymentRunStatus | str | None) -> bool:
    """True when a deployment run is parked waiting for an operator."""
    return run_phase(status) is StackPhase.AWAITING_APPROVAL


def run_is_terminal(status: DeploymentRunStatus | str | None) -> bool:
    """True when a deployment run has finished."""
    return run_phase(status) is StackPhase.TERMINAL


def step_is_awaiting_approval(status: DeploymentStepStatus | str | None) -> bool:
    """True when a deployment step is parked waiting for an operator."""
    return step_phase(status) is StackPhase.AWAITING_APPROVAL
