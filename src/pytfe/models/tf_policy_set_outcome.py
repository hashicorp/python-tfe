# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ._base import TFEModel
from .policy_types import TfPolicyEnforcementLevel, TfPolicyEvaluationStatus
from .tf_policy_evaluation import TfPolicyResultCount


class TraversalValue(BaseModel):
    """A single traversal/statement pair within a policy diagnostic resource."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    traversal: str | None = None
    statement: str | None = None


class OutcomeResource(BaseModel):
    """A Terraform resource referenced in a policy diagnostic."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    resource_name: str | None = None
    error_message: str | None = None
    info_message: str | None = None
    file_name: str | None = None
    code: str | None = None
    start_line: int | None = None
    values: list[TraversalValue] = Field(default_factory=list)

    @field_validator("values", mode="before")
    @classmethod
    def _none_to_empty_list(cls, value: Any) -> Any:
        return [] if value is None else value


class Diagnostic(BaseModel):
    """A single policy-evaluation diagnostic entry."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    code: str | None = None
    context: str | None = None
    start_line: int | None = None
    summary: str | None = None
    error_message: str | None = None
    resources: list[OutcomeResource] = Field(default_factory=list)

    @field_validator("resources", mode="before")
    @classmethod
    def _none_to_empty_list(cls, value: Any) -> Any:
        return [] if value is None else value


class PassedResource(BaseModel):
    """A Terraform resource that passed a policy check."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    resource_name: str | None = None
    info_messages: list[str] = Field(default_factory=list)

    @field_validator("info_messages", mode="before")
    @classmethod
    def _none_to_empty_list(cls, value: Any) -> Any:
        return [] if value is None else value


class PolicyOutcome(BaseModel):
    """The result of evaluating a single policy within a policy-set outcome.

    Inner fields use snake_case as stored — atlas serialises the ``outcomes``
    column verbatim and the AMS dash-transform does not reach inside it.
    """

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    policy_name: str | None = None
    description: str | None = None
    file_name: str | None = None
    enforcement_level: TfPolicyEnforcementLevel | None = None
    status: TfPolicyEvaluationStatus | None = None
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    passed_resources: list[PassedResource] = Field(default_factory=list)

    @field_validator("diagnostics", "passed_resources", mode="before")
    @classmethod
    def _none_to_empty_list(cls, value: Any) -> Any:
        return [] if value is None else value


class TfPolicySetOutcome(TFEModel):
    """Results for a single policy set within a tf-policy evaluation."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    outcomes: list[PolicyOutcome] = Field(default_factory=list, alias="outcomes")
    error: str | None = Field(None, alias="error")
    overridable: bool | None = Field(None, alias="overridable")
    policy_set_name: str | None = Field(None, alias="policy-set-name")
    policy_set_description: str | None = Field(None, alias="policy-set-description")
    result_count: TfPolicyResultCount | None = Field(None, alias="result-count")

    @field_validator("outcomes", mode="before")
    @classmethod
    def _none_to_empty_list(cls, value: Any) -> Any:
        return [] if value is None else value


class TfPolicySetOutcomeListOptions(BaseModel):
    """Options for listing tf-policy set outcomes under an evaluation."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(None, alias="page[size]")
    page_number: int | None = Field(None, alias="page[number]")
    # Wire params: filter[<key>][status] and filter[<key>][enforcement_level]
    # Build these at the resource layer via build_filter_params().
    filter_status: str | None = None
    filter_enforcement_level: str | None = None
