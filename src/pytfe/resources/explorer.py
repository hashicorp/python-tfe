# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Explorer API resource.

Maps organization-scoped Explorer endpoints (ad hoc query, CSV export, saved views) to
typed models. Saved-view create/update reshape filter JSON; read paths normalize API
variants before validation.
"""

from __future__ import annotations

import csv
import io
import logging
from collections.abc import Iterator
from typing import Any

from ..errors import (
    InvalidExplorerSavedViewIDError,
    InvalidOrgError,
    NotFound,
    ServerError,
    ValidationError,
)
from ..models.explorer import (
    ExplorerQueryOptions,
    ExplorerRow,
    ExplorerSavedView,
    ExplorerSavedViewCreateOptions,
    ExplorerSavedViewUpdateOptions,
    ExplorerUrlFilter,
)
from ..utils import valid_string_id
from ._base import _Service

_log = logging.getLogger(__name__)


def _explorer_single_resource_data(
    resp: Any,
    *,
    operation: str,
    organization: str,
    view_id: str | None = None,
) -> dict[str, Any]:
    """Parse json:api envelope for a single Explorer saved view; raise ValidationError if unusable."""
    ctx = f"org={organization!r}"
    if view_id is not None:
        ctx += f" view_id={view_id!r}"
    try:
        payload = resp.json()
    except ValueError as exc:
        _log.warning("explorer.%s: invalid JSON response (%s)", operation, ctx)
        raise ValidationError(
            f"Explorer {operation}: response body is not valid JSON ({ctx})"
        ) from exc
    if not isinstance(payload, dict):
        _log.warning("explorer.%s: top-level JSON is not an object (%s)", operation, ctx)
        raise ValidationError(
            f"Explorer {operation}: expected JSON object at top level ({ctx})"
        )
    data = payload.get("data")
    if not isinstance(data, dict):
        _log.warning(
            "explorer.%s: missing or invalid 'data' (type=%s) (%s)",
            operation,
            type(data).__name__,
            ctx,
        )
        raise ValidationError(
            f"Explorer {operation}: expected json:api 'data' object ({ctx})"
        )
    return data


def _require_organization(organization: str) -> None:
    """Reject blank organization identifiers before building paths."""
    if not valid_string_id(organization):
        raise InvalidOrgError()


def _require_organization_and_view(organization: str, view_id: str) -> None:
    """Validate org and saved-view id for routes under .../explorer/views/{view_id}."""
    _require_organization(organization)
    if not valid_string_id(view_id):
        raise InvalidExplorerSavedViewIDError()


def _write_attributes_with_query_shape(
    options: ExplorerSavedViewCreateOptions | ExplorerSavedViewUpdateOptions,
) -> dict[str, Any]:
    """Serialize create/update options; map saved-query filters to the map shape POST/PATCH expect."""
    attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
    raw_query = attrs.get("query")
    if isinstance(raw_query, dict):
        attrs["query"] = _saved_query_to_api_shape(raw_query)
    return attrs


def _query_params(options: ExplorerQueryOptions) -> dict[str, Any]:
    # mode="json" keeps ExplorerViewType as strings; filters are expanded separately (Explorer URL grammar).
    params = options.model_dump(
        by_alias=True,
        exclude_none=True,
        exclude={"filters"},
        mode="json",
    )
    if options.filters:
        for flt in options.filters:
            params[
                f"filter[{flt.index}][{flt.field}][{flt.operator}][{flt.value_index}]"
            ] = flt.value
    return params


def _parse_row(item: dict[str, Any]) -> ExplorerRow:
    return ExplorerRow.model_validate(item)


def _saved_query_to_api_shape(raw_query: dict[str, Any]) -> dict[str, Any]:
    """Map {field, operator, value} filter rows to nested {field: {operator: [...]}} JSON."""
    query = dict(raw_query)
    raw_filter = query.get("filter")
    if isinstance(raw_filter, list):
        mapped_filters: list[dict[str, Any]] = []
        for entry in raw_filter:
            if not isinstance(entry, dict):
                continue
            # Already API-compatible map style.
            if "field" not in entry or "operator" not in entry:
                mapped_filters.append(entry)
                continue
            field = str(entry.get("field", "")).replace("-", "_")
            operator = str(entry.get("operator", ""))
            values = entry.get("value", [])
            if not isinstance(values, list):
                values = [values]
            mapped_filters.append({field: {operator: [str(v) for v in values]}})
        query["filter"] = mapped_filters
    return query


def _normalize_saved_query(
    raw_query: dict[str, Any], raw_query_type: str | None
) -> dict[str, Any]:
    """Coerce saved-view query JSON into the flat filter + list fields shape our models use."""
    query = dict(raw_query)

    if "type" not in query and raw_query_type:
        query["type"] = raw_query_type

    raw_filter = query.get("filter")
    if isinstance(raw_filter, list):
        normalized_filters: list[dict[str, Any]] = []
        for entry in raw_filter:
            # Variant A (documented): {"field": "...", "operator": "...", "value": [...]}
            if isinstance(entry, dict) and "field" in entry and "operator" in entry:
                value = entry.get("value")
                if value is None:
                    value = []
                if not isinstance(value, list):
                    value = [str(value)]
                normalized_filters.append(
                    {
                        "field": str(entry["field"]).replace("-", "_"),
                        "operator": str(entry["operator"]),
                        "value": [str(v) for v in value],
                    }
                )
                continue

            # Variant B (observed): {"workspace-name": {"contains": ["foo"]}}
            if isinstance(entry, dict):
                for field_name, operators in entry.items():
                    if not isinstance(operators, dict):
                        continue
                    for operator, values in operators.items():
                        vals = values if isinstance(values, list) else [values]
                        normalized_filters.append(
                            {
                                "field": str(field_name).replace("-", "_"),
                                "operator": str(operator),
                                "value": [str(v) for v in vals],
                            }
                        )
        query["filter"] = normalized_filters

    raw_fields = query.get("fields")
    # Some responses return fields as {"workspaces": [...]}.
    if isinstance(raw_fields, dict):
        list_values: list[str] = []
        for value in raw_fields.values():
            if isinstance(value, list):
                list_values.extend(str(v) for v in value)
        query["fields"] = list_values

    return query


def _parse_saved_view(item: dict[str, Any]) -> ExplorerSavedView:
    # json:api envelope: attributes carry name, timestamps, nested query and query-type.
    attrs = item.get("attributes", {})
    query_type = attrs.get("query-type")
    query = attrs.get("query", {})
    if not isinstance(query, dict):
        query = {}

    return ExplorerSavedView.model_validate(
        {
            "id": item.get("id"),
            "name": attrs.get("name"),
            "created-at": attrs.get("created-at"),
            "query": _normalize_saved_query(query, query_type),
            "query-type": query_type,
        }
    )


def _deleted_saved_view_fallback(view_id: str) -> ExplorerSavedView:
    """Build a minimal saved view when delete responses have no body."""
    return ExplorerSavedView.model_validate(
        {
            "id": view_id,
            "name": "",
            "query-type": "workspaces",
            "query": {"type": "workspaces"},
        }
    )


def _query_options_from_saved_view(
    saved_view: ExplorerSavedView,
) -> ExplorerQueryOptions:
    """Replay a stored saved query as GET /explorer query params (used by CSV fallback)."""
    query = saved_view.query
    filters: list[ExplorerUrlFilter] = []
    if query.filter:
        for idx, flt in enumerate(query.filter):
            for value_index, value in enumerate(flt.value or []):
                filters.append(
                    ExplorerUrlFilter(
                        index=idx,
                        field=flt.field,
                        operator=flt.operator,
                        value=str(value),
                        value_index=value_index,
                    )
                )
    return ExplorerQueryOptions.model_validate(
        {
            "type": saved_view.query_type,
            "sort": ",".join(query.sort) if query.sort else None,
            "fields": ",".join(query.fields) if query.fields else None,
            "filters": filters or None,
        }
    )


def _rows_to_csv(rows: list[ExplorerRow]) -> str:
    """Union of row attribute keys as header; last-resort CSV when /views/.../csv is unavailable."""
    if not rows:
        return ""
    keys: set[str] = set()
    for row in rows:
        keys.update(row.attributes.keys())
    fieldnames = sorted(keys)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.attributes.get(k, "") for k in fieldnames})
    return buf.getvalue()


class Explorer(_Service):
    """Organization Explorer: ad hoc queries, CSV export, and saved view CRUD."""

    def query(
        self, organization: str, options: ExplorerQueryOptions
    ) -> Iterator[ExplorerRow]:
        _require_organization(organization)
        _log.debug(
            "explorer.query org=%r view_type=%s",
            organization,
            options.view_type.value,
        )
        # GET .../explorer — paginated JSON rows for the given view and filters.
        path = f"/api/v2/organizations/{organization}/explorer"
        for item in self._list(path, params=_query_params(options)):
            yield _parse_row(item)

    def export_csv(self, organization: str, options: ExplorerQueryOptions) -> str:
        _require_organization(organization)
        _log.debug(
            "explorer.export_csv org=%r view_type=%s",
            organization,
            options.view_type.value,
        )
        # Same query string as query(); response is a single unpaged CSV document.
        path = f"/api/v2/organizations/{organization}/explorer/export/csv"
        resp = self.t.request("GET", path, params=_query_params(options))
        return resp.text

    def list_saved_views(self, organization: str) -> Iterator[ExplorerSavedView]:
        _require_organization(organization)
        _log.debug("explorer.list_saved_views org=%r", organization)
        # GET collection of explorer-saved-queries for the org.
        path = f"/api/v2/organizations/{organization}/explorer/views"
        for item in self._list(path):
            yield _parse_saved_view(item)

    def create_saved_view(
        self, organization: str, options: ExplorerSavedViewCreateOptions
    ) -> ExplorerSavedView:
        _require_organization(organization)
        # POST json:api explorer-saved-queries; filters rewritten for server expectations.
        attrs = _write_attributes_with_query_shape(options)
        body = {
            "data": {
                "type": "explorer-saved-queries",
                "attributes": attrs,
            }
        }
        path = f"/api/v2/organizations/{organization}/explorer/views"
        resp = self.t.request("POST", path, json_body=body)
        data = _explorer_single_resource_data(
            resp, operation="create_saved_view", organization=organization
        )
        view = _parse_saved_view(data)
        _log.info("explorer.create_saved_view org=%r id=%r", organization, view.id)
        return view

    def read_saved_view(self, organization: str, view_id: str) -> ExplorerSavedView:
        _require_organization_and_view(organization, view_id)
        _log.debug(
            "explorer.read_saved_view org=%r view_id=%r",
            organization,
            view_id,
        )
        # Returns stored definition only; does not execute the query (see saved_view_results).
        path = f"/api/v2/organizations/{organization}/explorer/views/{view_id}"
        resp = self.t.request("GET", path)
        data = _explorer_single_resource_data(
            resp,
            operation="read_saved_view",
            organization=organization,
            view_id=view_id,
        )
        return _parse_saved_view(data)

    def update_saved_view(
        self,
        organization: str,
        view_id: str,
        options: ExplorerSavedViewUpdateOptions,
    ) -> ExplorerSavedView:
        _require_organization_and_view(organization, view_id)
        attrs = _write_attributes_with_query_shape(options)
        # PATCH includes resource id in the envelope per json:api update conventions.
        body = {
            "data": {
                "type": "explorer-saved-queries",
                "id": view_id,
                "attributes": attrs,
            }
        }
        path = f"/api/v2/organizations/{organization}/explorer/views/{view_id}"
        resp = self.t.request("PATCH", path, json_body=body)
        data = _explorer_single_resource_data(
            resp,
            operation="update_saved_view",
            organization=organization,
            view_id=view_id,
        )
        view = _parse_saved_view(data)
        _log.info("explorer.update_saved_view org=%r id=%r", organization, view.id)
        return view

    def delete_saved_view(self, organization: str, view_id: str) -> ExplorerSavedView:
        _require_organization_and_view(organization, view_id)
        path = f"/api/v2/organizations/{organization}/explorer/views/{view_id}"
        resp = self.t.request("DELETE", path)
        # DELETE often returns an empty body; callers still receive a minimal ExplorerSavedView.
        raw_text = (resp.text or "").strip()
        if not raw_text:
            _log.debug(
                "explorer.delete_saved_view: empty body, returning stub org=%r id=%r",
                organization,
                view_id,
            )
            return _deleted_saved_view_fallback(view_id)

        try:
            payload = resp.json()
        except ValueError:
            _log.debug(
                "explorer.delete_saved_view: non-JSON body, returning stub org=%r id=%r",
                organization,
                view_id,
            )
            return _deleted_saved_view_fallback(view_id)

        if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
            return _parse_saved_view(payload["data"])
        _log.debug(
            "explorer.delete_saved_view: no data object, returning stub org=%r id=%r",
            organization,
            view_id,
        )
        return _deleted_saved_view_fallback(view_id)

    def saved_view_results(
        self, organization: str, view_id: str
    ) -> Iterator[ExplorerRow]:
        _require_organization_and_view(organization, view_id)
        _log.debug(
            "explorer.saved_view_results org=%r view_id=%r",
            organization,
            view_id,
        )
        # Re-runs the saved query; rows match ad hoc query() shape (current data only).
        path = f"/api/v2/organizations/{organization}/explorer/views/{view_id}/results"
        for item in self._list(path):
            yield _parse_row(item)

    def saved_view_results_csv(self, organization: str, view_id: str) -> str:
        _require_organization_and_view(organization, view_id)
        _log.debug(
            "explorer.saved_view_results_csv org=%r view_id=%r",
            organization,
            view_id,
        )
        path = f"/api/v2/organizations/{organization}/explorer/views/{view_id}/csv"
        try:
            resp = self.t.request("GET", path)
            return resp.text
        except (NotFound, ServerError) as exc:
            _log.info(
                "explorer.saved_view_results_csv: primary CSV route unavailable (%s); "
                "trying export_csv replay org=%r view_id=%r",
                exc.__class__.__name__,
                organization,
                view_id,
            )

        # Fall back: replay saved definition via export_csv, then row materialization if needed.
        try:
            saved_view = self.read_saved_view(organization, view_id)
            options = _query_options_from_saved_view(saved_view)
            csv_text = self.export_csv(organization, options)
            _log.info(
                "explorer.saved_view_results_csv: used export_csv fallback org=%r view_id=%r",
                organization,
                view_id,
            )
            return csv_text
        except (NotFound, ServerError) as exc:
            _log.warning(
                "explorer.saved_view_results_csv: export_csv fallback failed (%s); "
                "building CSV from row stream org=%r view_id=%r",
                exc.__class__.__name__,
                organization,
                view_id,
            )
            rows = list(self.saved_view_results(organization, view_id))
            return _rows_to_csv(rows)
