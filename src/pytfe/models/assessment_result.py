# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AssessmentResult(BaseModel):
    """Result of a workspace health assessment (drift detection)."""

    model_config = ConfigDict(
        populate_by_name=True, validate_by_name=True, extra="allow"
    )

    id: str
    succeeded: bool | None = Field(default=None, alias="succeeded")
    all_checks_succeeded: bool | None = Field(
        default=None, alias="all-checks-succeeded"
    )
    checks_errored: int | None = Field(default=None, alias="checks-errored")
    checks_failed: int | None = Field(default=None, alias="checks-failed")
    checks_passed: int | None = Field(default=None, alias="checks-passed")
    checks_unknown: int | None = Field(default=None, alias="checks-unknown")
    created_at: datetime | None = Field(default=None, alias="created-at")
    drifted: bool | None = Field(default=None, alias="drifted")
    error_message: str | None = Field(default=None, alias="error-message")
    resources_drifted: int | None = Field(default=None, alias="resources-drifted")
    resources_undrifted: int | None = Field(default=None, alias="resources-undrifted")
