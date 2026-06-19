# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Model for an organization's HCP Terraform subscription."""

from __future__ import annotations

from datetime import datetime

from pydantic import ConfigDict, Field

from ._base import TFEModel


class Subscription(TFEModel):
    """An organization's subscription (its pricing plan / feature set link)."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    is_active: bool | None = Field(default=None, alias="is-active")
    start_at: datetime | None = Field(default=None, alias="start-at")
    end_at: datetime | None = Field(default=None, alias="end-at")
    runs_ceiling: int | None = Field(default=None, alias="runs-ceiling")
    agents_ceiling: int | None = Field(default=None, alias="agents-ceiling")
    contract_start_at: datetime | None = Field(default=None, alias="contract-start-at")
    contract_user_limit: int | None = Field(default=None, alias="contract-user-limit")
    contract_apply_limit: int | None = Field(default=None, alias="contract-apply-limit")
    run_task_limit: int | None = Field(default=None, alias="run-task-limit")
    run_task_workspace_limit: int | None = Field(
        default=None, alias="run-task-workspace-limit"
    )
    run_task_mandatory_enforcement_limit: int | None = Field(
        default=None, alias="run-task-mandatory-enforcement-limit"
    )
    policy_set_limit: int | None = Field(default=None, alias="policy-set-limit")
    policy_limit: int | None = Field(default=None, alias="policy-limit")
    policy_mandatory_enforcement_limit: int | None = Field(
        default=None, alias="policy-mandatory-enforcement-limit"
    )
    versioned_policy_set_limit: int | None = Field(
        default=None, alias="versioned-policy-set-limit"
    )
    is_public_free_tier: bool | None = Field(default=None, alias="is-public-free-tier")
    is_self_serve_trial: bool | None = Field(default=None, alias="is-self-serve-trial")
    # Flat relationship references (the raw block is on `.relationships`; the
    # feature set is hydrated into `.included` when present).
    organization_id: str | None = Field(default=None, alias="organization-id")
    feature_set_id: str | None = Field(default=None, alias="feature-set-id")
    billing_account_id: str | None = Field(default=None, alias="billing-account-id")
