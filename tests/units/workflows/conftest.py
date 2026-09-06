# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Shared fixtures for workflow unit tests.

The client is autospec'd from a real *instance*, not from ``TFEClient`` the
class. ``TFEClient`` declares no class-level attributes - every namespace is
assigned inside ``__init__`` - so ``create_autospec(TFEClient, instance=True)``
produces a mock with no ``.workspaces`` at all, and a typo like ``.wrokspaces``
is indistinguishable from a real name. Autospec'ing an instance gives both
namespace and per-method signature enforcement.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import create_autospec

import pytest

from pytfe import TFEClient, TFEConfig


@pytest.fixture
def client() -> Any:
    """A fully autospec'd TFEClient. Constructs offline; makes no requests."""
    real = TFEClient(TFEConfig(address="https://tfe.example.com", token="t"))
    try:
        mock = create_autospec(real, instance=True)
    finally:
        real.close()
    # `config` is a Pydantic model, so autospec leaves it as a mock; workflows
    # read `config.address` to build web URLs.
    mock.config = TFEConfig(address="https://tfe.example.com", token="t")
    return mock


@pytest.fixture
def clock() -> Any:
    """A monotonic clock and sleep pair that advance without real waiting."""

    class Clock:
        def __init__(self) -> None:
            self.now = 0.0
            self.slept: list[float] = []

        def time(self) -> float:
            return self.now

        def sleep(self, seconds: float) -> None:
            self.slept.append(seconds)
            self.now += seconds

    return Clock()
