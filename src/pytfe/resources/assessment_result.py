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
        """Read an assessment result by ID.

        Args:
            assessment_result_id: The assessment result ID
                (e.g. ``"asmtres-xxxxxxxx"``).

        Returns:
            The :class:`AssessmentResult`.

        Raises:
            InvalidAssessmentResultIDError: If ``assessment_result_id`` is not valid.
            TFEError: If the API request fails.

        Example:
            >>> result = client.assessment_results.read("asmtres-UG5rE9L1373hMYMA")
            >>> print(result.succeeded)
        """
        if not valid_string_id(assessment_result_id):
            raise InvalidAssessmentResultIDError()
        r = self.t.request("GET", f"/api/v2/assessment-results/{assessment_result_id}")
        body = r.json()
        data = (body or {}).get("data") or {} if isinstance(body, dict) else {}
        included = body.get("included") if isinstance(body, dict) else None
        return _assessment_result_from(data, included)

    def json_output(self, assessment_result_id: str) -> dict[str, Any] | None:
        """Read the JSON plan output for an assessment result.

        Only available once the assessment has succeeded and produced JSON output.
        Requires a user or team token with workspace admin access.

        Args:
            assessment_result_id: The assessment result ID
                (e.g. ``"asmtres-xxxxxxxx"``).

        Returns:
            The ``dict[str, Any]``, or ``None`` when output is not yet ready
            (HTTP 204) or the blob response is not JSON.

        Raises:
            InvalidAssessmentResultIDError: If ``assessment_result_id`` is not valid.
            TFEError: If the API request fails.

        Example:
            >>> output = client.assessment_results.json_output(
            ...     "asmtres-UG5rE9L1373hMYMA"
            ... )
            >>> print(output is None)
        """
        if not valid_string_id(assessment_result_id):
            raise InvalidAssessmentResultIDError()
        resp = self._follow_blob(
            f"/api/v2/assessment-results/{assessment_result_id}/json-output"
        )
        return self._as_json(resp)

    def json_schema(self, assessment_result_id: str) -> dict[str, Any] | None:
        """Read the JSON provider schema for an assessment result.

        Requires a user or team token with workspace admin access.

        Args:
            assessment_result_id: The assessment result ID
                (e.g. ``"asmtres-xxxxxxxx"``).

        Returns:
            The ``dict[str, Any]``, or ``None`` when the schema is not yet ready
            (HTTP 204) or the blob response is not JSON.

        Raises:
            InvalidAssessmentResultIDError: If ``assessment_result_id`` is not valid.
            TFEError: If the API request fails.

        Example:
            >>> schema = client.assessment_results.json_schema(
            ...     "asmtres-UG5rE9L1373hMYMA"
            ... )
            >>> print(schema is None)
        """
        if not valid_string_id(assessment_result_id):
            raise InvalidAssessmentResultIDError()
        resp = self._follow_blob(
            f"/api/v2/assessment-results/{assessment_result_id}/json-schema"
        )
        return self._as_json(resp)

    def log_output(self, assessment_result_id: str) -> str:
        """Read the Terraform JSON log output for an assessment result.

        Requires a user or team token with workspace admin access.

        Args:
            assessment_result_id: The assessment result ID
                (e.g. ``"asmtres-xxxxxxxx"``).

        Returns:
            The ``str``; returns an empty string when there is no log output yet
            (HTTP 204).

        Raises:
            InvalidAssessmentResultIDError: If ``assessment_result_id`` is not valid.
            TFEError: If the API request fails.

        Example:
            >>> log = client.assessment_results.log_output(
            ...     "asmtres-UG5rE9L1373hMYMA"
            ... )
            >>> print(log[:80])
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
