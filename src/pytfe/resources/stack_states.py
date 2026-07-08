# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import builtins
from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi, parse_relationships
from ..errors import InvalidStackIDError, InvalidStackStateIDError
from ..models.stack import Stack
from ..models.stack_deployment_run import StackDeploymentRun
from ..models.stack_state import StackState, StackStateListOptions
from ..utils import valid_string_id
from ._base import _Service


class StackStates(_Service):
    """Service for listing, reading, and downloading stack states."""

    def list(
        self,
        stack_id: str,
        options: StackStateListOptions | None = None,
    ) -> Iterator[StackState]:
        """List the states for a stack.

        Args:
            stack_id: The stack ID (e.g. ``"st-abc123"``).
            options: Optional pagination, as a :class:`StackStateListOptions`.

        Returns:
            A single-use ``Iterator[StackState]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidStackIDError: If ``stack_id`` is empty or malformed.
            TFEError: If the API request fails.

        Example:
            >>> for state in client.stack_states.list("st-abc123"):
            ...     print(state.id, state.deployment, state.is_current)
        """
        if not valid_string_id(stack_id):
            raise InvalidStackIDError()
        path = f"/api/v2/stacks/{stack_id}/stack-states"
        params: dict[str, Any] = {}
        if options and options.page_size is not None:
            params["page[size]"] = options.page_size
        for item in self._list(path=path, params=params):
            yield self._stack_state_from(item)

    def read(self, stack_state_id: str) -> StackState:
        """Read a stack state by its ID.

        Args:
            stack_state_id: The stack state ID (e.g. ``"ss-abc123"``).

        Returns:
            The :class:`StackState`.

        Raises:
            InvalidStackStateIDError: If ``stack_state_id`` is empty or malformed.
            TFEError: If the API request fails.

        Example:
            >>> state = client.stack_states.read("ss-abc123")
            >>> print(state.is_current, state.generation)
        """
        if not valid_string_id(stack_state_id):
            raise InvalidStackStateIDError()
        path = f"/api/v2/stack-states/{stack_state_id}"
        r = self.t.request("GET", path=path)
        payload = r.json()
        data = payload.get("data", {})
        return self._stack_state_from(data, payload.get("included"))

    def download_description(self, stack_state_id: str) -> bytes:
        """Download the state description for a stack state.

        Follows the redirect to the archivist URL and returns the raw bytes.

        Args:
            stack_state_id: The stack state ID (e.g. ``"ss-abc123"``).

        Returns:
            The raw description content as ``bytes``.

        Raises:
            InvalidStackStateIDError: If ``stack_state_id`` is empty or malformed.
            TFEError: If the API request fails.

        Example:
            >>> content = client.stack_states.download_description("ss-abc123")
            >>> print(content.decode())
        """
        if not valid_string_id(stack_state_id):
            raise InvalidStackStateIDError()
        path = f"/api/v2/stack-states/{stack_state_id}/description"
        resp = self.t.request("GET", path=path)
        return resp.content

    def _stack_state_from(
        self,
        data: dict[str, Any],
        included: builtins.list[dict[str, Any]] | None = None,
    ) -> StackState:
        """Parse a StackState from API response data."""
        attrs = dict(data.get("attributes", {}))
        attrs["id"] = data.get("id")
        attrs.update(
            parse_relationships(
                data.get("relationships"),
                {
                    "stack": Stack,
                    "stack-deployment-run": StackDeploymentRun,
                },
                included=included,
            )
        )
        return attach_jsonapi(StackState.model_validate(attrs), data, included)
