from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field, ConfigDict


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
    hosted_state_download_url: Optional[str] = Field(None, alias="hosted-state-download-url")
    hosted_state_upload_url: Optional[str] = Field(None, alias="hosted-state-upload-url")
    status: Optional[StateVersionStatus] = Field(None, alias="status")

    # Optional/advanced fields (present on newer servers; keep loose)
    resources_processed: Optional[bool] = Field(None, alias="resources-processed")
    modules: Optional[dict] = None
    providers: Optional[dict] = None
    resources: Optional[List[dict]] = None


class StateVersionCreateOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    # Mirrors go-tfe: optional hint payload
    json_state_outputs: Optional[str] = Field(None, alias="json-state-outputs")


class StateVersionCurrentOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    include: Optional[List[StateVersionIncludeOpt]] = None


class StateVersionReadOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    include: Optional[List[StateVersionIncludeOpt]] = None


class StateVersionListOptions(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    # Standard pagination + filters
    page_number: Optional[int] = Field(None, alias="page[number]")
    page_size: Optional[int] = Field(None, alias="page[size]")
    organization: Optional[str] = Field(None, alias="filter[organization][name]")
    workspace: Optional[str] = Field(None, alias="filter[workspace][name]")


class StateVersionList(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_by_name=True)

    items: List[StateVersion] = Field(default_factory=list)
    current_page: Optional[int] = None
    total_pages: Optional[int] = None
    total_count: Optional[int] = None
