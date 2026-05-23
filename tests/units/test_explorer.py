# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for Explorer API resource."""

import csv
from unittest.mock import Mock, call

import pytest

from pytfe.errors import (
    InvalidExplorerSavedViewIDError,
    InvalidOrgError,
    NotFound,
    ServerError,
    ValidationError,
)
from pytfe.models import (
    ExplorerQueryOptions,
    ExplorerRow,
    ExplorerSavedQuery,
    ExplorerSavedQueryFilter,
    ExplorerSavedViewCreateOptions,
    ExplorerSavedViewUpdateOptions,
    ExplorerUrlFilter,
    ExplorerViewType,
)
from pytfe.resources.explorer import (
    Explorer,
    _normalize_explorer_csv_column_order,
    _rows_to_csv,
)

ORG = "acme"
VIEW_ID = "sq-1"
EXPLORER_PATH = f"/api/v2/organizations/{ORG}/explorer"
VIEWS_PATH = f"{EXPLORER_PATH}/views"


@pytest.fixture
def mock_transport():
    return Mock()


@pytest.fixture
def explorer_service(mock_transport):
    return Explorer(mock_transport)


def test_normalize_explorer_csv_column_order_workspaces():
    raw = "workspace_name,all_checks_succeeded\ndemo,true\n"
    out = _normalize_explorer_csv_column_order(raw, ExplorerViewType.WORKSPACES)
    assert out.splitlines()[0].startswith("all_checks_succeeded,workspace_name")


def test_rows_to_csv_workspace_column_order_matches_doc():
    """Fallback CSV header matches Explorer export/csv workspaces sample column order."""
    rows = [
        ExplorerRow.model_validate(
            {
                "id": "ws-1",
                "type": "visibility-workspace",
                "attributes": {"workspace-name": "demo-workspace"},
            }
        )
    ]
    csv_text = _rows_to_csv(rows, view_type=ExplorerViewType.WORKSPACES)
    header = csv_text.strip().splitlines()[0]
    assert header.startswith(
        "all_checks_succeeded,current_rum_count,checks_errored,checks_failed,"
        "checks_passed,checks_unknown,current_run_applied_at,current_run_external_id,"
        "current_run_status,drifted,external_id,module_count,modules,organization_name,"
        "project_external_id,project_name,provider_count,providers,resources_drifted,"
        "resources_undrifted,state_version_terraform_version,vcs_repo_identifier,"
        "workspace_created_at,workspace_name,workspace_terraform_version,workspace_updated_at"
    )
    assert "demo-workspace" in csv_text


def _row_payload(row_id: str) -> dict:
    return {
        "id": row_id,
        "type": "visibility-workspace",
        "attributes": {"workspace-name": "demo-workspace"},
    }


def _saved_view_payload(view_id: str) -> dict:
    return {
        "id": view_id,
        "type": "explorer-saved-queries",
        "attributes": {
            "name": "my-view",
            "created-at": "2024-10-11T16:18:51.442Z",
            "query-type": "workspaces",
            "query": {
                "type": "workspaces",
                "filter": [
                    {
                        "field": "workspace_name",
                        "operator": "contains",
                        "value": ["child"],
                    }
                ],
            },
        },
    }


def _saved_view_payload_live_variant(view_id: str) -> dict:
    return {
        "id": view_id,
        "type": "explorer-saved-queries",
        "attributes": {
            "name": "my-view",
            "created-at": "2024-10-11T16:18:51.442Z",
            "query-type": "workspaces",
            "query": {
                "filter": [{"workspace-name": {"contains": ["r2l7cj4v"]}}],
                "fields": {"workspaces": []},
            },
        },
    }


def _assert_single_request_call(
    mock_transport, method: str, path: str, **kwargs
) -> None:
    mock_transport.request.assert_called_once_with(method, path, **kwargs)


def _query_request_params(page_number: int) -> dict:
    return {
        "type": "workspaces",
        "sort": "-workspace_name",
        "fields": "workspace_name,organization_name",
        "page[size]": 1,
        "filter[0][workspace_name][contains][0]": "test",
        "page[number]": page_number,
    }


class TestExplorerQuery:
    def test_query_with_filter_and_pagination(self, explorer_service, mock_transport):
        first = Mock()
        first.json.return_value = {"data": [_row_payload("ws-1")]}
        second = Mock()
        second.json.return_value = {"data": [_row_payload("ws-2")]}
        third = Mock()
        third.json.return_value = {"data": [_row_payload("ws-3")]}
        fourth = Mock()
        fourth.json.return_value = {"data": []}
        mock_transport.request.side_effect = [first, second, third, fourth]

        options = ExplorerQueryOptions(
            view_type=ExplorerViewType.WORKSPACES,
            sort="-workspace_name",
            fields="workspace_name,organization_name",
            page_size=1,
            filters=[
                ExplorerUrlFilter(
                    index=0,
                    field="workspace_name",
                    operator="contains",
                    value="test",
                )
            ],
        )

        rows = list(explorer_service.query(ORG, options))
        assert len(rows) == 3
        assert [row.id for row in rows] == ["ws-1", "ws-2", "ws-3"]
        assert all(row.row_type == "visibility-workspace" for row in rows)

        expected_calls = [
            call("GET", EXPLORER_PATH, params=_query_request_params(page_number=1)),
            call("GET", EXPLORER_PATH, params=_query_request_params(page_number=2)),
            call("GET", EXPLORER_PATH, params=_query_request_params(page_number=3)),
            call("GET", EXPLORER_PATH, params=_query_request_params(page_number=4)),
        ]
        mock_transport.request.assert_has_calls(expected_calls)
        assert mock_transport.request.call_count == 4

    def test_query_uses_pagination_meta_when_server_caps_page_size(
        self, explorer_service, mock_transport
    ):
        first = Mock()
        first.json.return_value = {
            "data": [_row_payload("ws-1"), _row_payload("ws-2")],
            "meta": {
                "pagination": {
                    "current-page": 1,
                    "page-size": 2,
                    "next-page": 2,
                    "total-pages": 2,
                }
            },
        }
        second = Mock()
        second.json.return_value = {
            "data": [_row_payload("ws-3")],
            "meta": {
                "pagination": {
                    "current-page": 2,
                    "page-size": 2,
                    "next-page": None,
                    "total-pages": 2,
                }
            },
        }
        mock_transport.request.side_effect = [first, second]

        options = ExplorerQueryOptions(
            view_type=ExplorerViewType.WORKSPACES,
            page_size=50,
        )

        rows = list(explorer_service.query(ORG, options))
        assert [row.id for row in rows] == ["ws-1", "ws-2", "ws-3"]

        expected_calls = [
            call(
                "GET",
                EXPLORER_PATH,
                params={"type": "workspaces", "page[size]": 50, "page[number]": 1},
            ),
            call(
                "GET",
                EXPLORER_PATH,
                params={"type": "workspaces", "page[size]": 50, "page[number]": 2},
            ),
        ]
        mock_transport.request.assert_has_calls(expected_calls)
        assert mock_transport.request.call_count == 2

    def test_query_uses_current_and_total_pages_when_next_page_missing(
        self, explorer_service, mock_transport
    ):
        first = Mock()
        first.json.return_value = {
            "data": [_row_payload("ws-1")],
            "meta": {"pagination": {"current-page": 1, "total-pages": 2}},
        }
        second = Mock()
        second.json.return_value = {
            "data": [_row_payload("ws-2")],
            "meta": {"pagination": {"current-page": 2, "total-pages": 2}},
        }
        mock_transport.request.side_effect = [first, second]

        rows = list(
            explorer_service.query(
                ORG, ExplorerQueryOptions(view_type=ExplorerViewType.WORKSPACES)
            )
        )
        assert [row.id for row in rows] == ["ws-1", "ws-2"]

        expected_calls = [
            call(
                "GET",
                EXPLORER_PATH,
                params={"type": "workspaces", "page[number]": 1, "page[size]": 100},
            ),
            call(
                "GET",
                EXPLORER_PATH,
                params={"type": "workspaces", "page[number]": 2, "page[size]": 100},
            ),
        ]
        mock_transport.request.assert_has_calls(expected_calls)
        assert mock_transport.request.call_count == 2

    def test_query_stops_when_pagination_meta_does_not_advance(
        self, explorer_service, mock_transport
    ):
        first = Mock()
        first.json.return_value = {
            "data": [_row_payload("ws-1")],
            "meta": {"pagination": {"current-page": 1, "total-pages": 2}},
        }
        second = Mock()
        second.json.return_value = {
            "data": [_row_payload("ws-1")],
            "meta": {"pagination": {"current-page": 1, "total-pages": 2}},
        }
        mock_transport.request.side_effect = [first, second]

        rows = list(
            explorer_service.query(
                ORG, ExplorerQueryOptions(view_type=ExplorerViewType.WORKSPACES)
            )
        )
        assert [row.id for row in rows] == ["ws-1", "ws-1"]
        assert mock_transport.request.call_count == 2

    def test_query_stops_on_empty_page_even_if_next_page_present(
        self, explorer_service, mock_transport
    ):
        first = Mock()
        first.json.return_value = {
            "data": [],
            "meta": {
                "pagination": {"current-page": 1, "next-page": 2, "total-pages": 5}
            },
        }
        mock_transport.request.return_value = first

        rows = list(
            explorer_service.query(
                ORG, ExplorerQueryOptions(view_type=ExplorerViewType.WORKSPACES)
            )
        )
        assert rows == []
        assert mock_transport.request.call_count == 1

    def test_query_invalid_org(self, explorer_service):
        with pytest.raises(InvalidOrgError):
            list(
                explorer_service.query(
                    "",
                    ExplorerQueryOptions(view_type=ExplorerViewType.WORKSPACES),
                )
            )

    @pytest.mark.parametrize("org", ["", None])
    def test_export_csv_invalid_org(self, explorer_service, org):
        with pytest.raises(InvalidOrgError):
            explorer_service.export_csv(
                org,
                ExplorerQueryOptions(view_type=ExplorerViewType.WORKSPACES),
            )

    def test_export_csv(self, explorer_service, mock_transport):
        response = Mock()
        response.text = "workspace_name\nexample\n"
        mock_transport.request.return_value = response

        csv_text = explorer_service.export_csv(
            ORG, ExplorerQueryOptions(view_type=ExplorerViewType.WORKSPACES)
        )

        assert "workspace_name" in csv_text
        _assert_single_request_call(
            mock_transport,
            "GET",
            f"{EXPLORER_PATH}/export/csv",
            params={"type": "workspaces"},
        )


class TestExplorerSavedViews:
    def test_list_saved_views(self, explorer_service, mock_transport):
        response = Mock()
        response.json.return_value = {"data": [_saved_view_payload("sq-1")]}
        mock_transport.request.return_value = response

        views = list(explorer_service.list_saved_views(ORG))
        assert len(views) == 1
        assert views[0].id == "sq-1"
        assert views[0].query_type == ExplorerViewType.WORKSPACES
        assert views[0].query.query_type == ExplorerViewType.WORKSPACES

    def test_create_saved_view(self, explorer_service, mock_transport):
        response = Mock()
        response.json.return_value = {"data": _saved_view_payload("sq-new")}
        mock_transport.request.return_value = response

        options = ExplorerSavedViewCreateOptions(
            name="my-view",
            query_type=ExplorerViewType.WORKSPACES,
            query=ExplorerSavedQuery(
                query_type=ExplorerViewType.WORKSPACES,
                filter=[
                    ExplorerSavedQueryFilter(
                        field="workspace_name", operator="contains", value=["test"]
                    )
                ],
            ),
        )
        view = explorer_service.create_saved_view(ORG, options)

        assert view.id == "sq-new"
        call = mock_transport.request.call_args
        assert call[0][0] == "POST"
        assert call[0][1] == VIEWS_PATH
        body = call[1]["json_body"]
        assert body["data"]["type"] == "explorer-saved-queries"
        assert body["data"]["attributes"]["query-type"] == "workspaces"
        assert body["data"]["attributes"]["query"]["filter"] == [
            {"workspace_name": {"contains": ["test"]}}
        ]

    def test_create_saved_view_invalid_json_raises(
        self, explorer_service, mock_transport
    ):
        response = Mock()
        response.json.side_effect = ValueError("invalid json")
        mock_transport.request.return_value = response

        options = ExplorerSavedViewCreateOptions(
            name="my-view",
            query_type=ExplorerViewType.WORKSPACES,
            query=ExplorerSavedQuery(query_type=ExplorerViewType.WORKSPACES),
        )
        with pytest.raises(ValidationError, match="create_saved_view"):
            explorer_service.create_saved_view(ORG, options)

    def test_read_saved_view_missing_data_object_raises(
        self, explorer_service, mock_transport
    ):
        response = Mock()
        response.json.return_value = {"data": []}
        mock_transport.request.return_value = response

        with pytest.raises(ValidationError, match="read_saved_view"):
            explorer_service.read_saved_view(ORG, VIEW_ID)

    def test_read_saved_view(self, explorer_service, mock_transport):
        response = Mock()
        response.json.return_value = {"data": _saved_view_payload("sq-1")}
        mock_transport.request.return_value = response

        view = explorer_service.read_saved_view(ORG, VIEW_ID)
        assert view.id == "sq-1"

        _assert_single_request_call(mock_transport, "GET", f"{VIEWS_PATH}/{VIEW_ID}")

    def test_read_saved_view_with_live_query_shape(
        self, explorer_service, mock_transport
    ):
        response = Mock()
        response.json.return_value = {"data": _saved_view_payload_live_variant("sq-2")}
        mock_transport.request.return_value = response

        view = explorer_service.read_saved_view(ORG, "sq-2")

        assert view.id == "sq-2"
        assert view.query.query_type == ExplorerViewType.WORKSPACES
        assert view.query.filter is not None
        assert view.query.filter[0].field == "workspace_name"
        assert view.query.filter[0].operator == "contains"
        assert view.query.filter[0].value == ["r2l7cj4v"]
        assert view.query.fields == []

    def test_update_saved_view(self, explorer_service, mock_transport):
        response = Mock()
        response.json.return_value = {"data": _saved_view_payload("sq-1")}
        mock_transport.request.return_value = response

        options = ExplorerSavedViewUpdateOptions(
            name="my-view-updated",
            query=ExplorerSavedQuery(
                query_type=ExplorerViewType.WORKSPACES,
                filter=[
                    ExplorerSavedQueryFilter(
                        field="workspace_name", operator="contains", value=["prod"]
                    )
                ],
            ),
        )
        view = explorer_service.update_saved_view(ORG, VIEW_ID, options)

        assert view.id == "sq-1"
        expected_body = {
            "data": {
                "type": "explorer-saved-queries",
                "id": VIEW_ID,
                "attributes": {
                    "name": "my-view-updated",
                    "query": {
                        "type": "workspaces",
                        "filter": [{"workspace_name": {"contains": ["prod"]}}],
                    },
                },
            }
        }
        _assert_single_request_call(
            mock_transport,
            "PATCH",
            f"{VIEWS_PATH}/{VIEW_ID}",
            json_body=expected_body,
        )

    def test_update_saved_view_invalid_json_raises(
        self, explorer_service, mock_transport
    ):
        response = Mock()
        response.json.side_effect = ValueError("invalid json")
        mock_transport.request.return_value = response

        options = ExplorerSavedViewUpdateOptions(
            name="my-view-updated",
            query=ExplorerSavedQuery(query_type=ExplorerViewType.WORKSPACES),
        )
        with pytest.raises(ValidationError, match="update_saved_view"):
            explorer_service.update_saved_view(ORG, VIEW_ID, options)

    @pytest.mark.parametrize("payload", [[], "bad-payload", {"data": []}])
    def test_update_saved_view_invalid_data_shape_raises(
        self, explorer_service, mock_transport, payload
    ):
        response = Mock()
        response.json.return_value = payload
        mock_transport.request.return_value = response

        options = ExplorerSavedViewUpdateOptions(
            name="my-view-updated",
            query=ExplorerSavedQuery(query_type=ExplorerViewType.WORKSPACES),
        )
        with pytest.raises(ValidationError, match="update_saved_view"):
            explorer_service.update_saved_view(ORG, VIEW_ID, options)

    def test_delete_saved_view(self, explorer_service, mock_transport):
        result = explorer_service.delete_saved_view(ORG, VIEW_ID)
        assert result is None

        _assert_single_request_call(mock_transport, "DELETE", f"{VIEWS_PATH}/{VIEW_ID}")

    def test_delete_saved_view_ignores_response_body(
        self, explorer_service, mock_transport
    ):
        response = Mock()
        response.text = '{"data":{"id":"unexpected"}}'
        response.json.side_effect = ValueError("No JSON body")
        mock_transport.request.return_value = response

        result = explorer_service.delete_saved_view(ORG, VIEW_ID)
        assert result is None

    def test_saved_view_results(self, explorer_service, mock_transport):
        first = Mock()
        first.json.return_value = {"data": [_row_payload("ws-1")]}
        second = Mock()
        second.json.return_value = {"data": []}
        mock_transport.request.side_effect = [first, second]

        rows = list(explorer_service.saved_view_results(ORG, VIEW_ID))
        assert len(rows) == 1
        assert rows[0].id == "ws-1"

        mock_transport.request.assert_any_call(
            "GET",
            f"{VIEWS_PATH}/{VIEW_ID}/results",
            params={"page[number]": 1, "page[size]": 100},
        )

    def test_saved_view_results_csv(self, explorer_service, mock_transport):
        csv_resp = Mock()
        csv_resp.text = "workspace_name,all_checks_succeeded\ndemo,true\n"
        mock_transport.request.return_value = csv_resp

        csv_text = explorer_service.saved_view_results_csv(ORG, VIEW_ID)
        assert csv_text.splitlines()[0].startswith(
            "all_checks_succeeded,workspace_name"
        )
        _assert_single_request_call(
            mock_transport, "GET", f"{VIEWS_PATH}/{VIEW_ID}/csv"
        )

    def test_saved_view_results_csv_invalid_csv_returns_raw(
        self, explorer_service, mock_transport, monkeypatch
    ):
        csv_resp = Mock()
        csv_resp.text = "raw-csv"
        mock_transport.request.return_value = csv_resp

        def _raise_csv_error(*_args, **_kwargs):
            raise csv.Error("invalid csv")

        monkeypatch.setattr("pytfe.resources.explorer.csv.reader", _raise_csv_error)

        csv_text = explorer_service.saved_view_results_csv(ORG, VIEW_ID)
        assert csv_text == "raw-csv"

    def test_saved_view_results_csv_fallback_to_export(
        self, explorer_service, mock_transport
    ):
        first = NotFound("not found", status=404)
        read_resp = Mock()
        read_resp.json.return_value = {"data": _saved_view_payload("sq-1")}
        export_resp = Mock()
        export_resp.text = "workspace_name\nfrom-export\n"
        mock_transport.request.side_effect = [first, read_resp, export_resp]

        csv_text = explorer_service.saved_view_results_csv(ORG, VIEW_ID)
        assert "from-export" in csv_text

    def test_saved_view_results_csv_server_error_fallback_to_export(
        self, explorer_service, mock_transport
    ):
        first = ServerError("server error", status=500)
        read_resp = Mock()
        read_resp.json.return_value = {"data": _saved_view_payload("sq-1")}
        export_resp = Mock()
        export_resp.text = "workspace_name\nfrom-export\n"
        mock_transport.request.side_effect = [first, read_resp, export_resp]

        csv_text = explorer_service.saved_view_results_csv(ORG, VIEW_ID)
        assert "from-export" in csv_text

    def test_saved_view_results_csv_fallback_to_rows(
        self, explorer_service, mock_transport
    ):
        not_found = NotFound("not found", status=404)
        read_resp = Mock()
        read_resp.json.return_value = {"data": _saved_view_payload("sq-1")}
        first_results = Mock()
        first_results.json.return_value = {"data": [_row_payload("ws-1")]}
        second_results = Mock()
        second_results.json.return_value = {"data": []}
        mock_transport.request.side_effect = [
            not_found,  # /csv
            read_resp,  # read saved view
            not_found,  # export_csv fallback fails
            first_results,  # saved_view_results page 1
            second_results,  # saved_view_results page 2
        ]

        csv_text = explorer_service.saved_view_results_csv(ORG, VIEW_ID)
        header = csv_text.strip().splitlines()[0]
        assert header.startswith(
            "all_checks_succeeded,current_rum_count,checks_errored,checks_failed,"
            "checks_passed,checks_unknown,current_run_applied_at,current_run_external_id,"
            "current_run_status,drifted,external_id,module_count,modules,organization_name,"
            "project_external_id,project_name,provider_count,providers,resources_drifted,"
            "resources_undrifted,state_version_terraform_version,vcs_repo_identifier,"
            "workspace_created_at,workspace_name,workspace_terraform_version,workspace_updated_at"
        )
        assert "demo-workspace" in csv_text

    @pytest.mark.parametrize("org", ["", None])
    def test_saved_view_methods_invalid_org(self, explorer_service, org):
        with pytest.raises(InvalidOrgError):
            list(explorer_service.list_saved_views(org))

        with pytest.raises(InvalidOrgError):
            explorer_service.read_saved_view(org, VIEW_ID)

    @pytest.mark.parametrize("view_id", ["", None])
    def test_saved_view_methods_invalid_id(self, explorer_service, view_id):
        with pytest.raises(InvalidExplorerSavedViewIDError):
            explorer_service.read_saved_view(ORG, view_id)

        with pytest.raises(InvalidExplorerSavedViewIDError):
            explorer_service.update_saved_view(
                ORG,
                view_id,
                ExplorerSavedViewUpdateOptions(
                    name="updated",
                    query=ExplorerSavedQuery(query_type=ExplorerViewType.WORKSPACES),
                ),
            )

        with pytest.raises(InvalidExplorerSavedViewIDError):
            explorer_service.delete_saved_view(ORG, view_id)

        with pytest.raises(InvalidExplorerSavedViewIDError):
            list(explorer_service.saved_view_results(ORG, view_id))

        with pytest.raises(InvalidExplorerSavedViewIDError):
            explorer_service.saved_view_results_csv(ORG, view_id)
