# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""The polling primitive. Nothing here sleeps for real."""

from __future__ import annotations

from typing import Any

import pytest

from pytfe.errors import TFEError, WorkflowTimeout
from pytfe.workflows import wait_until


def test_returns_immediately_when_already_done(clock: Any) -> None:
    calls = []

    def fetch() -> str:
        calls.append(1)
        return "done"

    value = wait_until(
        fetch, lambda v: v == "done", timeout=10, clock=clock.time, sleep=clock.sleep
    )
    assert value == "done"
    assert len(calls) == 1
    assert clock.slept == []


def test_polls_until_the_predicate_passes(clock: Any) -> None:
    values = iter(["pending", "planning", "planned"])
    value = wait_until(
        lambda: next(values),
        lambda v: v == "planned",
        timeout=100,
        interval=2.0,
        clock=clock.time,
        sleep=clock.sleep,
    )
    assert value == "planned"
    assert clock.slept == [2.0, 3.0]  # 2.0 then 2.0 * 1.5 backoff


def test_backoff_is_capped(clock: Any) -> None:
    values = iter(["a"] * 20 + ["z"])
    wait_until(
        lambda: next(values),
        lambda v: v == "z",
        timeout=10_000,
        interval=2.0,
        max_interval=15.0,
        clock=clock.time,
        sleep=clock.sleep,
    )
    assert max(clock.slept) == 15.0


def test_timeout_carries_the_last_value(clock: Any) -> None:
    with pytest.raises(WorkflowTimeout) as excinfo:
        wait_until(
            lambda: "still_planning",
            lambda v: False,
            timeout=5,
            interval=2.0,
            description="the run to finish",
            clock=clock.time,
            sleep=clock.sleep,
        )
    assert excinfo.value.last == "still_planning"
    assert "the run to finish" in str(excinfo.value)
    assert excinfo.value.hint


def test_timeout_is_catchable_both_ways(clock: Any) -> None:
    """Subclasses TFEError so `except TFEError` works, and TimeoutError."""

    def run() -> None:
        wait_until(
            lambda: 1, lambda v: False, timeout=0, clock=clock.time, sleep=clock.sleep
        )

    with pytest.raises(TFEError):
        run()
    with pytest.raises(TimeoutError):
        run()


def test_never_sleeps_past_the_deadline(clock: Any) -> None:
    """A 15s interval against 2s remaining must not overshoot the budget."""
    with pytest.raises(WorkflowTimeout):
        wait_until(
            lambda: "x",
            lambda v: False,
            timeout=5,
            interval=15.0,
            clock=clock.time,
            sleep=clock.sleep,
        )
    assert sum(clock.slept) <= 5.0


def test_on_tick_sees_every_value(clock: Any) -> None:
    seen: list[str] = []
    values = iter(["a", "b", "c"])
    wait_until(
        lambda: next(values),
        lambda v: v == "c",
        timeout=100,
        on_tick=seen.append,
        clock=clock.time,
        sleep=clock.sleep,
    )
    assert seen == ["a", "b", "c"]


def test_fetch_exceptions_propagate(clock: Any) -> None:
    def boom() -> None:
        raise TFEError("upstream failed")

    with pytest.raises(TFEError, match="upstream failed"):
        wait_until(
            boom, lambda v: True, timeout=10, clock=clock.time, sleep=clock.sleep
        )
