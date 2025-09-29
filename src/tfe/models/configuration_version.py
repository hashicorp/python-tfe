from __future__ import annotations

from pydantic import BaseModel, Field


class ConfigurationVersion(BaseModel):
    id: str
    auto_queue_runs: bool = Field(..., alias="auto-queue-runs")
    error: str | None = Field(None, alias="error")
    error_message: str | None = Field(None, alias="error-message")
    # source: ConfigurationSource = Field(..., alias="source")
    speculative: bool = Field(..., alias="speculative")
    provisional: bool = Field(..., alias="provisional")
    # status: ConfigurationStatus = Field(..., alias="status")
    # status_timestamps: CVStatusTimestamps = Field(..., alias="status-timestamps")
    upload_url: str | None = Field(None, alias="upload-url")
    # ingress_attributes: IngressAttributes | None = Field(None, alias="ingress-attributes")
