from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .policy_set import PolicySet
from .variable import CategoryType


class PolicySetParameter(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str
    key: str = Field(..., alias="key")
    value: str | None = Field(None, alias="value")
    category: CategoryType = Field(..., alias="category")
    sensitive: bool = Field(..., alias="sensitive")

    # relations
    policy_set: PolicySet = Field(..., alias="configurable")


class PolicySetParameterListOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    page_size: int | None = Field(None, alias="page[size]")


class PolicySetParameterCreateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    key: str = Field(..., alias="key")
    value: str | None = Field(None, alias="value")

    # Required: The Category of the parameter, should always be "policy-set"
    category: CategoryType = Field(default=CategoryType.POLICY_SET, alias="category")
    sensitive: bool | None = Field(None, alias="sensitive")


class PolicySetParameterUpdateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    key: str | None = Field(None, alias="key")
    value: str | None = Field(None, alias="value")
    sensitive: bool | None = Field(None, alias="sensitive")
