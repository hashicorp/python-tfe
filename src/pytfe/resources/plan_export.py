# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any

from .._jsonapi import attach_jsonapi
from ..errors import InvalidPlanExportIDError, TFEError
from ..models.plan_export import PlanExport, PlanExportCreateOptions
from ..utils import valid_string_id
from ._base import _Service


def _plan_export_from(
    data: dict[str, Any], included: list[dict[str, Any]] | None = None
) -> PlanExport:
    """Parse a JSON:API plan-export resource object into a PlanExport."""
    attrs = dict(data.get("attributes") or {})
    attrs["id"] = data.get("id")
    return attach_jsonapi(PlanExport.model_validate(attrs), data, included)


class PlanExports(_Service):
    """Service for exporting Terraform plan data (e.g. Sentinel mock bundles)."""

    def create(self, options: PlanExportCreateOptions) -> PlanExport:
        """Export a plan. The plan and data-type are supplied via ``options``."""
        payload = {
            "data": {
                "type": "plan-exports",
                "attributes": {"data-type": options.data_type.value},
                "relationships": {
                    "plan": {"data": {"type": "plans", "id": options.plan_id}}
                },
            }
        }
        r = self.t.request("POST", "/api/v2/plan-exports", json_body=payload)
        body = r.json()
        return _plan_export_from(body["data"], body.get("included"))

    def read(self, plan_export_id: str) -> PlanExport:
        """Read a plan export by its ID."""
        if not valid_string_id(plan_export_id):
            raise InvalidPlanExportIDError()
        r = self.t.request("GET", f"/api/v2/plan-exports/{plan_export_id}")
        body = r.json()
        return _plan_export_from(body["data"], body.get("included"))

    def delete(self, plan_export_id: str) -> None:
        """Delete a plan export by its ID."""
        if not valid_string_id(plan_export_id):
            raise InvalidPlanExportIDError()
        self.t.request("DELETE", f"/api/v2/plan-exports/{plan_export_id}")

    def download(self, plan_export_id: str) -> bytes:
        """Download a plan export's data as a ``.tar.gz`` archive (bytes).

        The endpoint 302-redirects to a temporary, presigned URL for the
        archive. That URL self-authorises via query parameters, so the API
        bearer must not be forwarded to the (cross-origin) blob host — this
        mirrors go-tfe, whose HTTP client also strips auth on the cross-host hop.
        """
        if not valid_string_id(plan_export_id):
            raise InvalidPlanExportIDError()
        resp = self.t.request(
            "GET",
            f"/api/v2/plan-exports/{plan_export_id}/download",
            allow_redirects=False,
        )
        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location") or resp.headers.get("location")
            if not location:
                raise TFEError(
                    "plan-export download redirect did not include a Location header"
                )
            blob = self.t.request("GET", location, include_auth=False)
            return blob.content
        return resp.content
