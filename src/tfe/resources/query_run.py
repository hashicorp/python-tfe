from __future__ import annotations

from typing import Any

from ..errors import (
    InvalidOrgError,
    InvalidQueryRunIDError,
)
from ..models.query_run import (
    QueryRun,
    QueryRunCancelOptions,
    QueryRunCreateOptions,
    QueryRunForceCancelOptions,
    QueryRunList,
    QueryRunListOptions,
    QueryRunLogs,
    QueryRunReadOptions,
    QueryRunResults,
)
from ..utils import valid_string_id
from ._base import _Service


class QueryRuns(_Service):
    """Query Runs API for Terraform Enterprise."""

    def list(
        self, organization: str, options: QueryRunListOptions | None = None
    ) -> QueryRunList:
        """List query runs for the given organization."""
        if not valid_string_id(organization):
            raise InvalidOrgError()

        params = (
            options.model_dump(by_alias=True, exclude_none=True) if options else None
        )

        r = self.t.request(
            "GET",
            f"/api/v2/organizations/{organization}/query-runs",
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

    def create(self, organization: str, options: QueryRunCreateOptions) -> QueryRun:
        """Create a new query run for the given organization."""
        if not valid_string_id(organization):
            raise InvalidOrgError()

        attrs = options.model_dump(by_alias=True, exclude_none=True)
        body: dict[str, Any] = {
            "data": {
                "attributes": attrs,
                "type": "query-runs",
            }
        }

        r = self.t.request(
            "POST",
            f"/api/v2/organizations/{organization}/query-runs",
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

        r = self.t.request("GET", f"/api/v2/query-runs/{query_run_id}")

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

        r = self.t.request("GET", f"/api/v2/query-runs/{query_run_id}", params=params)

        jd = r.json()
        data = jd.get("data", {})
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")

        return QueryRun.model_validate(attrs)

    def logs(self, query_run_id: str) -> QueryRunLogs:
        """Retrieve the logs for a query run."""
        if not valid_string_id(query_run_id):
            raise InvalidQueryRunIDError()

        r = self.t.request("GET", f"/api/v2/query-runs/{query_run_id}/logs")

        # Handle both JSON and plain text responses
        content_type = r.headers.get("content-type", "").lower()

        if "application/json" in content_type:
            jd = r.json()
            return QueryRunLogs.model_validate(jd.get("data", {}))
        else:
            # Plain text logs
            return QueryRunLogs(
                query_run_id=query_run_id,
                logs=r.text,
                log_level="info",
                timestamp=None,
            )

    def results(self, query_run_id: str) -> QueryRunResults:
        """Retrieve the results for a query run."""
        if not valid_string_id(query_run_id):
            raise InvalidQueryRunIDError()

        r = self.t.request("GET", f"/api/v2/query-runs/{query_run_id}/results")

        jd = r.json()
        data = jd.get("data", {})

        return QueryRunResults(
            query_run_id=query_run_id,
            results=data.get("results", []),
            total_count=data.get("total_count", 0),
            truncated=data.get("truncated", False),
        )

    def cancel(
        self, query_run_id: str, options: QueryRunCancelOptions | None = None
    ) -> QueryRun:
        """Cancel a query run."""
        if not valid_string_id(query_run_id):
            raise InvalidQueryRunIDError()

        attrs = options.model_dump(by_alias=True, exclude_none=True) if options else {}

        body: dict[str, Any] = {
            "data": {
                "attributes": attrs,
                "type": "query-runs",
            }
        }

        r = self.t.request(
            "POST",
            f"/api/v2/query-runs/{query_run_id}/actions/cancel",
            json_body=body,
        )

        jd = r.json()
        data = jd.get("data", {})
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")

        return QueryRun.model_validate(attrs)

    def force_cancel(
        self, query_run_id: str, options: QueryRunForceCancelOptions | None = None
    ) -> QueryRun:
        """Force cancel a query run."""
        if not valid_string_id(query_run_id):
            raise InvalidQueryRunIDError()

        attrs = options.model_dump(by_alias=True, exclude_none=True) if options else {}

        body: dict[str, Any] = {
            "data": {
                "attributes": attrs,
                "type": "query-runs",
            }
        }

        r = self.t.request(
            "POST",
            f"/api/v2/query-runs/{query_run_id}/actions/force-cancel",
            json_body=body,
        )

        jd = r.json()
        data = jd.get("data", {})
        attrs = data.get("attributes", {})
        attrs["id"] = data.get("id")

        return QueryRun.model_validate(attrs)
