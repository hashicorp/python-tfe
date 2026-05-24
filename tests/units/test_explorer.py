# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""Unit tests for the Explorer API resource."""

from unittest.mock import Mock

import pytest

from pytfe.errors import (
    InvalidExplorerSavedViewIDError,
    InvalidOrgError,
)
from pytfe.models import (
    ExplorerQueryOptions,
    ExplorerSavedQuery,
    ExplorerSavedQueryFilter,
    ExplorerSavedViewCreateOptions,
    ExplorerSavedViewUpdateOptions,
    ExplorerUrlFilter,
    ExplorerViewType,
)
from pytfe.resources.explorer import Explorer

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


def _row_payload(row_id: str) -> dict:
    """Server-shaped row: id + type + hyphen-keyed attributes."""
    return {
        "id": row_id,
        "type": "visibility-workspace",
        "attributes": {"workspace-name": "demo-workspace"},
    }


def _saved_view_payload(view_id: str) -> dict:
    """Server-shaped saved view (matches live API: nested filter map shape)."""
    return {
        "id": view_id,
        "type": "explorer-saved-queries",
        "attributes": {
            "name": "my-view",
            "created-at": "2024-10-11T16:18:51.442Z",
            "query-type": "workspaces",
            "query": {
                "type": "workspaces",
                "filter": [{"workspace_name": {"contains": ["child"]}}],
                "fields": {"workspaces": []},
                "sort": [],
            },
        },
    }


def _single_page_response(items):
    """Mimic the transport response for a one-page _list iteration."""
    resp = Mock()
    resp.json.return_value = {
        "data": items,
        "meta": {
            "pagination": {
                "current-page": 1,
                "total-pages": 1,
                "next-page": None,
            }
        },
    }
    return resp


class TestExplorerQuery:
    def test_query_emits_expanded_filter_params(
        self, explorer_service, mock_transport
    ):
        mock_transport.request.return_value = _single_page_response(
            [_row_payload("ws-1"), _row_payload("ws-2")]
        )

        opts = ExplorerQueryOptions(
            view_type=ExplorerViewType.WORKSPACES,
            page_size=50,
            filters=[
                ExplorerUrlFilter(
                    index=0, field="workspace_name", operator="contains", value="demo"
                ),
            ],
        )
        rows = list(explorer_service.query(ORG, opts))

        assert [r.id for r in rows] == ["ws-1", "ws-2"]
        assert rows[0].type == "visibility-workspace"
        # Hyphen attribute keys must be normalised to snake_case at parse time.
        assert rows[0].attributes == {"workspace_name": "demo-workspace"}

        # The transport was called against the right path with the expanded
        # filter key in the params.
        call = mock_transport.request.call_args
        assert call.args == ("GET", EXPLORER_PATH)
        params = call.kwargs["params"]
        assert params["type"] == "workspaces"
        assert params["page[size]"] == 50
        assert (
            params["filter[0][workspace_name][contains][0]"] == "demo"
        )

    def test_query_invalid_org(self, explorer_service):
        with pytest.raises(InvalidOrgError):
            list(
                explorer_service.query(
                    "", ExplorerQueryOptions(view_type=ExplorerViewType.WORKSPACES)
                )
            )

    def test_export_csv_returns_text(self, explorer_service, mock_transport):
        resp = Mock()
        resp.text = "workspace_name\ndemo\n"
        mock_transport.request.return_value = resp

        opts = ExplorerQueryOptions(view_type=ExplorerViewType.WORKSPACES)
        out = explorer_service.export_csv(ORG, opts)
        assert out == "workspace_name\ndemo\n"

        call = mock_transport.request.call_args
        assert call.args == ("GET", f"{EXPLORER_PATH}/export/csv")
        assert call.kwargs["params"]["type"] == "workspaces"

    @pytest.mark.parametrize("org", ["", "bad/org"])
    def test_export_csv_invalid_org(self, explorer_service, org):
        with pytest.raises(InvalidOrgError):
            explorer_service.export_csv(
                org, ExplorerQueryOptions(view_type=ExplorerViewType.WORKSPACES)
            )


class TestExplorerSavedViews:
    def test_list_saved_views(self, explorer_service, mock_transport):
        mock_transport.request.return_value = _single_page_response(
            [_saved_view_payload(VIEW_ID), _saved_view_payload("sq-2")]
        )

        views = list(explorer_service.list_saved_views(ORG))
        assert [v.id for v in views] == [VIEW_ID, "sq-2"]
        assert views[0].name == "my-view"
        assert views[0].query_type == ExplorerViewType.WORKSPACES
        assert views[0].query.query_type == ExplorerViewType.WORKSPACES
        # Filter must be flattened from server's map shape to the flat model.
        assert len(views[0].query.filter) == 1
        flt = views[0].query.filter[0]
        assert flt.field == "workspace_name"
        assert flt.operator == "contains"
        assert flt.value == ["child"]

    def test_create_saved_view_reshapes_filter_for_api(
        self, explorer_service, mock_transport
    ):
        resp = Mock()
        resp.json.return_value = {"data": _saved_view_payload(VIEW_ID)}
        mock_transport.request.return_value = resp

        opts = ExplorerSavedViewCreateOptions(
            name="my-view",
            query_type=ExplorerViewType.WORKSPACES,
            query=ExplorerSavedQuery(
                query_type=ExplorerViewType.WORKSPACES,
                filter=[
                    ExplorerSavedQueryFilter(
                        field="workspace_name",
                        operator="contains",
                        value=["child"],
                    )
                ],
            ),
        )
        view = explorer_service.create_saved_view(ORG, opts)
        assert view.id == VIEW_ID

        call = mock_transport.request.call_args
        assert call.args == ("POST", VIEWS_PATH)
        body = call.kwargs["json_body"]
        assert body["data"]["type"] == "explorer-saved-queries"
        attrs = body["data"]["attributes"]
        assert attrs["name"] == "my-view"
        assert attrs["query-type"] == "workspaces"
        # Filter rows in the request body must be in the nested map shape.
        assert attrs["query"]["filter"] == [
            {"workspace_name": {"contains": ["child"]}}
        ]

    def test_read_saved_view(self, explorer_service, mock_transport):
        resp = Mock()
        resp.json.return_value = {"data": _saved_view_payload(VIEW_ID)}
        mock_transport.request.return_value = resp

        view = explorer_service.read_saved_view(ORG, VIEW_ID)
        assert view.id == VIEW_ID
        assert view.query.query_type == ExplorerViewType.WORKSPACES

        call = mock_transport.request.call_args
        assert call.args == ("GET", f"{VIEWS_PATH}/{VIEW_ID}")

    def test_update_saved_view(self, explorer_service, mock_transport):
        resp = Mock()
        resp.json.return_value = {"data": _saved_view_payload(VIEW_ID)}
        mock_transport.request.return_value = resp

        opts = ExplorerSavedViewUpdateOptions(
            name="renamed",
            query=ExplorerSavedQuery(
                query_type=ExplorerViewType.WORKSPACES,
                filter=[
                    ExplorerSavedQueryFilter(
                        field="workspace_name",
                        operator="contains",
                        value=["abc"],
                    )
                ],
            ),
        )
        view = explorer_service.update_saved_view(ORG, VIEW_ID, opts)
        assert view.id == VIEW_ID

        call = mock_transport.request.call_args
        assert call.args == ("PATCH", f"{VIEWS_PATH}/{VIEW_ID}")
        body = call.kwargs["json_body"]
        assert body["data"]["id"] == VIEW_ID
        assert body["data"]["attributes"]["name"] == "renamed"
        # Same nested-map reshape on update.
        assert body["data"]["attributes"]["query"]["filter"] == [
            {"workspace_name": {"contains": ["abc"]}}
        ]

    def test_delete_saved_view(self, explorer_service, mock_transport):
        mock_transport.request.return_value = Mock()
        explorer_service.delete_saved_view(ORG, VIEW_ID)
        call = mock_transport.request.call_args
        assert call.args == ("DELETE", f"{VIEWS_PATH}/{VIEW_ID}")

    def test_saved_view_results(self, explorer_service, mock_transport):
        mock_transport.request.return_value = _single_page_response(
            [_row_payload("ws-1")]
        )

        rows = list(explorer_service.saved_view_results(ORG, VIEW_ID))
        assert [r.id for r in rows] == ["ws-1"]

        call = mock_transport.request.call_args
        assert call.args == ("GET", f"{VIEWS_PATH}/{VIEW_ID}/results")

    def test_saved_view_results_csv(self, explorer_service, mock_transport):
        resp = Mock()
        resp.text = "id,name\nws-1,demo\n"
        mock_transport.request.return_value = resp

        out = explorer_service.saved_view_results_csv(ORG, VIEW_ID)
        assert out == "id,name\nws-1,demo\n"

        call = mock_transport.request.call_args
        assert call.args == ("GET", f"{VIEWS_PATH}/{VIEW_ID}/export/csv")

    @pytest.mark.parametrize("org", ["", "bad/org"])
    def test_saved_view_methods_invalid_org(self, explorer_service, org):
        with pytest.raises(InvalidOrgError):
            list(explorer_service.list_saved_views(org))
        with pytest.raises(InvalidOrgError):
            explorer_service.read_saved_view(org, VIEW_ID)
        with pytest.raises(InvalidOrgError):
            explorer_service.delete_saved_view(org, VIEW_ID)

    @pytest.mark.parametrize("view_id", ["", "bad/view"])
    def test_saved_view_methods_invalid_id(self, explorer_service, view_id):
        with pytest.raises(InvalidExplorerSavedViewIDError):
            explorer_service.read_saved_view(ORG, view_id)
        with pytest.raises(InvalidExplorerSavedViewIDError):
            explorer_service.delete_saved_view(ORG, view_id)
        with pytest.raises(InvalidExplorerSavedViewIDError):
            list(explorer_service.saved_view_results(ORG, view_id))
        with pytest.raises(InvalidExplorerSavedViewIDError):
            explorer_service.saved_view_results_csv(ORG, view_id)
