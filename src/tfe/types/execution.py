from __future__ import annotations

from enum import Enum

__all__ = [
    "ExecutionMode",
]


class ExecutionMode(str, Enum):
    REMOTE = "remote"
    AGENT = "agent"
    LOCAL = "local"