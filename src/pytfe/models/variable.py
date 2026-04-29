# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class CategoryType(str, Enum):
    ENV = "env"
    POLICY_SET = "policy-set"
    TERRAFORM = "terraform"


class Variable(BaseModel):
    id: str | None = None
    key: str | None = None
    value: str | None = None
    description: str | None = None
    category: CategoryType | None = None
    hcl: bool | None = None
    sensitive: bool | None = None
    version_id: str | None = None
    workspace: dict | None = None


class VariableListOptions(BaseModel):
    # Base pagination options would be handled by the service layer
    pass


class VariableCreateOptions(BaseModel):
    key: str | None = None
    value: str | None = None
    description: str | None = None
    category: CategoryType | None = None
    hcl: bool | None = None
    sensitive: bool | None = None


class VariableUpdateOptions(BaseModel):
    key: str | None = None
    value: str | None = None
    description: str | None = None
    category: CategoryType | None = None
    hcl: bool | None = None
    sensitive: bool | None = None
