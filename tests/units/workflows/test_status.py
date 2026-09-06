# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Run-status classification, including the completeness guarantee."""

from __future__ import annotations

import pytest

from pytfe.models.run import Run, RunStatus
from pytfe.workflows.status import (
    AWAITING_DECISION,
    CONFIRMABLE,
    FAILED,
    IN_PROGRESS,
    PLAN_DONE,
    SUCCEEDED,
    TERMINAL,
    RunPhase,
    is_awaiting_decision,
    is_confirmable,
    is_plan_done,
    is_terminal,
    phase_of,
    run_is_confirmable,
)


def test_every_status_is_classified_exactly_once() -> None:
    """The guarantee that stops a new upstream status hanging the waiter.

    When HCP Terraform adds a run status, this fails instead of the poller
    spinning to timeout on a state it has never heard of.
    """
    buckets = (TERMINAL, CONFIRMABLE, AWAITING_DECISION, IN_PROGRESS)
    for status in RunStatus:
        hits = [b for b in buckets if status in b]
        assert len(hits) == 1, (
            f"{status.value!r} appears in {len(hits)} buckets; every RunStatus "
            "must be in exactly one of TERMINAL/CONFIRMABLE/"
            "AWAITING_DECISION/IN_PROGRESS"
        )
    assert len(TERMINAL | CONFIRMABLE | AWAITING_DECISION | IN_PROGRESS) == len(
        list(RunStatus)
    )


def test_plan_queueable_is_a_real_status() -> None:
    """Regression: the enum was missing this and parsing a run raised.

    ``Run.model_validate`` raising pydantic's ValidationError is especially bad
    here because it is *not* a TFEError, so the workflow layer's
    ``except TFEError`` would not catch it.
    """
    assert RunStatus("plan_queueable") in IN_PROGRESS
    run = Run.model_validate({"id": "run-1", "status": "plan_queueable"})
    assert run.status is RunStatus.Run_Plan_Queueable


def test_succeeded_and_failed_partition_terminal() -> None:
    assert SUCCEEDED | FAILED == TERMINAL
    assert not SUCCEEDED & FAILED


def test_plan_done_is_everything_but_in_progress() -> None:
    assert PLAN_DONE == frozenset(RunStatus) - IN_PROGRESS


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("applied", RunPhase.TERMINAL),
        ("errored", RunPhase.TERMINAL),
        ("planned", RunPhase.CONFIRMABLE),
        ("cost_estimated", RunPhase.CONFIRMABLE),
        ("policy_checked", RunPhase.CONFIRMABLE),
        ("policy_soft_failed", RunPhase.AWAITING_DECISION),
        ("tf_policy_override", RunPhase.AWAITING_DECISION),
        ("post_plan_awaiting_decision", RunPhase.AWAITING_DECISION),
        ("planning", RunPhase.IN_PROGRESS),
        ("plan_queueable", RunPhase.IN_PROGRESS),
    ],
)
def test_phase_of(status: str, expected: RunPhase) -> None:
    assert phase_of(status) is expected


def test_unknown_and_none_keep_polling() -> None:
    """An unrecognised status must not read as 'finished'."""
    assert phase_of("some_future_status") is RunPhase.IN_PROGRESS
    assert phase_of(None) is RunPhase.IN_PROGRESS
    assert not is_terminal("some_future_status")
    assert not is_plan_done(None)


def test_predicates_agree_with_phase_of() -> None:
    for status in RunStatus:
        assert is_terminal(status) is (phase_of(status) is RunPhase.TERMINAL)
        assert is_confirmable(status) is (phase_of(status) is RunPhase.CONFIRMABLE)
        assert is_awaiting_decision(status) is (
            phase_of(status) is RunPhase.AWAITING_DECISION
        )


def test_run_is_confirmable_prefers_the_wire() -> None:
    """actions.is_confirmable is authoritative and never drifts from the API."""
    run = Run.model_validate(
        {
            "id": "run-1",
            "status": "planned",
            # Every RunActions field is required, so all four are supplied.
            "actions": {
                "is-cancelable": False,
                "is-confirmable": False,
                "is-discardable": True,
                "is-force-cancelable": False,
            },
        }
    )
    assert is_confirmable(run.status) is True
    assert run_is_confirmable(run) is False


def test_run_is_confirmable_falls_back_when_actions_absent() -> None:
    run = Run.model_validate({"id": "run-1", "status": "planned"})
    assert run.actions is None
    assert run_is_confirmable(run) is True


def test_force_canceled_is_not_a_status() -> None:
    """examples/oidc_aws_e2e.py has this in a terminal set; it is not real."""
    with pytest.raises(ValueError):
        RunStatus("force_canceled")
