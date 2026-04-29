# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from enum import Enum


class PolicyKind(str, Enum):
    """The kind of policy - shared between Policy and PolicySet models."""

    OPA = "opa"
    SENTINEL = "sentinel"


class EnforcementLevel(str, Enum):
    """Policy enforcement levels."""

    ENFORCEMENT_ADVISORY = "advisory"
    ENFORCEMENT_MANDATORY = "mandatory"
    ENFORCEMENT_HARD = "hard-mandatory"
    ENFORCEMENT_SOFT = "soft-mandatory"
