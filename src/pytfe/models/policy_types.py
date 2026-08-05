# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from enum import Enum


class PolicyKind(str, Enum):
    """The kind of policy - shared between Policy and PolicySet models."""

    OPA = "opa"
    SENTINEL = "sentinel"
    TFPOLICY = "tfpolicy"


class EnforcementLevel(str, Enum):
    """Policy enforcement levels."""

    ENFORCEMENT_ADVISORY = "advisory"
    ENFORCEMENT_MANDATORY = "mandatory"
    ENFORCEMENT_HARD = "hard-mandatory"
    ENFORCEMENT_SOFT = "soft-mandatory"


class TfPolicyEvaluationStatus(str, Enum):
    """Status values for a tf-policy evaluation lifecycle."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_OVERRIDE = "awaiting_override"
    PASSED = "passed"
    FAILED = "failed"
    OVERRIDDEN = "overridden"
    ERRORED = "errored"
    CANCELED = "canceled"
    UNREACHABLE = "unreachable"  # Pseudo-state derived from run final state


class TfPolicyStage(str, Enum):
    """Stage type for a tf-policy evaluation (wire values are capital-initial)."""

    INIT = "Init"
    PLAN = "Plan"
    APPLY = "Apply"


class TfPolicyEnforcementLevel(str, Enum):
    """Enforcement levels used by tf-policy outcomes.

    Distinct from ``EnforcementLevel`` (Sentinel/OPA) — ``mandatory_overridable``
    is tf-policy only and uses an underscore, not a hyphen.
    """

    ADVISORY = "advisory"
    MANDATORY = "mandatory"
    MANDATORY_OVERRIDABLE = "mandatory_overridable"
