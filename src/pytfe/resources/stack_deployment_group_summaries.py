# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi, parse_relationships
from ..errors import InvalidStackConfigurationIDError
from ..models.stack_deployment_group import (
    StackDeploymentGroup,
    StackDeploymentGroupSummary,
    StackDeploymentGroupSummaryListOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class StackDeploymentGroupSummaries(_Service):
    """Service for listing stack deployment group summaries."""

    def list(
        self,
        stack_configuration_id: str,
        options: StackDeploymentGroupSummaryListOptions | None = None,
    ) -> Iterator[StackDeploymentGroupSummary]:
        """List the deployment group summaries for a stack configuration.

        Args:
            stack_configuration_id: The stack configuration ID (e.g. ``"stc-abc123"``).
            options: Optional pagination, as a
                :class:`StackDeploymentGroupSummaryListOptions`.

        Returns:
            A single-use ``Iterator[StackDeploymentGroupSummary]``. Wrap with
            ``list(...)`` to materialize the results or iterate more than once.

        Raises:
            InvalidStackConfigurationIDError: If ``stack_configuration_id`` is empty
                or malformed.
            TFEError: If the API request fails.

        Example:
            >>> for summary in client.stack_deployment_group_summaries.list("stc-abc123"):
            ...     print(summary.name, summary.status, summary.status_counts)
        """
        if not valid_string_id(stack_configuration_id):
            raise InvalidStackConfigurationIDError()
        path = f"/api/v2/stack-configurations/{stack_configuration_id}/stack-deployment-group-summaries"
        params: dict[str, Any] = {}
        if options and options.page_size is not None:
            params["page[size]"] = options.page_size
        for item in self._list(path=path, params=params):
            yield self._summary_from(item)

    def _summary_from(self, data: dict[str, Any]) -> StackDeploymentGroupSummary:
        """Parse a StackDeploymentGroupSummary from API response data."""
        attrs = dict(data.get("attributes", {}))
        attrs["id"] = data.get("id")
        attrs.update(
            parse_relationships(
                data.get("relationships"),
                {"stack-deployment-group": StackDeploymentGroup},
            )
        )
        return attach_jsonapi(
            StackDeploymentGroupSummary.model_validate(attrs), data, None
        )
