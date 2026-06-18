# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Read health assessment (drift detection / continuous validation) results.

``GET /api/v2/assessment-results/:id`` returns the assessment summary; the
``/json-output``, ``/json-schema`` and ``/log-output`` companion endpoints
return the underlying plan JSON, provider schema, and Terraform JSON log.

Those output endpoints do not adhere to JSON:API and (per the API docs) require
a **user or team token with admin access to the workspace** — organization
tokens cannot read them.

API reference:
https://developer.hashicorp.com/terraform/cloud-docs/api-docs/assessment-results
"""

from __future__ import annotations

from typing import Any

import httpx

from .._jsonapi import attach_jsonapi
from ..errors import InvalidAssessmentResultIDError, TFEError
from ..models.assessment_result import AssessmentResult
from ..utils import valid_string_id
from ._base import _Service


def _assessment_result_from(
    data: dict[str, Any], included: list[dict[str, Any]] | None = None
) -> AssessmentResult:
    """Parse a JSON:API assessment-results resource into an AssessmentResult."""
    attrs = dict(data.get("attributes") or {})
    attrs["id"] = data.get("id")
    return attach_jsonapi(AssessmentResult.model_validate(attrs), data, included)


class AssessmentResults(_Service):
    """Service for reading workspace health assessment results."""

    def read(self, assessment_result_id: str) -> AssessmentResult:
        """Read an assessment result by its ID."""
        if not valid_string_id(assessment_result_id):
            raise InvalidAssessmentResultIDError()
        r = self.t.request("GET", f"/api/v2/assessment-results/{assessment_result_id}")
        body = r.json()
        data = (body or {}).get("data") or {} if isinstance(body, dict) else {}
        included = body.get("included") if isinstance(body, dict) else None
        return _assessment_result_from(data, included)

    def json_output(self, assessment_result_id: str) -> dict[str, Any] | None:
        """Return the JSON plan output for an assessment result.

        Only available once the assessment has succeeded and produced JSON
        output. Returns ``None`` when output is not yet ready (HTTP 204); the
        transport raises (e.g. ``NotFound``) when the assessment produced no
        output, such as when it did not succeed. Requires a user/team token with
        workspace admin access.
        """
        if not valid_string_id(assessment_result_id):
            raise InvalidAssessmentResultIDError()
        resp = self._follow_blob(
            f"/api/v2/assessment-results/{assessment_result_id}/json-output"
        )
        return self._as_json(resp)

    def json_schema(self, assessment_result_id: str) -> dict[str, Any] | None:
        """Return the JSON provider schema for an assessment result.

        Returns ``None`` when the schema is not yet ready (HTTP 204); the
        transport raises when the assessment produced no schema (e.g. it did not
        succeed). Requires a user/team token with workspace admin access.
        """
        if not valid_string_id(assessment_result_id):
            raise InvalidAssessmentResultIDError()
        resp = self._follow_blob(
            f"/api/v2/assessment-results/{assessment_result_id}/json-schema"
        )
        return self._as_json(resp)

    def log_output(self, assessment_result_id: str) -> str:
        """Return the Terraform JSON log output for an assessment result as text.

        Returns an empty string when there is no log output yet (HTTP 204).
        Requires a user/team token with workspace admin access.
        """
        if not valid_string_id(assessment_result_id):
            raise InvalidAssessmentResultIDError()
        resp = self._follow_blob(
            f"/api/v2/assessment-results/{assessment_result_id}/log-output"
        )
        return resp.text if resp is not None else ""

    def _follow_blob(self, path: str) -> httpx.Response | None:
        """Fetch a non-JSON:API output endpoint, following a blob redirect.

        These endpoints may 307-redirect to a HashiCorp object-storage URL
        (Archivist), which requires the API bearer; we re-issue the request to
        the ``Location`` with auth (matching the plan ``json-output`` flow).
        Returns ``None`` when the API responds ``204 No Content``.
        """
        resp = self.t.request("GET", path, allow_redirects=False)
        if resp.status_code == 204:
            return None
        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location") or resp.headers.get("location")
            if not location:
                raise TFEError(
                    "assessment-results output redirect did not include a Location header"
                )
            return self.t.request("GET", location)
        return resp

    @staticmethod
    def _as_json(resp: httpx.Response | None) -> dict[str, Any] | None:
        if resp is None:
            return None
        try:
            data = resp.json()
        except Exception:
            return None
        if data is None:
            return None
        return data if isinstance(data, dict) else {"data": data}
