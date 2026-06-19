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
        """Create a plan export.

        Args:
            options: The plan export request, as a :class:`PlanExportCreateOptions`.

        Returns:
            The created :class:`PlanExport`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import PlanExportCreateOptions
            >>> export = client.plan_exports.create(
            ...     PlanExportCreateOptions(plan_id="plan-8F5JFydVYAmtTjET")
            ... )
        """
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
        """Read a plan export by its ID.

        Args:
            plan_export_id: The plan export ID (e.g. ``"pe-xxxxxxxx"``).

        Returns:
            The :class:`PlanExport`.

        Raises:
            InvalidPlanExportIDError: If ``plan_export_id`` is not a valid resource
                ID.
            TFEError: If the API request fails.

        Example:
            >>> export = client.plan_exports.read("pe-3yVQZvHzf5j3WRJ1")
            >>> print(export.status)
        """
        if not valid_string_id(plan_export_id):
            raise InvalidPlanExportIDError()
        r = self.t.request("GET", f"/api/v2/plan-exports/{plan_export_id}")
        body = r.json()
        return _plan_export_from(body["data"], body.get("included"))

    def delete(self, plan_export_id: str) -> None:
        """Delete a plan export by its ID.

        Args:
            plan_export_id: The plan export ID (e.g. ``"pe-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidPlanExportIDError: If ``plan_export_id`` is not a valid resource
                ID.
            TFEError: If the API request fails.

        Example:
            >>> client.plan_exports.delete("pe-3yVQZvHzf5j3WRJ1")
        """
        if not valid_string_id(plan_export_id):
            raise InvalidPlanExportIDError()
        self.t.request("DELETE", f"/api/v2/plan-exports/{plan_export_id}")

    def download(self, plan_export_id: str) -> bytes:
        """Download a plan export archive.

        The endpoint may redirect to a temporary, presigned URL for the archive; the
        SDK follows that URL and returns the response body.

        Args:
            plan_export_id: The plan export ID (e.g. ``"pe-xxxxxxxx"``).

        Returns:
            The raw bytes (the SDK follows the storage/redirect URL for you).

        Raises:
            InvalidPlanExportIDError: If ``plan_export_id`` is not a valid resource
                ID.
            TFEError: If the API request fails or a redirect is missing ``Location``.

        Example:
            >>> archive = client.plan_exports.download("pe-3yVQZvHzf5j3WRJ1")
            >>> len(archive) > 0
            True
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
