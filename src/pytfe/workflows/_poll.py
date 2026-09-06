# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""The single polling primitive for the workflow layer.

Every wait in ``pytfe.workflows`` goes through :func:`wait_until`. Nothing else
in the package calls ``time.sleep``, which is enforced by
``tests/contract/test_isolation.py``.

Two properties matter and neither is available from ``pytfe.utils.poll_until``
(which is dead code, returns ``bool``, and raises a bare ``TimeoutError`` that
``except TFEError`` cannot catch):

* the last observed value is returned, and is attached to the timeout error -
  "timed out" without "...while the run was still planning" is not actionable;
* ``clock`` and ``sleep`` are injectable, so the unit suite never really sleeps
  (``docs/TESTS.md`` forbids it).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from ..errors import WorkflowTimeout

T = TypeVar("T")

__all__ = ["wait_until"]


def wait_until(
    fetch: Callable[[], T],
    done: Callable[[T], bool],
    *,
    timeout: float,
    interval: float = 2.0,
    max_interval: float = 15.0,
    backoff: float = 1.5,
    on_tick: Callable[[T], None] | None = None,
    description: str = "condition",
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Poll ``fetch`` until ``done`` is satisfied, then return the value.

    The deadline is wall-clock across the whole call, measured on a monotonic
    clock. This matters because the transport itself sleeps on 429/502/503/504
    retries (up to ``max_retries`` attempts with exponential backoff) *inside* a
    single ``fetch()``, so a per-attempt budget would badly under-count.

    Args:
        fetch: Called to obtain the current value. Exceptions propagate.
        done: Predicate deciding whether polling is finished.
        timeout: Total seconds to wait before giving up.
        interval: Delay before the second poll, in seconds.
        max_interval: Ceiling for the growing delay.
        backoff: Multiplier applied to the delay after each poll.
        on_tick: Called with every observed value, including the final one.
        description: Noun used in the timeout message.
        clock: Monotonic time source. Injected by tests.
        sleep: Sleep function. Injected by tests.

    Returns:
        The first fetched value for which ``done`` returned True.

    Raises:
        WorkflowTimeout: If the deadline passes first. The last observed value
            is attached as ``.last``.

    Example:
        >>> run = wait_until(
        ...     lambda: client.runs.read("run-CZcmD7eagjhyXAvx"),
        ...     lambda r: is_terminal(r.status),
        ...     timeout=1800,
        ...     description="run run-CZcmD7eagjhyXAvx to finish",
        ... )
    """
    started = clock()
    delay = interval
    value = fetch()
    while True:
        if on_tick is not None:
            on_tick(value)
        if done(value):
            return value

        elapsed = clock() - started
        if elapsed >= timeout:
            raise WorkflowTimeout(
                f"timed out after {elapsed:.0f}s waiting for {description}",
                last=value,
                hint=(
                    "Raise the timeout= argument, or inspect the last observed "
                    "value on the exception's .last attribute."
                ),
            )

        # Never sleep past the deadline: a 15s interval against 2s remaining
        # would report a 17s elapsed time for a 10s timeout.
        sleep(min(delay, timeout - elapsed))
        delay = min(delay * backoff, max_interval)
        value = fetch()
