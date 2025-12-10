from __future__ import annotations

import io
from typing import Any

from ..errors import (
    InvalidQueryRunIDError,
    InvalidWorkspaceIDError,
)
from ..models.query_run import (
    QueryRun,
    QueryRunCancelOptions,
    QueryRunCreateOptions,
    QueryRunForceCancelOptions,
    QueryRunList,
    QueryRunListOptions,
    QueryRunReadOptions,
)
from ..utils import valid_string_id
from ._base import _Service


class QueryRuns(_Service):
    """Query Runs API for Terraform Enterprise."""

    def list(
        self, workspace_id: str, options: QueryRunListOptions | None = None
    ) -> QueryRunList:
        """List query runs for the given workspace."""
        if not valid_string_id(workspace_id):
            raise InvalidWorkspaceIDError()

        params = (
            options.model_dump(by_alias=True, exclude_none=True) if options else None
        )

        r = self.t.request(
            "GET",
            f"/api/v2/workspaces/{workspace_id}/queries",
            params=params,
        )

        jd = r.json()
        items = []
        meta = jd.get("meta", {})
        pagination = meta.get("pagination", {})

        for d in jd.get("data", []):
            attrs = d.get("attributes", {})
            attrs["id"] = d.get("id")
            items.append(QueryRun.model_validate(attrs))

        return QueryRunList(
            items=items,
            current_page=pagination.get("current-page"),
            total_pages=pagination.get("total-pages"),
            prev_page=pagination.get("prev-page"),
            next_page=pagination.get("next-page"),
            total_count=pagination.get("total-count"),
        )

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

    def cancel(
        self, query_run_id: str, options: QueryRunCancelOptions | None = None
    ) -> None:
        """Cancel a query run.
        
        Returns 202 on success with empty body.
        """
        if not valid_string_id(query_run_id):
            raise InvalidQueryRunIDError()

        body: dict[str, Any] | None = None
        if options:
            attrs = options.model_dump(by_alias=True, exclude_none=True)
            if attrs:
                body = {"data": {"attributes": attrs}}

        self.t.request(
            "POST",
            f"/api/v2/queries/{query_run_id}/actions/cancel",
            json_body=body,
        )

    def force_cancel(
        self, query_run_id: str, options: QueryRunForceCancelOptions | None = None
    ) -> None:
        """Force cancel a query run.
        
        Returns 202 on success with empty body.
        """
        if not valid_string_id(query_run_id):
            raise InvalidQueryRunIDError()

        body: dict[str, Any] | None = None
        if options:
            attrs = options.model_dump(by_alias=True, exclude_none=True)
            if attrs:
                body = {"data": {"attributes": attrs}}

        self.t.request(
            "POST",
            f"/api/v2/queries/{query_run_id}/actions/force-cancel",
            json_body=body,
        )
