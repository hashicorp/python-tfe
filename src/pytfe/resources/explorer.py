# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Explorer API resource.

Maps organization-scoped Explorer endpoints (ad-hoc query, CSV export, saved
views) to typed models. Saved-view create/update reshape filter JSON to the
nested ``{field: {operator: [values]}}`` form the server expects.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..errors import (
    InvalidExplorerSavedViewIDError,
    InvalidOrgError,
)
from ..models.explorer import (
    ExplorerQueryOptions,
    ExplorerRow,
    ExplorerSavedView,
    ExplorerSavedViewCreateOptions,
    ExplorerSavedViewUpdateOptions,
)
from ..utils import valid_string_id
from ._base import _Service


def _query_params(options: ExplorerQueryOptions) -> dict[str, Any]:
    """Serialise ExplorerQueryOptions to query-string params, expanding filters."""
    # mode="json" keeps ExplorerViewType as strings; filters are expanded
    # separately into the Explorer URL grammar.
    params = options.model_dump(
        by_alias=True,
        exclude_none=True,
        exclude={"filters"},
        mode="json",
    )
    if options.filters:
        for flt in options.filters:
            key = f"filter[{flt.index}][{flt.field}][{flt.operator}][{flt.value_index}]"
            params[key] = flt.value
    return params


def _normalize_attribute_keys(attrs: dict[str, Any]) -> dict[str, Any]:
    """Normalise JSON:API hyphen attribute keys to Python snake_case."""
    return {k.replace("-", "_"): v for k, v in attrs.items()}


def _parse_row(item: dict[str, Any]) -> ExplorerRow:
    return ExplorerRow.model_validate(
        {
            "id": item.get("id", ""),
            "type": item.get("type", ""),
            "attributes": _normalize_attribute_keys(item.get("attributes") or {}),
        }
    )


def _saved_query_to_api_shape(raw_query: dict[str, Any]) -> dict[str, Any]:
    """Map the model's flat filter rows and field list into the shapes the
    API expects on create/update:

      * ``filter`` rows:  ``{field, operator, value}`` → ``{field: {operator: [values]}}``
      * ``fields``:        ``[col, ...]`` → ``{view_type: [col, ...]}``
    """
    query = dict(raw_query)

    raw_filter = query.get("filter")
    if isinstance(raw_filter, list):
        mapped: list[dict[str, Any]] = []
        for entry in raw_filter:
            if not isinstance(entry, dict):
                continue
            # Already in API map shape — pass through.
            if "field" not in entry or "operator" not in entry:
                mapped.append(entry)
                continue
            field = str(entry.get("field", "")).replace("-", "_")
            operator = str(entry.get("operator", ""))
            values = entry.get("value", [])
            if not isinstance(values, list):
                values = [values]
            mapped.append({field: {operator: [str(v) for v in values]}})
        query["filter"] = mapped

    # The API stores `fields` as `{view_type: [columns]}`. Wrap a flat list.
    raw_fields = query.get("fields")
    view_type = query.get("type")
    if isinstance(raw_fields, list) and isinstance(view_type, str):
        query["fields"] = {view_type: list(raw_fields)}

    return query


def _write_attributes(
    options: ExplorerSavedViewCreateOptions | ExplorerSavedViewUpdateOptions,
) -> dict[str, Any]:
    """Serialise create/update options with filters reshaped for the API."""
    attrs = options.model_dump(by_alias=True, exclude_none=True, mode="json")
    raw_query = attrs.get("query")
    if isinstance(raw_query, dict):
        attrs["query"] = _saved_query_to_api_shape(raw_query)
    return attrs


def _saved_query_from_api(raw_query: dict[str, Any]) -> dict[str, Any]:
    """Coerce a saved query's API response into the flat model shape.

    The Explorer API can return filter rows in either of two shapes:

      * Documented flat shape:  ``{"field": ..., "operator": ..., "value": [...]}``
      * Operator-map shape:     ``{field_name: {operator: [values]}}``

    We accept both. Dropping either shape silently loses filter data and
    risks consumers overwriting saved-view criteria on an update round-trip.

    ``fields`` arrives as ``{view_type: [...]}`` and is flattened to a list.
    """
    query = dict(raw_query)

    raw_filter = query.get("filter")
    if isinstance(raw_filter, list):
        flat: list[dict[str, Any]] = []
        for entry in raw_filter:
            if not isinstance(entry, dict):
                continue
            # Variant A: flat shape with explicit field/operator/value keys.
            if "field" in entry and "operator" in entry:
                value = entry.get("value", [])
                if value is None:
                    value = []
                if not isinstance(value, list):
                    value = [value]
                flat.append(
                    {
                        "field": str(entry["field"]).replace("-", "_"),
                        "operator": str(entry["operator"]),
                        "value": [str(v) for v in value],
                    }
                )
                continue
            # Variant B: operator-map shape — what the live API actually returns.
            for field_name, operators in entry.items():
                if not isinstance(operators, dict):
                    continue
                for operator, values in operators.items():
                    vals = values if isinstance(values, list) else [values]
                    flat.append(
                        {
                            "field": str(field_name).replace("-", "_"),
                            "operator": str(operator),
                            "value": [str(v) for v in vals],
                        }
                    )
        query["filter"] = flat

    # `fields` arrives as {view_type: [...]}; flatten to a single list.
    raw_fields = query.get("fields")
    if isinstance(raw_fields, dict):
        flat_fields: list[str] = []
        for value in raw_fields.values():
            if isinstance(value, list):
                flat_fields.extend(str(v) for v in value)
        query["fields"] = flat_fields

    return query


def _parse_saved_view(item: dict[str, Any]) -> ExplorerSavedView:
    attrs = item.get("attributes") or {}
    query = attrs.get("query") or {}
    if not isinstance(query, dict):
        query = {}
    return ExplorerSavedView.model_validate(
        {
            "id": item.get("id"),
            "name": attrs.get("name"),
            "created-at": attrs.get("created-at"),
            "query": _saved_query_from_api(query),
            "query-type": attrs.get("query-type"),
        }
    )


class Explorer(_Service):
    """Organization Explorer: ad-hoc queries, CSV export, and saved view CRUD."""

    def query(
        self, organization: str, options: ExplorerQueryOptions
    ) -> Iterator[ExplorerRow]:
        """Execute an Explorer query and iterate result rows across all pages."""
        if not valid_string_id(organization):
            raise InvalidOrgError()
        path = f"/api/v2/organizations/{organization}/explorer"
        for item in self._list(path, params=_query_params(options)):
            yield _parse_row(item)

    def export_csv(self, organization: str, options: ExplorerQueryOptions) -> str:
        """Run an Explorer query and return CSV text from the export endpoint."""
        if not valid_string_id(organization):
            raise InvalidOrgError()
        path = f"/api/v2/organizations/{organization}/explorer/export/csv"
        resp = self.t.request("GET", path, params=_query_params(options))
        return resp.text

    def list_saved_views(self, organization: str) -> Iterator[ExplorerSavedView]:
        """Iterate all saved Explorer views in an organization."""
        if not valid_string_id(organization):
            raise InvalidOrgError()
        path = f"/api/v2/organizations/{organization}/explorer/views"
        for item in self._list(path):
            yield _parse_saved_view(item)

    def create_saved_view(
        self, organization: str, options: ExplorerSavedViewCreateOptions
    ) -> ExplorerSavedView:
        """Create a saved Explorer view."""
        if not valid_string_id(organization):
            raise InvalidOrgError()
        body = {
            "data": {
                "type": "explorer-saved-queries",
                "attributes": _write_attributes(options),
            }
        }
        path = f"/api/v2/organizations/{organization}/explorer/views"
        resp = self.t.request("POST", path, json_body=body)
        data = (resp.json() or {}).get("data") or {}
        return _parse_saved_view(data)

    def read_saved_view(self, organization: str, view_id: str) -> ExplorerSavedView:
        """Read one saved Explorer view by id."""
        if not valid_string_id(organization):
            raise InvalidOrgError()
        if not valid_string_id(view_id):
            raise InvalidExplorerSavedViewIDError()
        path = f"/api/v2/organizations/{organization}/explorer/views/{view_id}"
        resp = self.t.request("GET", path)
        data = (resp.json() or {}).get("data") or {}
        return _parse_saved_view(data)

    def update_saved_view(
        self,
        organization: str,
        view_id: str,
        options: ExplorerSavedViewUpdateOptions,
    ) -> ExplorerSavedView:
        """Replace attributes of an existing saved Explorer view."""
        if not valid_string_id(organization):
            raise InvalidOrgError()
        if not valid_string_id(view_id):
            raise InvalidExplorerSavedViewIDError()
        body = {
            "data": {
                "type": "explorer-saved-queries",
                "id": view_id,
                "attributes": _write_attributes(options),
            }
        }
        path = f"/api/v2/organizations/{organization}/explorer/views/{view_id}"
        resp = self.t.request("PATCH", path, json_body=body)
        data = (resp.json() or {}).get("data") or {}
        return _parse_saved_view(data)

    def delete_saved_view(self, organization: str, view_id: str) -> None:
        """Delete a saved Explorer view."""
        if not valid_string_id(organization):
            raise InvalidOrgError()
        if not valid_string_id(view_id):
            raise InvalidExplorerSavedViewIDError()
        path = f"/api/v2/organizations/{organization}/explorer/views/{view_id}"
        self.t.request("DELETE", path)

    def saved_view_results(
        self, organization: str, view_id: str
    ) -> Iterator[ExplorerRow]:
        """Execute a saved view and iterate result rows across all pages."""
        if not valid_string_id(organization):
            raise InvalidOrgError()
        if not valid_string_id(view_id):
            raise InvalidExplorerSavedViewIDError()
        path = f"/api/v2/organizations/{organization}/explorer/views/{view_id}/results"
        for item in self._list(path):
            yield _parse_row(item)

    def saved_view_results_csv(self, organization: str, view_id: str) -> str:
        """Return CSV text for a saved view from the dedicated export endpoint."""
        if not valid_string_id(organization):
            raise InvalidOrgError()
        if not valid_string_id(view_id):
            raise InvalidExplorerSavedViewIDError()
        path = (
            f"/api/v2/organizations/{organization}/explorer/views/{view_id}/export/csv"
        )
        resp = self.t.request("GET", path)
        return resp.text
