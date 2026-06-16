# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ._base import TFEModel


class AdminUserListOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    query: str | None = Field(default=None, alias="q")
    administrators: bool | None = None
    suspended: bool | None = None
    page_number: int | None = Field(default=None, alias="page[number]")
    page_size: int | None = Field(default=None, alias="page[size]")


class AdminUser(TFEModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)
    id: str | None = None
    username: str | None = None
    email: str | None = None
    avatar_url: str | None = Field(default=None, alias="avatar-url")
    is_admin: bool | None = Field(default=None, alias="is-admin")
    is_suspended: bool | None = Field(default=None, alias="is-suspended")
    two_factor_enabled: bool | None = Field(default=None, alias="two-factor-enabled")
    two_factor_verified: bool | None = Field(default=None, alias="two-factor-verified")
