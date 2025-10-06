from __future__ import annotations

from enum import Enum


class PolicyKind(str, Enum):
    OPA = "opa"
    SENTINEL = "sentinel"
