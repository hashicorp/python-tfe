# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Any

from .._jsonapi import attach_jsonapi
from ..errors import InvalidCostEstimateIDError
from ..models.cost_estimate import CostEstimate
from ..utils import valid_string_id
from ._base import _Service


def _cost_estimate_from(
    data: dict[str, Any], included: list[dict[str, Any]] | None = None
) -> CostEstimate:
    """Parse a JSON:API cost-estimate resource object into a CostEstimate."""
    attrs = dict(data.get("attributes") or {})
    attrs["id"] = data.get("id")
    return attach_jsonapi(CostEstimate.model_validate(attrs), data, included)


class CostEstimates(_Service):
    """Service for reading run cost estimates."""

    def read(self, cost_estimate_id: str) -> CostEstimate:
        """Read a cost estimate by its ID.

        Cost estimates have no list endpoint; find an ID in a run's
        ``relationships.cost-estimate``.

        Args:
            cost_estimate_id: The cost estimate ID (e.g. ``"ce-xxxxxxxx"``).

        Returns:
            The :class:`CostEstimate`.

        Raises:
            InvalidCostEstimateIDError: If ``cost_estimate_id`` is not valid.
            TFEError: If the API request fails.

        Example:
            >>> cost_estimate = client.cost_estimates.read("ce-BPvFFrYCqRV6qVBK")
            >>> print(cost_estimate.status)
        """
        if not valid_string_id(cost_estimate_id):
            raise InvalidCostEstimateIDError()
        r = self.t.request("GET", f"/api/v2/cost-estimates/{cost_estimate_id}")
        body = r.json()
        data = body.get("data")
        # The API docs show the resource wrapped in a single-element array;
        # accept both that and the conventional single-object envelope.
        if isinstance(data, list):
            data = data[0] if data else {}
        return _cost_estimate_from(data or {}, body.get("included"))

    def logs(self, cost_estimate_id: str) -> str:
        """Read a cost estimate's logs as text.

        Logs are produced once the estimate finishes running; reading them
        before then may return an empty body.

        Args:
            cost_estimate_id: The cost estimate ID (e.g. ``"ce-xxxxxxxx"``).

        Returns:
            The log output as text.

        Raises:
            InvalidCostEstimateIDError: If ``cost_estimate_id`` is not valid.
            TFEError: If the API request fails.

        Example:
            >>> logs = client.cost_estimates.logs("ce-BPvFFrYCqRV6qVBK")
            >>> print(logs)
        """
        if not valid_string_id(cost_estimate_id):
            raise InvalidCostEstimateIDError()
        r = self.t.request("GET", f"/api/v2/cost-estimates/{cost_estimate_id}/output")
        return r.text
