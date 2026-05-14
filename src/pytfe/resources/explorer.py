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
    ExplorerViewType,
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
        _log.warning(
            "explorer.%s: top-level JSON is not an object (%s)", operation, ctx
        )
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


def _normalize_filter_field_name(raw_field: Any) -> str:
    """Normalize filter field names to SDK model style."""
    return str(raw_field).replace("-", "_")


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
            field = _normalize_filter_field_name(entry.get("field", ""))
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
                        "field": _normalize_filter_field_name(entry["field"]),
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
                                "field": _normalize_filter_field_name(field_name),
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


# Column order matches HashiCorp Explorer API docs (view-type field tables and export/csv
# workspaces sample): https://developer.hashicorp.com/terraform/cloud-docs/api-docs/explorer
_EXPLORER_CSV_COLUMNS: dict[ExplorerViewType, tuple[str, ...]] = {
    ExplorerViewType.WORKSPACES: (
        "all_checks_succeeded",
        "current_rum_count",
        "checks_errored",
        "checks_failed",
        "checks_passed",
        "checks_unknown",
        "current_run_applied_at",
        "current_run_external_id",
        "current_run_status",
        "drifted",
        "external_id",
        "module_count",
        "modules",
        "organization_name",
        "project_external_id",
        "project_name",
        "provider_count",
        "providers",
        "resources_drifted",
        "resources_undrifted",
        "state_version_terraform_version",
        "vcs_repo_identifier",
        "workspace_created_at",
        "workspace_name",
        "workspace_terraform_version",
        "workspace_updated_at",
    ),
    ExplorerViewType.TF_VERSIONS: ("version", "workspace_count", "workspaces"),
    ExplorerViewType.PROVIDERS: (
        "name",
        "source",
        "version",
        "workspace_count",
        "workspaces",
    ),
    ExplorerViewType.MODULES: (
        "name",
        "source",
        "version",
        "workspace_count",
        "workspaces",
    ),
}

_ROW_TYPE_TO_VIEW: dict[str, ExplorerViewType] = {
    "visibility-workspace": ExplorerViewType.WORKSPACES,
}


def _infer_view_type_from_csv_header(header: list[str]) -> ExplorerViewType | None:
    """Pick Explorer view type from CSV header names (no extra API call)."""
    h = frozenset(header)
    candidates: list[tuple[int, int, str, ExplorerViewType]] = []
    for vt, cols in _EXPLORER_CSV_COLUMNS.items():
        colset = frozenset(cols)
        overlap = len(h & colset)
        if overlap == 0:
            continue
        # Prefer more matching columns; tie-break to a narrower schema (e.g. tf_versions).
        candidates.append((overlap, -len(colset), vt.value, vt))
    if not candidates:
        return None
    _, _, _, vt = max(candidates)
    return vt


def _explorer_attribute_value(attrs: dict[str, Any], logical_snake: str) -> Any:
    """Resolve API attribute keys (snake_case or kebab-case) for one logical Explorer column."""
    hyphen = logical_snake.replace("_", "-")
    if logical_snake in attrs:
        return attrs[logical_snake]
    if hyphen in attrs:
        return attrs[hyphen]
    return ""


def _csv_fieldnames_for_explorer_rows(
    rows: list[ExplorerRow],
    view_type: ExplorerViewType | None,
) -> tuple[list[str], frozenset[str]]:
    """Doc-ordered columns first; trailing columns for attributes not in the doc schema."""
    all_raw: set[str] = set()
    for row in rows:
        all_raw.update(row.attributes.keys())

    order = _EXPLORER_CSV_COLUMNS.get(view_type) if view_type is not None else None
    if not order:
        seen: set[str] = set()
        visit: list[str] = []
        for row in rows:
            for k in row.attributes:
                if k not in seen:
                    seen.add(k)
                    visit.append(k)
        return visit, frozenset()

    canonical_set = frozenset(order)
    matched_raw: set[str] = set()
    for raw in all_raw:
        for col in order:
            if raw == col or raw == col.replace("_", "-"):
                matched_raw.add(raw)
                break

    extras: list[str] = []
    seen_extras: set[str] = set()
    for row in rows:
        for raw in row.attributes:
            if raw not in canonical_set and raw not in seen_extras:
                seen_extras.add(raw)
                extras.append(raw)
    return list(order) + extras, canonical_set


def _infer_view_type_from_rows(rows: list[ExplorerRow]) -> ExplorerViewType | None:
    if not rows:
        return None
    return _ROW_TYPE_TO_VIEW.get(rows[0].row_type)


def _normalize_explorer_csv_column_order(
    csv_text: str, view_type: ExplorerViewType | None
) -> str:
    """Reorder CSV header/data columns to match Explorer API doc order (GET CSV varies)."""
    if not csv_text.strip() or view_type is None:
        return csv_text
    order = _EXPLORER_CSV_COLUMNS.get(view_type)
    if not order:
        return csv_text
    try:
        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)
    except csv.Error:
        return csv_text
    if not rows or not rows[0]:
        return csv_text
    header = rows[0]
    idx = {name: i for i, name in enumerate(header)}
    order_set = frozenset(order)
    canonical = [c for c in order if c in idx]
    extras = [h for h in header if h not in order_set]
    new_header = canonical + extras
    if new_header == header:
        return csv_text
    perm = [idx[h] for h in new_header]
    ncols = len(header)
    out_rows: list[list[str]] = [new_header]
    for row in rows[1:]:
        padded = list(row) + [""] * max(0, ncols - len(row))
        padded = padded[:ncols]
        out_rows.append([padded[i] for i in perm])
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerows(out_rows)
    return buf.getvalue()


def _rows_to_csv(
    rows: list[ExplorerRow],
    *,
    view_type: ExplorerViewType | None = None,
) -> str:
    """Build CSV from result rows; column order follows Explorer API docs when view_type is known."""
    if not rows:
        return ""
    vt = view_type if view_type is not None else _infer_view_type_from_rows(rows)
    fieldnames, canonical_set = _csv_fieldnames_for_explorer_rows(rows, vt)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        attrs = row.attributes
        row_out: dict[str, Any] = {}
        for name in fieldnames:
            if name in canonical_set:
                row_out[name] = _explorer_attribute_value(attrs, name)
            else:
                row_out[name] = attrs.get(name, "")
        writer.writerow(row_out)
    return buf.getvalue()


class Explorer(_Service):
    """Organization Explorer: ad hoc queries, CSV export, and saved view CRUD."""

    def query(
        self, organization: str, options: ExplorerQueryOptions
    ) -> Iterator[ExplorerRow]:
        """Execute an Explorer query and iterate result rows across all pages.

        Args:
            organization: Organization slug that owns the Explorer data.
            options: Query options including view type, filters, sort, and paging.

        Yields:
            ExplorerRow items returned by the Explorer endpoint.
        """
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
        """Run an Explorer query and return CSV text from the export endpoint.

        Args:
            organization: Organization slug that owns the Explorer data.
            options: Query options including view type, filters, sort, and paging.

        Returns:
            Raw CSV text returned by the server.
        """
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
        """Iterate all saved Explorer views in an organization.

        Args:
            organization: Organization slug that owns the saved views.

        Yields:
            ExplorerSavedView resources from the list endpoint.
        """
        _require_organization(organization)
        _log.debug("explorer.list_saved_views org=%r", organization)
        # GET collection of explorer-saved-queries for the org.
        path = f"/api/v2/organizations/{organization}/explorer/views"
        for item in self._list(path):
            yield _parse_saved_view(item)

    def create_saved_view(
        self, organization: str, options: ExplorerSavedViewCreateOptions
    ) -> ExplorerSavedView:
        """Create a saved Explorer view.

        Args:
            organization: Organization slug that owns the saved view.
            options: Saved-view name and query definition to persist.

        Returns:
            The created ExplorerSavedView as returned by the API.
        """
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
        """Read one saved Explorer view by id.

        Args:
            organization: Organization slug that owns the saved view.
            view_id: Saved-view id (for example, ``sq-...``).

        Returns:
            The saved view definition and query metadata.
        """
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
        """Replace attributes of an existing saved Explorer view.

        Args:
            organization: Organization slug that owns the saved view.
            view_id: Saved-view id (for example, ``sq-...``).
            options: Updated name and full replacement query definition.

        Returns:
            The updated ExplorerSavedView as returned by the API.
        """
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

    def delete_saved_view(self, organization: str, view_id: str) -> None:
        """Delete a saved Explorer view.

        Args:
            organization: Organization slug that owns the saved view.
            view_id: Saved-view id (for example, ``sq-...``).

        Returns:
            None.
        """
        _require_organization_and_view(organization, view_id)
        path = f"/api/v2/organizations/{organization}/explorer/views/{view_id}"
        self.t.request("DELETE", path)

    def saved_view_results(
        self, organization: str, view_id: str
    ) -> Iterator[ExplorerRow]:
        """Execute a saved view and iterate result rows across all pages.

        Args:
            organization: Organization slug that owns the saved view.
            view_id: Saved-view id (for example, ``sq-...``).

        Yields:
            ExplorerRow items produced by the saved query.
        """
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
        """Return CSV for a saved view with resilient fallback behavior.

        Tries the dedicated saved-view CSV endpoint first, then falls back to replaying
        the saved view through ``export_csv`` and finally to materializing rows from the
        paginated results endpoint.

        Args:
            organization: Organization slug that owns the saved view.
            view_id: Saved-view id (for example, ``sq-...``).

        Returns:
            CSV text for the saved view results.
        """
        _require_organization_and_view(organization, view_id)
        _log.debug(
            "explorer.saved_view_results_csv org=%r view_id=%r",
            organization,
            view_id,
        )
        path = f"/api/v2/organizations/{organization}/explorer/views/{view_id}/csv"
        try:
            resp = self.t.request("GET", path)
            csv_text = resp.text
            try:
                parsed = list(csv.reader(io.StringIO(csv_text)))
            except csv.Error:
                return csv_text
            if parsed and parsed[0]:
                vt = _infer_view_type_from_csv_header(parsed[0])
                if vt is not None:
                    csv_text = _normalize_explorer_csv_column_order(csv_text, vt)
            return csv_text
        except (NotFound, ServerError) as exc:
            _log.info(
                "explorer.saved_view_results_csv: primary CSV route unavailable (%s); "
                "trying export_csv replay org=%r view_id=%r",
                exc.__class__.__name__,
                organization,
                view_id,
            )

        # Fall back: replay saved definition via export_csv, then row materialization if needed.
        saved_for_csv: ExplorerSavedView | None = None
        try:
            saved_for_csv = self.read_saved_view(organization, view_id)
            options = _query_options_from_saved_view(saved_for_csv)
            csv_text = self.export_csv(organization, options)
            csv_text = _normalize_explorer_csv_column_order(
                csv_text, saved_for_csv.query_type
            )
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
            vt = saved_for_csv.query_type if saved_for_csv is not None else None
            return _rows_to_csv(rows, view_type=vt)
