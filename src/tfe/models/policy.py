from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from .organization import Organization
from .policy_set import PolicyKind


class EnforcementLevel(str, Enum):
    ENFORCEMENT_ADVISORY = "advisory"
    ENFORCEMENT_MANDATORY = "mandatory"
    ENFORCEMENT_HARD = "hard-mandatory"
    ENFORCEMENT_SOFT = "soft-mandatory"


class Policy(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    name: str | None = Field(None, alias="name")
    kind: PolicyKind | None = Field(None, alias="kind")
    query: str | None = Field(None, alias="query")
    description: str | None = Field(None, alias="description")
    enforcement_level: EnforcementLevel | None = Field(None, alias="enforcement-level")
    policy_set_count: int | None = Field(None, alias="policy-set-count")
    updated_at: datetime | None = Field(None, alias="updated-at")
    organization: Organization | None = Field(None, alias="organization")


class PolicyList(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    items: list[Policy] = Field(default_factory=list)
    current_page: int | None = None
    total_pages: int | None = None
    prev_page: int | None = None
    next_page: int | None = None
    total_count: int | None = None


class PolicyListOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    search: str | None = Field(None, alias="search[name]")
    kind: PolicyKind | None = Field(None, alias="filter[kind]")
    page_number: int | None = Field(None, alias="page[number]")
    page_size: int | None = Field(None, alias="page[size]")


class PolicyCreateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    name: str = Field(..., alias="name")
    kind: PolicyKind | None = Field(None, alias="kind")
    query: str | None = Field(None, alias="query")
    description: str | None = Field(None, alias="description")
    enforcement_level: EnforcementLevel | None = Field(None, alias="enforcement-level")


class PolicyUpdateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    query: str | None = Field(None, alias="query")
    description: str | None = Field(None, alias="description")
    enforcement_level: EnforcementLevel | None = Field(None, alias="enforcement-level")
