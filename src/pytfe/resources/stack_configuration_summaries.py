# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi
from ..errors import InvalidStackIDError
from ..models.stack_configuration import (
    StackConfigurationSummary,
    StackConfigurationSummaryListOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class StackConfigurationSummaries(_Service):
    """Service for listing stack configuration summaries."""

    def list(
        self,
        stack_id: str,
        options: StackConfigurationSummaryListOptions | None = None,
    ) -> Iterator[StackConfigurationSummary]:
        """List the configuration summaries for a stack.

        Args:
            stack_id: The stack ID (e.g. ``"st-abc123"``).
            options: Optional pagination, as a
                :class:`StackConfigurationSummaryListOptions`.

        Returns:
            A single-use ``Iterator[StackConfigurationSummary]``. Wrap with
            ``list(...)`` to materialize the results or iterate more than once.

        Raises:
            InvalidStackIDError: If ``stack_id`` is empty or malformed.
            TFEError: If the API request fails.

        Example:
            >>> for summary in client.stack_configuration_summaries.list("st-abc123"):
            ...     print(summary.id, summary.sequence_number, summary.status)
        """
        if not valid_string_id(stack_id):
            raise InvalidStackIDError()
        path = f"/api/v2/stacks/{stack_id}/stack-configuration-summaries"
        params: dict[str, Any] = {}
        if options and options.page_size is not None:
            params["page[size]"] = options.page_size
        for item in self._list(path=path, params=params):
            yield self._summary_from(item)

    def _summary_from(self, data: dict[str, Any]) -> StackConfigurationSummary:
        """Parse a StackConfigurationSummary from API response data."""
        attrs = dict(data.get("attributes", {}))
        attrs["id"] = data.get("id")
        return attach_jsonapi(
            StackConfigurationSummary.model_validate(attrs), data, None
        )
