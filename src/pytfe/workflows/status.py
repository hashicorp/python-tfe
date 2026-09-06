# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Run-status classification.

The SDK ships :class:`~pytfe.models.run.RunStatus` with 33 members and no way
to ask whether one is final. Every caller that waits on a run has had to invent
its own set of "terminal" strings, and the four sets in this repository's
examples and scenario docs disagree with one another. This module is the single
classification they collapse into.

Every ``RunStatus`` member belongs to exactly one phase, enforced by
``tests/units/workflows/test_status.py``: when HCP Terraform adds a status, that
test fails rather than the waiter silently spinning until timeout.
"""

from __future__ import annotations

from enum import Enum

from ..models.run import Run, RunStatus

__all__ = [
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
    "SUCCEEDED",
    "FAILED",
]


class RunPhase(str, Enum):
    """Which phase of its life a run is in."""

    TERMINAL = "terminal"
    """Finished. Nothing further will happen without a new run."""

    CONFIRMABLE = "confirmable"
    """Planned and ready to apply."""

    AWAITING_DECISION = "awaiting_decision"
    """Paused for a human: a policy override or a post-plan task decision."""

    IN_PROGRESS = "in_progress"
    """Still working. Keep polling."""


#: Run reached an end state; no further transition is possible.
TERMINAL: frozenset[RunStatus] = frozenset(
    {
        RunStatus.Run_Applied,
        RunStatus.Run_Canceled,
        RunStatus.Run_Discarded,
        RunStatus.Run_Errored,
        RunStatus.Run_Planned_And_Finished,
    }
)

#: Plan finished and the run can be applied.
CONFIRMABLE: frozenset[RunStatus] = frozenset(
    {
        RunStatus.Run_Planned,
        RunStatus.Run_Planned_And_Saved,
        RunStatus.Run_Cost_Estimated,
        RunStatus.Run_Policy_Checked,
        RunStatus.Run_Policy_Override,
        RunStatus.Run_Tf_Policy_Checked,
        RunStatus.Run_Post_Plan_Completed,
    }
)

#: Paused awaiting a human decision. Polling past these states never resolves.
#:
#: ``tf_policy_override`` sits here rather than in :data:`CONFIRMABLE` because a
#: run *paused awaiting* a tf-policy override decision reports that status on
#: the wire - see the v1.4.1 CHANGELOG entry that introduced it.
AWAITING_DECISION: frozenset[RunStatus] = frozenset(
    {
        RunStatus.Run_Policy_Soft_Failed,
        RunStatus.Run_Tf_Policy_Override,
        RunStatus.Run_Post_Plan_Awaiting_Decision,
    }
)

#: Everything still moving.
IN_PROGRESS: frozenset[RunStatus] = frozenset(
    set(RunStatus) - TERMINAL - CONFIRMABLE - AWAITING_DECISION
)

#: The plan is over, one way or another.
PLAN_DONE: frozenset[RunStatus] = TERMINAL | CONFIRMABLE | AWAITING_DECISION

#: Terminal states that represent success.
SUCCEEDED: frozenset[RunStatus] = frozenset(
    {RunStatus.Run_Applied, RunStatus.Run_Planned_And_Finished}
)

#: Terminal states that represent failure or abandonment.
FAILED: frozenset[RunStatus] = TERMINAL - SUCCEEDED


def phase_of(status: RunStatus | str | None) -> RunPhase:
    """Return the :class:`RunPhase` a run status belongs to.

    Args:
        status: A ``RunStatus``, its wire string, or None.

    Returns:
        The phase. An unknown or None status is reported as
        ``RunPhase.IN_PROGRESS``, which keeps a waiter polling rather than
        declaring a run finished it cannot classify.

    Example:
        >>> from pytfe.workflows.status import phase_of
        >>> phase_of("planned_and_finished")
        <RunPhase.TERMINAL: 'terminal'>
    """
    if status is None:
        return RunPhase.IN_PROGRESS
    try:
        value = RunStatus(status)
    except ValueError:
        return RunPhase.IN_PROGRESS
    if value in TERMINAL:
        return RunPhase.TERMINAL
    if value in CONFIRMABLE:
        return RunPhase.CONFIRMABLE
    if value in AWAITING_DECISION:
        return RunPhase.AWAITING_DECISION
    return RunPhase.IN_PROGRESS


def is_terminal(status: RunStatus | str | None) -> bool:
    """True when a run has finished and will not transition again."""
    return phase_of(status) is RunPhase.TERMINAL


def is_confirmable(status: RunStatus | str | None) -> bool:
    """True when a run's plan is done and the run can be applied."""
    return phase_of(status) is RunPhase.CONFIRMABLE


def is_awaiting_decision(status: RunStatus | str | None) -> bool:
    """True when a run is paused for a human decision."""
    return phase_of(status) is RunPhase.AWAITING_DECISION


def is_plan_done(status: RunStatus | str | None) -> bool:
    """True when a run's plan has finished, whatever the outcome."""
    return phase_of(status) is not RunPhase.IN_PROGRESS


def run_is_confirmable(run: Run) -> bool:
    """True when ``run`` can be applied right now.

    Prefers the wire's own answer (``run.actions.is_confirmable``), which never
    drifts, and falls back to :data:`CONFIRMABLE` only when the API did not
    include an ``actions`` block.

    Args:
        run: The run to test.

    Returns:
        Whether an apply would be accepted.

    Example:
        >>> run = client.runs.read("run-CZcmD7eagjhyXAvx")
        >>> if run_is_confirmable(run):
        ...     client.runs.apply(run.id)
    """
    if run.actions is not None:
        return bool(run.actions.is_confirmable)
    return is_confirmable(run.status)
