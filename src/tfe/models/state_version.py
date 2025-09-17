from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# ---- Enums ----


class StateVersionStatus(str, Enum):
    PENDING = "pending"
    FINALIZED = "finalized"
    DISCARDED = "discarded"


class StateVersionIncludeOpt(str, Enum):
    CREATED_BY = "created_by"
    RUN = "run"
    RUN_CREATED_BY = "run.created_by"
    RUN_CONFIGURATION_VERSION = "run.configuration_version"
    OUTPUTS = "outputs"


# ---- DTOs ----


class StateVersion(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    id: str = Field(..., alias="id")
    created_at: datetime = Field(..., alias="created-at")
    hosted_state_download_url: str | None = Field(
        None, alias="hosted-state-download-url"
    )
    hosted_state_upload_url: str | None = Field(None, alias="hosted-state-upload-url")
    status: StateVersionStatus | None = Field(None, alias="status")

    # Optional/advanced fields (present on newer servers; keep loose)
    resources_processed: bool | None = Field(None, alias="resources-processed")
    modules: dict | None = None
    providers: dict | None = None
    resources: list[dict] | None = None


class StateVersionCreateOptions(BaseModel):
    """
    Options for POST /workspaces/:id/state-versions.
    If you omit inline content (recommended), you must include serial & md5.
    """

    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    serial: int
    md5: str
    lineage: str | None = None
    terraform_version: str | None = Field(None, alias="terraform-version")

    # Optional one-shot create path (if you don't use signed upload)
    state: str | None = None  # base64-encoded tfstate
    json_state: str | None = Field(None, alias="json-state")
    json_state_outputs: str | None = Field(None, alias="json-state-outputs")


class StateVersionCurrentOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    include: list[StateVersionIncludeOpt] | None = None


class StateVersionReadOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    include: list[StateVersionIncludeOpt] | None = None


class StateVersionListOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    # Standard pagination + filters
    page_number: int | None = Field(None, alias="page[number]")
    page_size: int | None = Field(None, alias="page[size]")
    organization: str | None = Field(None, alias="filter[organization][name]")
    workspace: str | None = Field(None, alias="filter[workspace][name]")


class StateVersionList(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    items: list[StateVersion] = Field(default_factory=list)
    current_page: int | None = None
    total_pages: int | None = None
    total_count: int | None = None
