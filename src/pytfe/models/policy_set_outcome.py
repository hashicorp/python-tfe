from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .policy_evaluation import PolicyEvaluation, PolicyResultCount


class PolicySetOutcome(BaseModel):
    """PolicySetOutcome represents outcome of the policy set that are part of the policy evaluation"""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    outcomes: list[Outcome] = Field(default_factory=list, alias="outcomes")
    error: str | None = Field(None, alias="error")
    overridable: bool | None = Field(None, alias="overridable")
    policy_set_name: str | None = Field(None, alias="policy-set-name")
    policy_set_description: str | None = Field(None, alias="policy-set-description")
    result_count: PolicyResultCount | None = Field(None, alias="result-count")

    # The policy evaluation that this outcome belongs to
    policy_evaluation: PolicyEvaluation | None = Field(None, alias="policy-evaluation")


class Outcome(BaseModel):
    """Outcome represents the outcome of the individual policy"""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    enforcement_level: str | None = Field(None, alias="enforcement-level")
    query: str | None = Field(None, alias="query")
    status: str | None = Field(None, alias="status")
    policy_name: str | None = Field(None, alias="policy-name")
    description: str | None = Field(None, alias="description")


class PolicySetOutcomeListFilter(BaseModel):
    """PolicySetOutcomeListFilter represents the filters that are supported while listing a policy set outcome"""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    status: str | None = Field(None, alias="status")
    enforcement_level: str | None = Field(None, alias="enforcement-level")


class PolicySetOutcomeListOptions(BaseModel):
    """PolicySetOutcomeListOptions represents the options for listing policy set outcomes."""

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    filter: dict[str, PolicySetOutcomeListFilter] | None = None
    page_size: int | None = Field(None, alias="page[size]")
