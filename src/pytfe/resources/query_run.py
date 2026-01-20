from __future__ import annotations

import io
from collections.abc import Iterator
from typing import Any

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
        """Iterate through all query runs for the given workspace.

        This method automatically handles pagination and yields QueryRun objects one at a time.

        Args:
            workspace_id: The ID of the workspace
            options: Optional list options (page_size, include, etc.)

        Yields:
            QueryRun objects one at a time

        Example:
            for query_run in client.query_runs.list(workspace_id):
                print(f"Query Run: {query_run.id} - Status: {query_run.status}")
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
            yield QueryRun.model_validate(attrs)

    def create(self, options: QueryRunCreateOptions) -> QueryRun:
        """Create a new query run."""
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

        return QueryRun.model_validate(attrs)

    def read(self, query_run_id: str) -> QueryRun:
        """Read a query run by its ID."""
        if not valid_string_id(query_run_id):
            raise InvalidQueryRunIDError()

        r = self.t.request("GET", f"/api/v2/queries/{query_run_id}")

        jd = r.json()
        data = jd.get("data", {})
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")

        return QueryRun.model_validate(attrs)

    def read_with_options(
        self, query_run_id: str, options: QueryRunReadOptions
    ) -> QueryRun:
        """Read a query run with additional options."""
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

        return QueryRun.model_validate(attrs)

    def logs(self, query_run_id: str) -> io.IOBase:
        """Retrieve the logs for a query run.

        Returns an IO stream that can be read to get the log content.
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

        Returns 202 on success with empty body.
        """
        if not valid_string_id(query_run_id):
            raise InvalidQueryRunIDError()

        self.t.request(
            "POST",
            f"/api/v2/queries/{query_run_id}/actions/cancel",
        )

    def force_cancel(self, query_run_id: str) -> None:
        """Force cancel a query run.

        Returns 202 on success with empty body.
        """
        if not valid_string_id(query_run_id):
            raise InvalidQueryRunIDError()

        self.t.request(
            "POST",
            f"/api/v2/queries/{query_run_id}/actions/force-cancel",
        )
