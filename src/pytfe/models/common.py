# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Pagination(BaseModel):
    current_page: int
    total_count: int
    previous_page: int | None = None
    next_page: int | None = None
    total_pages: int | None = None
    # Add other pagination fields as needed


class Tag(BaseModel):
    id: str | None = None
    name: str = ""


class TagBinding(BaseModel):
    id: str | None = None
    key: str
    value: str | None = None


class TagList(BaseModel):
    items: list[Tag] = Field(default_factory=list)
    pagination: Pagination | None = None


class EffectiveTagBinding(BaseModel):
    id: str
    key: str
    value: str | None = None
    links: dict[str, Any] = Field(default_factory=dict)
