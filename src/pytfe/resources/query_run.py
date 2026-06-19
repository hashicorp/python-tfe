# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import io
from collections.abc import Iterator
from typing import Any

from .._jsonapi import attach_jsonapi
from ..errors import (
    InvalidQueryRunIDError,
    InvalidWorkspaceIDError,
)
from ..models.query_run import (
    QueryRun,
    QueryRunCreateOptions,
    QueryRunListOptions,
    QueryRunReadOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class QueryRuns(_Service):
    """Query Runs API for Terraform Enterprise."""

    def list(
        self, workspace_id: str, options: QueryRunListOptions | None = None
    ) -> Iterator[QueryRun]:
        """List query runs for a workspace.

        Args:
            workspace_id: The workspace ID (e.g. ``"ws-xxxxxxxx"``).
            options: Optional pagination and include options, as a
                :class:`QueryRunListOptions`.

        Returns:
            A single-use ``Iterator[QueryRun]``. Wrap with ``list(...)`` to
            materialize the results or iterate more than once.

        Raises:
            InvalidWorkspaceIDError: If ``workspace_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> for query_run in client.query_runs.list("ws-abc123"):
            ...     print(query_run.id, query_run.status)
        """
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        params: dict[str, Any] = {}
        if options:
            params = options.model_dump(by_alias=True, exclude_none=True)
            # Convert include list to comma-separated string
            if "include" in params and params["include"] and options.include:
                params["include"] = ",".join([i.value for i in options.include])

        path = f"/api/v2/workspaces/{workspace_id}/queries"
        for item in self._list(path, params=params):
            attrs = item.get("attributes", {})
            attrs["id"] = item.get("id")
            yield attach_jsonapi(QueryRun.model_validate(attrs), item)

    def create(self, options: QueryRunCreateOptions) -> QueryRun:
        """Create a query run.

        Args:
            options: The query run settings, as a :class:`QueryRunCreateOptions`.

        Returns:
            The created :class:`QueryRun`.

        Raises:
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import QueryRunCreateOptions, QueryRunSource
            >>> query_run = client.query_runs.create(
            ...     QueryRunCreateOptions(
            ...         source=QueryRunSource.API,
            ...         workspace_id="ws-abc123",
            ...     )
            ... )
        """
        attrs = options.model_dump(by_alias=True, exclude_none=True)

        # Build relationships
        relationships: dict[str, Any] = {}

        if workspace_id := attrs.pop("workspace-id", None):
            relationships["workspace"] = {
                "data": {"type": "workspaces", "id": workspace_id}
            }

        if config_version_id := attrs.pop("configuration-version-id", None):
            relationships["configuration-version"] = {
                "data": {"type": "configuration-versions", "id": config_version_id}
            }

        body: dict[str, Any] = {
            "data": {
                "type": "queries",
                "attributes": attrs,
            }
        }

        if relationships:
            body["data"]["relationships"] = relationships

        r = self.t.request(
            "POST",
            "/api/v2/queries",
            json_body=body,
        )

        jd = r.json()
        data = jd.get("data", {})
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")

        return attach_jsonapi(QueryRun.model_validate(attrs), data, jd.get("included"))

    def read(self, query_run_id: str) -> QueryRun:
        """Read a query run by its ID.

        Args:
            query_run_id: The query run ID (e.g. ``"qr-xxxxxxxx"``).

        Returns:
            The :class:`QueryRun`.

        Raises:
            InvalidQueryRunIDError: If ``query_run_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> query_run = client.query_runs.read("qr-123abc456def")
            >>> print(query_run.status)
        """
        if not valid_string_id(query_run_id):
            raise InvalidQueryRunIDError()

        r = self.t.request("GET", f"/api/v2/queries/{query_run_id}")

        jd = r.json()
        data = jd.get("data", {})
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")

        return attach_jsonapi(QueryRun.model_validate(attrs), data, jd.get("included"))

    def read_with_options(
        self, query_run_id: str, options: QueryRunReadOptions
    ) -> QueryRun:
        """Read a query run by its ID with include options.

        Args:
            query_run_id: The query run ID (e.g. ``"qr-xxxxxxxx"``).
            options: Include options, as a :class:`QueryRunReadOptions`.

        Returns:
            The :class:`QueryRun`.

        Raises:
            InvalidQueryRunIDError: If ``query_run_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> from pytfe.models import QueryRunIncludeOpt, QueryRunReadOptions
            >>> query_run = client.query_runs.read_with_options(
            ...     "qr-123abc456def",
            ...     QueryRunReadOptions(include=[QueryRunIncludeOpt.CREATED_BY]),
            ... )
        """
        if not valid_string_id(query_run_id):
            raise InvalidQueryRunIDError()

        params = options.model_dump(by_alias=True, exclude_none=True)
        # Convert include list to comma-separated string
        if "include" in params and params["include"] and options.include:
            params["include"] = ",".join([i.value for i in options.include])

        r = self.t.request("GET", f"/api/v2/queries/{query_run_id}", params=params)

        jd = r.json()
        data = jd.get("data", {})
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")

        return attach_jsonapi(QueryRun.model_validate(attrs), data, jd.get("included"))

    def logs(self, query_run_id: str) -> io.IOBase:
        """Retrieve logs for a query run.

        Args:
            query_run_id: The query run ID (e.g. ``"qr-xxxxxxxx"``).

        Returns:
            The ``IOBase`` stream containing the log bytes.

        Raises:
            InvalidQueryRunIDError: If ``query_run_id`` is not a valid resource ID.
            ValueError: If the query run does not have a log URL.
            TFEError: If the API request fails.

        Example:
            >>> stream = client.query_runs.logs("qr-123abc456def")
            >>> stream.read().decode()
        """
        if not valid_string_id(query_run_id):
            raise InvalidQueryRunIDError()

        # First get the query run to retrieve the log read URL
        query_run = self.read(query_run_id)

        if not query_run.log_read_url:
            raise ValueError(f"Query run {query_run_id} does not have a log URL")

        # Fetch the logs from the URL (absolute URLs are handled by _build_url)
        r = self.t.request("GET", query_run.log_read_url)

        # Return the content as a BytesIO stream
        return io.BytesIO(r.content)

    def cancel(self, query_run_id: str) -> None:
        """Cancel a query run.

        Args:
            query_run_id: The query run ID (e.g. ``"qr-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidQueryRunIDError: If ``query_run_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.query_runs.cancel("qr-123abc456def")
        """
        if not valid_string_id(query_run_id):
            raise InvalidQueryRunIDError()

        self.t.request(
            "POST",
            f"/api/v2/queries/{query_run_id}/actions/cancel",
        )

    def force_cancel(self, query_run_id: str) -> None:
        """Force cancel a query run.

        Args:
            query_run_id: The query run ID (e.g. ``"qr-xxxxxxxx"``).

        Returns:
            None.

        Raises:
            InvalidQueryRunIDError: If ``query_run_id`` is not a valid resource ID.
            TFEError: If the API request fails.

        Example:
            >>> client.query_runs.force_cancel("qr-123abc456def")
        """
        if not valid_string_id(query_run_id):
            raise InvalidQueryRunIDError()

        self.t.request(
            "POST",
            f"/api/v2/queries/{query_run_id}/actions/force-cancel",
        )
